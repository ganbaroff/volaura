"""
ResearchLoop — Autonomous web research for the swarm.

v7 "Research Autonomy" architecture:
  1. Agents propose ResearchRequest in every response
  2. PM collects + deduplicates by topic similarity (word overlap, like PathProposal)
  3. Team lead (highest-accuracy agent in hive) is elected as research coordinator
  4. WebResearcher (Gemini Pro + google_search) executes the top-voted topic
  5. Findings injected into StructuredMemory World Network
  6. All future agents have access to these grounded facts

Why Gemini Pro as researcher:
  - Only model in our stack with native google_search tool integration
  - No extra API — same key, same SDK
  - Grounding sources are returned alongside findings (verifiable)
  - Can be parallelized: one topic per concurrent research task

Why World Network:
  - World facts are the first thing injected into every agent prompt
  - Research findings reach ALL future agents automatically
  - No manual "tell agents about X" needed

Autonomy contract:
  - Agents decide WHAT to research (through research_request proposals)
  - PM decides WHICH is top priority (dedup + vote count)
  - Gemini Pro decides HOW to research (google_search queries)
  - World Network decides WHERE findings live (permanent swarm memory)
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from .types import ResearchRequest

if TYPE_CHECKING:
    from .structured_memory import StructuredMemory

# Minimum votes required to trigger research (avoid researching fringe requests)
MIN_VOTES_FOR_RESEARCH = 1  # even 1 unique request is worth researching
MAX_TOPICS_PER_DECISION = 3  # max parallel research tasks per decision cycle
RESEARCH_TIMEOUT_SECONDS = 60.0


class ResearchFindings:
    """Structured output from a web research run."""

    def __init__(
        self,
        topic: str,
        query_used: str,
        summary: str,
        key_facts: list[str],
        sources: list[str],
        model_used: str,
        latency_ms: int,
        error: str | None = None,
    ):
        self.topic = topic
        self.query_used = query_used
        self.summary = summary
        self.key_facts = key_facts
        self.sources = sources
        self.model_used = model_used
        self.latency_ms = latency_ms
        self.error = error
        self.ok = error is None and bool(summary)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "query_used": self.query_used,
            "summary": self.summary,
            "key_facts": self.key_facts,
            "sources": self.sources,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }

    def to_world_fact(self) -> str:
        """Format findings as a World Network fact entry."""
        lines = [
            f"[RESEARCH: {self.topic}]",
            self.summary,
        ]
        if self.key_facts:
            lines.append("Key facts:")
            for fact in self.key_facts[:5]:
                lines.append(f"  - {fact}")
        if self.sources:
            lines.append(f"Sources: {', '.join(self.sources[:3])}")
        return "\n".join(lines)


class WebResearcher:
    """Executes web research using Gemini Pro with google_search grounding.

    Primary: Gemini Pro + google_search (real-time internet access)
    Fallback: DeepSeek Chat (uses its training knowledge, no live web, but
              much better than nothing when Gemini is down)

    This was flagged by kimi-k2 in v7 feedback: "ResearchLoop is a single-point
    Gemini failure away from uselessness." DeepSeek fallback fixes this.
    """

    RESEARCH_MODEL = "gemini-2.5-pro"
    FALLBACK_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: str | None = None,
        deepseek_key: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.deepseek_key = deepseek_key or os.environ.get("DEEPSEEK_API_KEY", "")

    async def conduct(self, request: ResearchRequest) -> ResearchFindings:
        """Execute one research request. Returns structured findings."""
        start = time.monotonic()
        topic = request.topic
        domain = request.domain

        try:
            from google import genai
            from google.genai import types as genai_types

            client = genai.Client(api_key=self.api_key)

            # Build research prompt — ask for structured output
            prompt = f"""You are a research analyst. Investigate this topic thoroughly using web search.

RESEARCH TOPIC: {topic}

DOMAIN: {domain}
RATIONALE (why this was requested): {request.rationale or "To improve AI decision-making quality"}

Instructions:
1. Search for the most current, authoritative information on this topic
2. Focus on: recent developments, best practices, concrete data, and expert consensus
3. Return your findings in this EXACT JSON format:

{{
  "summary": "2-3 sentence executive summary of what you found",
  "key_facts": [
    "specific fact 1 with source or date if known",
    "specific fact 2",
    "specific fact 3",
    "specific fact 4",
    "specific fact 5"
  ],
  "sources": ["source title or URL 1", "source title or URL 2", "source title or URL 3"],
  "confidence": "high|medium|low",
  "query_used": "the search query you actually used"
}}

Be specific. No vague summaries. Real facts, real numbers, real citations."""

            # Gemini Pro with google_search grounding
            # NOTE: response_mime_type="application/json" is INCOMPATIBLE with tool use.
            # We use plain text response and extract JSON from the output manually.
            response = await client.aio.models.generate_content(
                model=self.RESEARCH_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                    temperature=0.1,
                    max_output_tokens=1500,
                ),
            )

            ms = int((time.monotonic() - start) * 1000)
            raw = response.text.strip() if response.text else ""

            import json
            import re

            # Extract JSON block from text response (model may wrap in markdown)
            json_match = re.search(r"\{[\s\S]*\}", raw)
            if not json_match:
                raise ValueError(f"No JSON in response: {raw[:200]}")
            data = json.loads(json_match.group(0))

            # Extract grounding sources if available
            grounding_sources = []
            try:
                if hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                        meta = candidate.grounding_metadata
                        if hasattr(meta, "search_entry_point"):
                            pass  # rendered search results
                        if hasattr(meta, "grounding_chunks"):
                            for chunk in meta.grounding_chunks or []:
                                if hasattr(chunk, "web") and chunk.web:
                                    grounding_sources.append(
                                        chunk.web.title or chunk.web.uri or ""
                                    )
            except Exception:
                pass

            sources = grounding_sources or data.get("sources", [])

            return ResearchFindings(
                topic=topic,
                query_used=data.get("query_used", topic),
                summary=data.get("summary", ""),
                key_facts=data.get("key_facts", []),
                sources=sources[:5],
                model_used=self.RESEARCH_MODEL,
                latency_ms=ms,
            )

        except Exception as e:
            ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "WebResearcher (Gemini) failed for '{topic}': {err}. Trying DeepSeek fallback.",
                topic=topic[:60],
                err=str(e)[:100],
            )
            # v7 fallback: DeepSeek as backup researcher (no live web, but training knowledge)
            if self.deepseek_key:
                return await self._conduct_deepseek(request)
            return ResearchFindings(
                topic=topic,
                query_used=topic,
                summary="",
                key_facts=[],
                sources=[],
                model_used=self.RESEARCH_MODEL,
                latency_ms=ms,
                error=str(e)[:300],
            )

    async def _conduct_deepseek(self, request: ResearchRequest) -> ResearchFindings:
        """Fallback researcher: DeepSeek Chat (no live web, but strong reasoning)."""
        start = time.monotonic()
        topic = request.topic
        try:
            from openai import AsyncOpenAI
            import json
            import re

            client = AsyncOpenAI(
                api_key=self.deepseek_key,
                base_url="https://api.deepseek.com",
            )

            prompt = f"""You are a research analyst. Provide your best knowledge on this topic.
Note: You do NOT have internet access. Use your training knowledge only.
Be honest if your information might be outdated.

TOPIC: {topic}
RATIONALE: {request.rationale or "To improve AI decision-making quality"}

Return JSON:
{{
  "summary": "2-3 sentence summary of what you know",
  "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
  "sources": ["known paper/resource 1", "known paper/resource 2"],
  "confidence": "high|medium|low",
  "query_used": "deepseek-training-knowledge"
}}"""

            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            ms = int((time.monotonic() - start) * 1000)
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)

            logger.info(
                "DeepSeek fallback research complete: '{topic}' ({ms}ms)",
                topic=topic[:60], ms=ms,
            )

            return ResearchFindings(
                topic=topic,
                query_used="deepseek-training-knowledge",
                summary=data.get("summary", ""),
                key_facts=data.get("key_facts", []),
                sources=data.get("sources", []) + ["[DeepSeek fallback — no live web]"],
                model_used="deepseek-chat",
                latency_ms=ms,
            )

        except Exception as e:
            ms = int((time.monotonic() - start) * 1000)
            logger.warning("DeepSeek fallback also failed: {err}", err=str(e)[:200])
            return ResearchFindings(
                topic=topic,
                query_used=topic,
                summary="",
                key_facts=[],
                sources=[],
                model_used="deepseek-chat",
                latency_ms=ms,
                error=f"Both Gemini and DeepSeek failed: {str(e)[:200]}",
            )

    async def conduct_parallel(
        self, requests: list[ResearchRequest], max_concurrent: int = 3
    ) -> list[ResearchFindings]:
        """Research multiple topics in parallel, up to max_concurrent."""
        limited = requests[:max_concurrent]
        logger.info(
            "WebResearcher: conducting {n} research tasks in parallel",
            n=len(limited),
        )
        results = await asyncio.gather(
            *[self.conduct(req) for req in limited],
            return_exceptions=True,
        )
        findings = []
        for req, result in zip(limited, results):
            if isinstance(result, ResearchFindings):
                if result.ok:
                    logger.info(
                        "Research complete: '{topic}' → {n} facts ({ms}ms)",
                        topic=req.topic[:60],
                        n=len(result.key_facts),
                        ms=result.latency_ms,
                    )
                    findings.append(result)
                else:
                    logger.warning(
                        "Research failed: '{topic}' — {err}",
                        topic=req.topic[:60],
                        err=result.error,
                    )
            else:
                logger.warning("Research exception: {err}", err=str(result)[:200])
        return findings


def collect_and_prioritize_research(
    results: list,  # list[AgentResult]
    existing_topics: set[str] | None = None,
) -> list[ResearchRequest]:
    """Collect research requests from agent results, deduplicate, sort by votes.

    Deduplication: same logic as PathProposal (word overlap 40% = same topic).
    Returns sorted list, most-voted first.
    """
    from .pm import _word_overlap  # reuse existing similarity function

    raw: list[ResearchRequest] = []
    for r in results:
        if hasattr(r, "research_request") and r.research_request:
            req = r.research_request
            req.proposed_by = r.agent_id
            raw.append(req)

    if not raw:
        return []

    # Deduplicate by topic word overlap
    merged: list[ResearchRequest] = []
    for req in raw:
        matched = False
        for existing in merged:
            overlap = _word_overlap(
                req.topic + " " + req.rationale,
                existing.topic + " " + existing.rationale,
            )
            if overlap >= 0.40:
                existing.votes += 1
                matched = True
                break
        if not matched:
            merged.append(req)

    # Filter out topics already in existing_topics
    if existing_topics:
        merged = [
            r for r in merged
            if not any(
                _word_overlap(r.topic, t) >= 0.50 for t in existing_topics
            )
        ]

    # Sort by votes DESC, then by priority weight
    priority_weight = {"high": 3, "medium": 2, "low": 1}
    merged.sort(
        key=lambda r: (r.votes, priority_weight.get(r.priority, 2)),
        reverse=True,
    )

    return merged


async def inject_findings_into_memory(
    findings: list[ResearchFindings],
    structured_memory: "StructuredMemory",
    decision_id: str = "",
) -> int:
    """Inject research findings into StructuredMemory World Network.

    Returns number of facts successfully stored.
    """
    stored = 0
    for finding in findings:
        if not finding.ok:
            continue
        try:
            # Store main summary as world fact
            structured_memory.store_world_fact(
                content=finding.to_world_fact(),
                source=f"WebResearcher:{finding.model_used}",
                tags=[finding.topic.split()[0].lower(), "research"],
            )
            stored += 1

            # Store each key fact individually for granular retrieval
            for fact in finding.key_facts[:3]:
                structured_memory.store_world_fact(
                    content=f"[Re: {finding.topic}] {fact}",
                    source=f"WebResearch:{','.join(finding.sources[:1])}",
                    tags=[finding.topic.split()[0].lower(), "research_detail"],
                )
                stored += 1

        except Exception as e:
            logger.warning(
                "Failed to inject research finding: {err}",
                err=str(e)[:200],
            )

    if stored:
        logger.info(
            "Injected {n} research facts into World Network (decision: {id})",
            n=stored,
            id=decision_id or "unknown",
        )
    return stored

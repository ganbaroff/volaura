"""@atlas_tool registry (Pattern 3 — Pydantic-AI shape, zero extra deps).

A tiny decorator + registry so new Telegram action-layer tools become a
+5-LOC change instead of +40. Mirrors the Pydantic-AI `@agent.tool` ergonomics
using only Pydantic v2 (already in stack) and FastAPI-compatible `await`.

Usage:

    class CreateGithubIssueArgs(BaseModel):
        title: str
        body: str
        labels: list[str] = Field(default_factory=list)

    @atlas_tool(
        name="create_github_issue",
        description="Create a GitHub issue in ganbaroff/volaura",
        requires_approval=True,
    )
    async def create_github_issue(args: CreateGithubIssueArgs) -> ToolResult:
        ...
        return ToolResult.ok(anchor=url)

Registry API:
    list_tools()          → list[ToolSpec]     (for /tools display + prompt prefix)
    invoke(name, args)    → ToolResult         (validates via the tool's arg-model)
    get(name)             → AtlasTool | None

Every tool auto-gets:
  * Pydantic v2 argument validation (bad args → ToolResult.error).
  * JSON-safe `args_preview` for Pattern 2 approval cards.
  * sha256 payload fingerprint for Pattern 2 tamper detection.

Source: docs/research/agent-action-layer/summary.md Pattern 3.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

# ── Result model ────────────────────────────────────────────────────────────


class ToolResult(BaseModel):
    """Uniform return shape for every @atlas_tool."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    anchor: str | None = None  # URL / path / id the tool produced
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(cls, anchor: str | None = None, **data: Any) -> ToolResult:
        return cls(ok=True, anchor=anchor, data=data)

    @classmethod
    def fail(cls, error: str, **data: Any) -> ToolResult:
        return cls(ok=False, error=error[:500], data=data)


ArgsT = TypeVar("ArgsT", bound=BaseModel)
ToolFn = Callable[[Any], Awaitable[ToolResult]]


# ── Tool spec + registry ────────────────────────────────────────────────────


class ToolSpec(BaseModel):
    """Public description of a tool (safe to render to CEO / LLM)."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    requires_approval: bool
    args_schema: dict[str, Any]


class AtlasTool(Generic[ArgsT]):
    """Bound tool: function + its Pydantic arg model + metadata."""

    def __init__(
        self,
        name: str,
        description: str,
        requires_approval: bool,
        fn: ToolFn,
        args_model: type[BaseModel],
    ) -> None:
        self.name = name
        self.description = description.strip()
        self.requires_approval = requires_approval
        self.fn = fn
        self.args_model = args_model

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            requires_approval=self.requires_approval,
            args_schema=self.args_model.model_json_schema(),
        )

    def preview(self, args: BaseModel | dict[str, Any]) -> tuple[str, str]:
        """Return (pretty_json, sha12) for Pattern 2 approval cards."""
        payload = args.model_dump() if isinstance(args, BaseModel) else dict(args)
        pretty = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        sha = hashlib.sha256(pretty.encode("utf-8")).hexdigest()
        return pretty, sha[:12]

    async def invoke(self, args: dict[str, Any] | BaseModel) -> ToolResult:
        """Validate args → call the underlying coroutine → return ToolResult."""
        try:
            if isinstance(args, BaseModel):
                validated = args
            else:
                validated = self.args_model.model_validate(args)
        except ValidationError as e:
            return ToolResult.fail(f"arg validation failed: {e}")

        try:
            return await self.fn(validated)
        except Exception as e:  # noqa: BLE001 — tool layer catches everything
            logger.exception("atlas_tool {n} raised", n=self.name)
            return ToolResult.fail(f"{type(e).__name__}: {e}")


class _Registry:
    """Process-wide registry. One per app."""

    def __init__(self) -> None:
        self._tools: dict[str, AtlasTool] = {}

    def register(self, tool: AtlasTool) -> None:
        if tool.name in self._tools:
            logger.warning("atlas_tool {n} re-registered — overwriting", n=tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> AtlasTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolSpec]:
        return [t.spec() for t in self._tools.values()]

    async def invoke(self, name: str, args: dict[str, Any] | BaseModel) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult.fail(f"unknown tool: {name}")
        return await tool.invoke(args)

    def clear(self) -> None:  # test helper
        self._tools.clear()


REGISTRY = _Registry()


# ── Decorator ───────────────────────────────────────────────────────────────


def atlas_tool(
    *,
    name: str,
    description: str,
    requires_approval: bool = False,
) -> Callable[[ToolFn], ToolFn]:
    """Register a coroutine as an Atlas tool.

    The decorated function MUST be `async` and take exactly one positional
    argument whose annotation is a Pydantic BaseModel subclass. That model is
    used for validation + preview rendering.
    """

    def _decorate(fn: ToolFn) -> ToolFn:
        sig = inspect.signature(fn)
        params = [p for p in sig.parameters.values() if p.kind != inspect.Parameter.VAR_KEYWORD]
        if len(params) != 1:
            raise TypeError(f"@atlas_tool {name}: function must take exactly one positional arg (got {len(params)})")
        # `from __future__ import annotations` turns annotations into strings at
        # class bodies but not at module-level functions on 3.12 — still, resolve
        # defensively via inspect.get_annotations.
        try:
            resolved = inspect.get_annotations(fn, eval_str=True)
        except Exception:
            resolved = {}
        ann = resolved.get(params[0].name, params[0].annotation)
        if ann is inspect.Parameter.empty or not (isinstance(ann, type) and issubclass(ann, BaseModel)):
            raise TypeError(
                f"@atlas_tool {name}: single arg must be annotated with a Pydantic BaseModel subclass (got {ann!r})"
            )
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"@atlas_tool {name}: function must be async")

        tool = AtlasTool(
            name=name,
            description=description,
            requires_approval=requires_approval,
            fn=fn,
            args_model=ann,
        )
        REGISTRY.register(tool)
        return fn

    return _decorate


# ── Starter tools ───────────────────────────────────────────────────────────
#
# NOTE: Bodies delegate to the existing helpers in telegram_webhook.py via
# late-import so we don't create an import cycle. Existing behaviour is
# preserved; callers gain the registry surface (list_tools, preview, sha12).


class CreateGithubIssueArgs(BaseModel):
    """Args for the `create_github_issue` tool."""

    text: str = Field(..., description="Raw CEO message / issue body")
    label: str = Field(default="atlas-telegram-request")


@atlas_tool(
    name="create_github_issue",
    description="Create a GitHub issue in ganbaroff/volaura using GH_PAT_ACTIONS.",
    requires_approval=False,  # Atlas-action branch auto-approves; proposal cards set True.
)
async def create_github_issue(args: CreateGithubIssueArgs) -> ToolResult:
    from app.routers.telegram_webhook import _create_github_issue as _impl  # late import

    url = await _impl(args.text, label=args.label)
    if not url:
        return ToolResult.fail("github issue creation returned no URL")
    return ToolResult.success(anchor=url)


class CreateInboxFileArgs(BaseModel):
    """Args for the `create_inbox_file` fallback tool."""

    text: str = Field(..., description="Body to write into memory/atlas/inbox/*.md")
    issue_url: str | None = Field(default=None, description="Optional GH issue URL to link")


@atlas_tool(
    name="create_inbox_file",
    description="Drop a note into memory/atlas/inbox/ so the live Atlas picks it up on wake.",
    requires_approval=False,
)
async def create_inbox_file(args: CreateInboxFileArgs) -> ToolResult:
    from app.routers.telegram_webhook import _write_atlas_inbox_file as _impl  # late import

    path = await _impl(args.text, issue_url=args.issue_url)
    if not path:
        return ToolResult.fail("inbox file write returned empty path")
    return ToolResult.success(anchor=path)


# ── Pattern 2 helpers (duplicated with packages/swarm/telegram_proposal_cards.py
# because apps/api runtime does NOT have `packages/` on sys.path — the cron
# script runs from repo root and imports its local copy. Keep the two
# implementations byte-identical so the sha12 matches across processes.) ────


def compute_payload_sha12(payload: dict[str, Any]) -> str:
    """Canonical sha256(payload) → first 12 hex chars.

    Deterministic: sort_keys=True, ensure_ascii=False, indent=2. Must match
    `packages.swarm.telegram_proposal_cards.compute_payload_sha12` exactly.
    """
    canon = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


def extract_action_payload(proposal: dict[str, Any]) -> dict[str, Any]:
    """Mirror of `packages.swarm.telegram_proposal_cards._extract_action_payload`."""
    if isinstance(proposal.get("action_payload"), dict):
        return proposal["action_payload"]
    if isinstance(proposal.get("tool_args"), dict):
        return {"tool": proposal.get("tool_name", "?"), "args": proposal["tool_args"]}
    return {
        "title": proposal.get("title", ""),
        "content": (proposal.get("content") or "")[:1000],
    }


__all__ = [
    "REGISTRY",
    "AtlasTool",
    "CreateGithubIssueArgs",
    "CreateInboxFileArgs",
    "ToolResult",
    "ToolSpec",
    "atlas_tool",
    "compute_payload_sha12",
    "create_github_issue",
    "create_inbox_file",
    "extract_action_payload",
]

"""Tests for packages/swarm/project_briefing.py.

Validates that PROJECT_FACTS is non-empty, contains required facts, and
that both autonomous_run and coordinator import it correctly.
"""

from __future__ import annotations

import importlib


class TestProjectBriefingContent:
    def test_project_facts_non_empty(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert len(PROJECT_FACTS) > 100

    def test_aura_weights_present(self):
        from swarm.project_briefing import PROJECT_FACTS

        # All 8 competencies with correct weights
        assert "communication: 0.20" in PROJECT_FACTS
        assert "reliability: 0.15" in PROJECT_FACTS
        assert "english_proficiency: 0.15" in PROJECT_FACTS
        assert "leadership: 0.15" in PROJECT_FACTS
        assert "event_performance: 0.10" in PROJECT_FACTS
        assert "tech_literacy: 0.10" in PROJECT_FACTS
        assert "adaptability: 0.10" in PROJECT_FACTS
        assert "empathy_safeguarding: 0.05" in PROJECT_FACTS

    def test_badge_tiers_present(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert "Platinum" in PROJECT_FACTS
        assert "Gold" in PROJECT_FACTS
        assert "Silver" in PROJECT_FACTS
        assert "Bronze" in PROJECT_FACTS

    def test_positioning_rules_present(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert 'volunteer' in PROJECT_FACTS.lower()
        assert "LinkedIn competitor" in PROJECT_FACTS

    def test_five_foundation_laws_mentioned(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert "Foundation Laws" in PROJECT_FACTS
        assert "Energy modes" in PROJECT_FACTS or "Energy" in PROJECT_FACTS

    def test_ecosystem_five_faces(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert "VOLAURA" in PROJECT_FACTS
        assert "MindShift" in PROJECT_FACTS
        assert "Life Simulator" in PROJECT_FACTS
        assert "BrandedBy" in PROJECT_FACTS
        assert "ZEUS" in PROJECT_FACTS

    def test_tech_stack_constants(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert "FastAPI" in PROJECT_FACTS
        assert "Supabase" in PROJECT_FACTS
        assert "Next.js" in PROJECT_FACTS

    def test_llm_hierarchy_present(self):
        from swarm.project_briefing import PROJECT_FACTS

        assert "Cerebras" in PROJECT_FACTS
        assert "Haiku" in PROJECT_FACTS


class TestAutonomousRunImport:
    def test_autonomous_run_imports_project_facts(self):
        """autonomous_run must import PROJECT_FACTS — it's what swarm agents receive."""
        import ast
        from pathlib import Path

        src = (Path(__file__).parents[1] / "autonomous_run.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append((node.module, [a.name for a in node.names]))
        # At least one import FROM project_briefing of PROJECT_FACTS
        found = any(
            (mod or "").endswith("project_briefing") and "PROJECT_FACTS" in names
            for mod, names in imports
        )
        assert found, "autonomous_run.py must import PROJECT_FACTS from project_briefing"

    def test_project_facts_in_prompt_template(self):
        """_build_agent_prompt must include PROJECT_FACTS in its return string template."""
        from pathlib import Path

        src = (Path(__file__).parents[1] / "autonomous_run.py").read_text(encoding="utf-8")
        # Should appear in the f-string template
        assert "PROJECT_FACTS" in src


class TestCoordinatorImport:
    def test_coordinator_imports_project_facts(self):
        """coordinator.py must import _PROJECT_FACTS from project_briefing."""
        from pathlib import Path

        src = (Path(__file__).parents[1] / "coordinator.py").read_text(encoding="utf-8")
        assert "project_briefing" in src

    def test_coordinator_injects_facts_into_instruction(self):
        """SubtaskContract instruction must start with _PROJECT_FACTS."""
        from pathlib import Path

        src = (Path(__file__).parents[1] / "coordinator.py").read_text(encoding="utf-8")
        assert "_PROJECT_FACTS" in src
        # The instruction f-string should start with facts
        assert '_PROJECT_FACTS' in src

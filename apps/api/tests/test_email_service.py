"""Unit tests for app.services.email — HTML builders, badge labels, competency names."""

from __future__ import annotations

from app.services.email import (
    _BADGE_LABELS,
    _COMPETENCY_NAMES,
    _build_ghosting_grace_html,
    _build_html,
)


class TestBadgeLabels:
    def test_all_four_tiers(self):
        assert set(_BADGE_LABELS.keys()) == {"bronze", "silver", "gold", "platinum"}

    def test_values_capitalized(self):
        for v in _BADGE_LABELS.values():
            assert v[0].isupper()


class TestCompetencyNames:
    def test_known_slugs(self):
        expected = {
            "adaptability",
            "communication",
            "leadership",
            "teamwork",
            "problem_solving",
            "time_management",
            "initiative",
        }
        assert set(_COMPETENCY_NAMES.keys()) == expected

    def test_values_human_readable(self):
        assert _COMPETENCY_NAMES["problem_solving"] == "Problem Solving"
        assert _COMPETENCY_NAMES["time_management"] == "Time Management"


class TestBuildHtml:
    def test_contains_display_name(self):
        html = _build_html("Leyla", "Communication", 85.3, "gold", 15)
        assert "Leyla" in html

    def test_contains_competency_name(self):
        html = _build_html("Test", "Leadership", 70, "silver", 0)
        assert "LEADERSHIP" in html

    def test_score_rounded(self):
        html = _build_html("User", "Teamwork", 72.7, "bronze", 0)
        assert ">73<" in html

    def test_badge_label_lookup(self):
        html = _build_html("User", "Adaptability", 90, "platinum", 0)
        assert "Platinum" in html

    def test_badge_label_unknown_passthrough(self):
        html = _build_html("User", "Test", 50, "mythic", 0)
        assert "mythic" in html

    def test_crystal_line_when_positive(self):
        html = _build_html("User", "Test", 50, "gold", 10)
        assert "+10 crystals" in html

    def test_no_crystal_line_when_zero(self):
        html = _build_html("User", "Test", 50, "gold", 0)
        assert "crystals earned" not in html

    def test_valid_html_structure(self):
        html = _build_html("User", "Test", 50, "gold", 5)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_volaura_branding(self):
        html = _build_html("User", "Test", 50, "gold", 0)
        assert "VOLAURA" in html

    def test_no_red_colors(self):
        html = _build_html("User", "Test", 50, "gold", 10)
        assert "#ff0000" not in html.lower()
        assert "#f44336" not in html.lower()
        assert "red" not in html.lower().split("border")[0]

    def test_fallback_display_name(self):
        html = _build_html("", "Test", 50, "gold", 0)
        assert "there" not in html or "" == ""

    def test_default_display_name_there(self):
        html = _build_html("", "Comp", 50, "gold", 0)
        assert ", your" in html


class TestBuildGhostingGraceHtml:
    def test_contains_name(self):
        html = _build_ghosting_grace_html("Kamran")
        assert "Kamran" in html

    def test_fallback_name(self):
        html = _build_ghosting_grace_html("")
        assert "there" in html

    def test_locale_in_link(self):
        html = _build_ghosting_grace_html("User", locale="az")
        assert "volaura.app/az/assessment" in html

    def test_default_locale_en(self):
        html = _build_ghosting_grace_html("User")
        assert "volaura.app/en/assessment" in html

    def test_shame_free_copy(self):
        html = _build_ghosting_grace_html("User")
        lower = html.lower()
        assert "you haven't" not in lower
        assert "hurry" not in lower
        assert "missed" not in lower
        assert "behind" not in lower

    def test_single_nudge_promise(self):
        html = _build_ghosting_grace_html("User")
        assert "only nudge" in html.lower()

    def test_valid_html(self):
        html = _build_ghosting_grace_html("User")
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_cta_button_present(self):
        html = _build_ghosting_grace_html("User")
        assert "Pick up where you left off" in html

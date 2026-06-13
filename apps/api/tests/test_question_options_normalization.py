"""make_question_out must serve ONE option shape and never leak grading fields.

Regression guard for 2026-06-13 finding: the 2026-05 seed batch stored options
as {id, text, score, ...} and the per-option score — the answer key — was
served verbatim to the candidate's browser on 22 of 99 MCQ rows.
"""

from app.services.assessment.helpers import make_question_out


def _row(options):
    return {
        "id": "00000000-0000-4000-a000-000000000001",
        "type": "mcq",
        "scenario_en": "en",
        "scenario_az": "az",
        "competency_id": "00000000-0000-4000-a000-000000000002",
        "options": options,
    }


def test_classic_shape_passes_through():
    out = make_question_out(_row([{"key": "A", "text_en": "Call", "text_az": "Zəng", "text_ru": "Звонок"}]))
    assert out.options == [{"key": "A", "text_en": "Call", "text_az": "Zəng", "text_ru": "Звонок"}]


def test_legacy_id_text_score_shape_is_normalized_and_score_stripped():
    out = make_question_out(_row([
        {"id": "a", "text": "Notify immediately", "score": 1.0},
        {"id": "b", "text": "Wait", "score": 0.0, "text_ru": "Ждать"},
    ]))
    assert out.options is not None
    for opt in out.options:
        assert "score" not in opt, "grading field leaked to client"
        assert set(opt) == {"key", "text_en", "text_az", "text_ru"}
    assert out.options[0]["key"] == "a"
    assert out.options[0]["text_en"] == "Notify immediately"
    assert out.options[0]["text_az"] == "Notify immediately"  # fallback
    assert out.options[1]["text_ru"] == "Ждать"


def test_open_ended_none_options_stay_none():
    row = _row(None)
    row["type"] = "open_ended"
    assert make_question_out(row).options is None

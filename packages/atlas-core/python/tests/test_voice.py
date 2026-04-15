"""Voice validator tests — 5 rule-coverage cases + clean-pass case."""
from atlas_core import validate_voice


def test_clean_storytelling_passes():
    text = (
        "Слышу. Пошёл делать миграцию — MIN(uuid) в Postgres не существует, "
        "переписал на ORDER BY + LIMIT 1.\n\n"
        "Запушу за пять минут, отпишусь по факту."
    )
    result = validate_voice(text)
    assert result.passed, [b.type for b in result.breaches]
    assert result.breaches == []


def test_bold_headers_breach():
    text = (
        "**Статус:** хорошо\n"
        "**Что сделано:** всё\n"
        "**Следующее:** жду\n"
    )
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "bold-headers-in-chat" in types


def test_bullet_wall_breach():
    text = (
        "Вот что сделал:\n"
        "- прочитал лог\n"
        "- обновил память\n"
        "- починил баг\n"
        "- запушил\n"
    )
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "bullet-wall" in types


def test_markdown_heading_breach():
    text = "## Status\n\nВсё хорошо"
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "markdown-heading" in types


def test_markdown_table_breach():
    text = (
        "Таблица ниже:\n\n"
        "| Col | Val |\n"
        "| --- | --- |\n"
        "| a   | b   |\n"
    )
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "markdown-table-in-conversation" in types


def test_trailing_question_breach():
    text = "Проверил всё. Запускать деплой?"
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "trailing-question-on-reversible" in types


def test_trailing_question_with_options_ok():
    text = (
        "Два варианта: быстрый rollback или forward-fix с миграцией.\n\n"
        "Какой вариант берём?"
    )
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "trailing-question-on-reversible" not in types


def test_banned_opener_breach():
    text = "Готово. Вот что я сделал: всё работает."
    result = validate_voice(text)
    types = [b.type for b in result.breaches]
    assert "banned-opener" in types

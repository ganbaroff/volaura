"""Unit tests for app/routers/beta_invite.py — schemas, defaults, env loading."""

import pytest

from app.routers.beta_invite import (
    _DEFAULT_CODES,
    _load_valid_codes,
    ValidateCodeRequest,
    ValidateCodeResponse,
    router,
    RATE_VALIDATE,
)


# ── _DEFAULT_CODES ────────────────────────────────────────────────────────────

class TestDefaultCodes:
    def test_exactly_36_entries(self):
        assert len(_DEFAULT_CODES) == 36

    def test_30_beta_codes(self):
        beta = [c for c in _DEFAULT_CODES if c.startswith("BETA_")]
        assert len(beta) == 30

    def test_5_org_codes(self):
        org = [c for c in _DEFAULT_CODES if c.startswith("ORG_")]
        assert len(org) == 5

    def test_open_code_present(self):
        assert "OPEN" in _DEFAULT_CODES

    def test_contains_beta_01(self):
        assert "BETA_01" in _DEFAULT_CODES

    def test_contains_beta_30(self):
        assert "BETA_30" in _DEFAULT_CODES

    def test_contains_org_01(self):
        assert "ORG_01" in _DEFAULT_CODES

    def test_contains_org_05(self):
        assert "ORG_05" in _DEFAULT_CODES

    def test_all_uppercase(self):
        for code in _DEFAULT_CODES:
            assert code == code.upper(), f"{code!r} is not uppercase"

    def test_is_frozenset(self):
        assert isinstance(_DEFAULT_CODES, frozenset)


# ── _load_valid_codes ─────────────────────────────────────────────────────────

class TestLoadValidCodes:
    def test_no_env_vars_returns_defaults(self, monkeypatch):
        monkeypatch.delenv("INVITE_CODES", raising=False)
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        assert _load_valid_codes() == _DEFAULT_CODES

    def test_invite_codes_env_used(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "CODE_A,CODE_B,CODE_C")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        result = _load_valid_codes()
        assert result == frozenset({"CODE_A", "CODE_B", "CODE_C"})

    def test_invite_codes_uppercased(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "code_a,code_b")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        result = _load_valid_codes()
        assert "CODE_A" in result
        assert "CODE_B" in result

    def test_invite_codes_stripped(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "  TRIM_ME  ,  ALSO_THIS  ")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        result = _load_valid_codes()
        assert "TRIM_ME" in result
        assert "ALSO_THIS" in result

    def test_legacy_beta_invite_code_included(self, monkeypatch):
        monkeypatch.delenv("INVITE_CODES", raising=False)
        monkeypatch.setenv("BETA_INVITE_CODE", "LEGACY_CODE")
        result = _load_valid_codes()
        assert "LEGACY_CODE" in result

    def test_legacy_code_uppercased(self, monkeypatch):
        monkeypatch.delenv("INVITE_CODES", raising=False)
        monkeypatch.setenv("BETA_INVITE_CODE", "legacy_code")
        result = _load_valid_codes()
        assert "LEGACY_CODE" in result

    def test_both_env_vars_merged(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "CODE_A,CODE_B")
        monkeypatch.setenv("BETA_INVITE_CODE", "LEGACY_CODE")
        result = _load_valid_codes()
        assert result == frozenset({"CODE_A", "CODE_B", "LEGACY_CODE"})

    def test_empty_invite_codes_falls_back_to_defaults(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        assert _load_valid_codes() == _DEFAULT_CODES

    def test_whitespace_only_invite_codes_falls_back_to_defaults(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "   ")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        assert _load_valid_codes() == _DEFAULT_CODES

    def test_empty_legacy_code_ignored(self, monkeypatch):
        monkeypatch.delenv("INVITE_CODES", raising=False)
        monkeypatch.setenv("BETA_INVITE_CODE", "")
        assert _load_valid_codes() == _DEFAULT_CODES

    def test_returns_frozenset(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "X,Y")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        assert isinstance(_load_valid_codes(), frozenset)

    def test_comma_separated_empty_parts_ignored(self, monkeypatch):
        monkeypatch.setenv("INVITE_CODES", "CODE_A,,CODE_B,")
        monkeypatch.delenv("BETA_INVITE_CODE", raising=False)
        result = _load_valid_codes()
        assert result == frozenset({"CODE_A", "CODE_B"})


# ── ValidateCodeRequest ───────────────────────────────────────────────────────

class TestValidateCodeRequest:
    def test_strips_whitespace(self):
        req = ValidateCodeRequest(code="  BETA_01  ")
        assert req.code == "BETA_01"

    def test_uppercases_code(self):
        req = ValidateCodeRequest(code="beta_01")
        assert req.code == "BETA_01"

    def test_strips_and_uppercases(self):
        req = ValidateCodeRequest(code="  open  ")
        assert req.code == "OPEN"

    def test_already_clean_code_unchanged(self):
        req = ValidateCodeRequest(code="ORG_03")
        assert req.code == "ORG_03"

    def test_empty_string_after_strip(self):
        req = ValidateCodeRequest(code="   ")
        assert req.code == ""

    def test_empty_string_direct(self):
        req = ValidateCodeRequest(code="")
        assert req.code == ""


# ── ValidateCodeResponse ──────────────────────────────────────────────────────

class TestValidateCodeResponse:
    def test_valid_true(self):
        resp = ValidateCodeResponse(valid=True)
        assert resp.valid is True

    def test_valid_false(self):
        resp = ValidateCodeResponse(valid=False)
        assert resp.valid is False


# ── Router metadata ───────────────────────────────────────────────────────────

class TestRouterMetadata:
    def test_prefix(self):
        assert router.prefix == "/invite"

    def test_tags(self):
        assert router.tags == ["Beta Invite"]


# ── RATE_VALIDATE constant ────────────────────────────────────────────────────

class TestRateValidate:
    def test_rate_validate_value(self):
        assert RATE_VALIDATE == "10/minute"

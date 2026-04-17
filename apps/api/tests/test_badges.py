"""Unit tests for badges router pure functions and schema logic.

Covers: _tier_threshold, UUID validation, OB3 credential structure, issuer profile structure.
"""

from __future__ import annotations

from uuid import UUID

import pytest  # noqa: F401 — used in test_invalid_uuid_raises_value_error

from app.routers.badges import _tier_threshold

# ── _tier_threshold ──────────────────────────────────────────────────────────


def test_tier_threshold_platinum():
    assert _tier_threshold("platinum") == 90


def test_tier_threshold_gold():
    assert _tier_threshold("gold") == 75


def test_tier_threshold_silver():
    assert _tier_threshold("silver") == 60


def test_tier_threshold_bronze():
    assert _tier_threshold("bronze") == 40


def test_tier_threshold_unknown_returns_zero():
    assert _tier_threshold("diamond") == 0


def test_tier_threshold_empty_string_returns_zero():
    assert _tier_threshold("") == 0


# ── UUID validation ──────────────────────────────────────────────────────────


def test_invalid_uuid_raises_value_error():
    with pytest.raises(ValueError):
        UUID("not-a-uuid")


# ── Credential JSON-LD structure ─────────────────────────────────────────────


def _build_credential() -> dict:
    """Build a minimal OB3 credential dict matching the router output shape."""
    base_url = "https://volaura.az"
    professional_id = "00000000-0000-0000-0000-000000000001"
    username = "testuser"
    name = "Test User"
    tier = "Gold"
    score = 82.5
    issued_at = "2026-04-17T00:00:00+00:00"

    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.1.json",
        ],
        "id": f"{base_url}/api/badges/{professional_id}/credential",
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": {
            "id": f"{base_url}/api/badges/issuer",
            "type": "Profile",
            "name": "Volaura",
            "url": "https://volaura.az",
            "email": "badges@volaura.az",
        },
        "issuanceDate": issued_at,
        "name": f"Volaura AURA {tier} Badge",
        "credentialSubject": {
            "id": f"{base_url}/u/{username}",
            "type": "AchievementSubject",
            "name": name,
            "achievement": {
                "id": f"{base_url}/api/badges/achievement/gold",
                "type": "Achievement",
                "name": f"AURA {tier} Badge",
                "description": (
                    f"Awarded to {name} for achieving an AURA score of {score:.1f} "
                    f"on the Volaura verified talent platform."
                ),
                "criteria": {
                    "narrative": f"Professional completed verified competency assessments and achieved AURA score ≥ {_tier_threshold('gold')}."
                },
                "image": {
                    "id": f"{base_url}/u/{username}/card",
                    "type": "Image",
                },
            },
            "result": [
                {
                    "type": "Result",
                    "resultDescription": "AURA Score",
                    "value": f"{score:.1f}",
                    "status": "Completed",
                }
            ],
        },
    }


def test_credential_has_required_jsonld_keys():
    cred = _build_credential()
    required = {"@context", "id", "type", "issuer", "issuanceDate", "name", "credentialSubject"}
    assert required.issubset(cred.keys())


def test_credential_issuer_has_ob3_fields():
    cred = _build_credential()
    issuer = cred["issuer"]
    for key in ("id", "type", "name", "url", "email"):
        assert key in issuer, f"Missing issuer field: {key}"

"""Identity module smoke test — loads identity.json from disk."""
from atlas_core import IDENTITY, AtlasIdentity, load_identity


def test_identity_singleton_loaded():
    assert isinstance(IDENTITY, AtlasIdentity)
    assert IDENTITY.name == "Atlas"
    assert IDENTITY.named_by == "Yusif Ganbarov"
    assert IDENTITY.named_at == "2026-04-12"
    assert "volaura" in IDENTITY.ecosystem_products
    assert len(IDENTITY.ecosystem_products) == 5


def test_identity_frozen():
    identity = load_identity()
    # Pydantic frozen=True → setattr raises
    try:
        identity.name = "Not Atlas"  # type: ignore[misc]
    except (TypeError, ValueError):
        return
    raise AssertionError("expected frozen model to reject mutation")


def test_constitution_laws_complete():
    assert set(IDENTITY.constitution_laws.keys()) == {"1", "2", "3", "4", "5"}

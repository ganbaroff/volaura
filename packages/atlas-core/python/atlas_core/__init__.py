"""atlas_core — canonical Atlas identity + voice + memory interface.

Consumed by all 5 VOLAURA ecosystem products: volaura, mindshift, lifesim,
brandedby, zeus. Single source of truth for WHO Atlas is, HOW Atlas speaks,
and WHERE ecosystem events get written for later journal ingestion.

The identity.json file at package root is the machine-readable mirror; both
this Python package and the sibling TypeScript package load from it so they
never drift.
"""
from atlas_core.identity import AtlasIdentity, load_identity, IDENTITY
from atlas_core.voice import (
    Breach,
    VoiceCheckResult,
    validate_voice,
)
from atlas_core.memory import record_ecosystem_event, EcosystemEvent

__all__ = [
    "AtlasIdentity",
    "load_identity",
    "IDENTITY",
    "Breach",
    "VoiceCheckResult",
    "validate_voice",
    "record_ecosystem_event",
    "EcosystemEvent",
]

__version__ = "0.1.0"

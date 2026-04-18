"""Unit tests for 5 remaining Pydantic v2 schema modules.

Covers:
- admin.py: AdminUserRow, AdminOrgRow, AdminStatsResponse, OrgApproveResponse,
  AdminActivationFunnel, AdminPresenceMatrix, AdminOverviewResponse, AdminActivityEvent
- profile.py: ProfileBase, ProfileCreate, ProfileUpdate, ProfileResponse,
  PublicProfileResponse, DiscoverableProfessional
- subscription.py: SubscriptionStatus, CheckoutSessionResponse, WebhookAck,
  compute_days_remaining, build_subscription_status
- tribes.py: TribeMemberStatus, TribeOut, TribeStreakOut, KudosResponse,
  OptOutResponse, RenewalResponse, TribeMatchPreview, PoolStatusOut, TribeMatchCandidate
- verification.py: VALID_COMPETENCY_IDS, CreateVerificationLinkRequest,
  CreateVerificationLinkResponse, VerificationTokenInfo, SubmitVerificationRequest,
  SubmitVerificationResponse, TokenErrorCode
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.admin import (
    AdminActivationFunnel,
    AdminActivityEvent,
    AdminOrgRow,
    AdminOverviewResponse,
    AdminPresenceMatrix,
    AdminStatsResponse,
    AdminUserRow,
    OrgApproveResponse,
)
from app.schemas.profile import (
    DiscoverableProfessional,
    ProfileBase,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    PublicProfileResponse,
)
from app.schemas.subscription import (
    CheckoutSessionResponse,
    SubscriptionStatus,
    WebhookAck,
    build_subscription_status,
    compute_days_remaining,
)
from app.schemas.tribes import (
    KudosResponse,
    OptOutResponse,
    PoolStatusOut,
    RenewalResponse,
    TribeMatchCandidate,
    TribeMatchPreview,
    TribeMemberStatus,
    TribeOut,
    TribeStreakOut,
)
from app.schemas.verification import (
    VALID_COMPETENCY_IDS,
    CreateVerificationLinkRequest,
    CreateVerificationLinkResponse,
    SubmitVerificationRequest,
    SubmitVerificationResponse,
    TokenErrorCode,
    VerificationTokenInfo,
)

# ── Shared fixtures ──────────────────────────────────────────────────────────

NOW = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
FUTURE = NOW + timedelta(days=14)
PAST = NOW - timedelta(days=1)


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminUserRow:
    def test_required_fields(self):
        row = AdminUserRow(
            id="user-1",
            username="alice",
            account_type="professional",
            subscription_status="trial",
            created_at=NOW,
        )
        assert row.id == "user-1"
        assert row.username == "alice"
        assert row.account_type == "professional"
        assert row.subscription_status == "trial"
        assert row.created_at == NOW

    def test_optional_display_name_defaults_none(self):
        row = AdminUserRow(
            id="u",
            username="bob",
            account_type="volunteer",
            subscription_status="active",
            created_at=NOW,
        )
        assert row.display_name is None

    def test_is_platform_admin_default_false(self):
        row = AdminUserRow(
            id="u",
            username="bob",
            account_type="volunteer",
            subscription_status="active",
            created_at=NOW,
        )
        assert row.is_platform_admin is False

    def test_is_platform_admin_explicit_true(self):
        row = AdminUserRow(
            id="u",
            username="admin",
            account_type="professional",
            subscription_status="active",
            created_at=NOW,
            is_platform_admin=True,
        )
        assert row.is_platform_admin is True

    def test_from_attributes(self):
        class FakeRow:
            id = "obj-1"
            username = "charlie"
            display_name = "Charlie D"
            account_type = "organization"
            subscription_status = "expired"
            is_platform_admin = False
            created_at = NOW

        row = AdminUserRow.model_validate(FakeRow())
        assert row.username == "charlie"
        assert row.display_name == "Charlie D"

    def test_missing_required_id_raises(self):
        with pytest.raises(ValidationError):
            AdminUserRow(
                username="x",
                account_type="professional",
                subscription_status="trial",
                created_at=NOW,
            )

    def test_missing_created_at_raises(self):
        with pytest.raises(ValidationError):
            AdminUserRow(
                id="u",
                username="x",
                account_type="professional",
                subscription_status="trial",
            )


class TestAdminOrgRow:
    def test_required_fields(self):
        row = AdminOrgRow(
            id="org-1",
            name="Acme",
            owner_id="user-1",
            is_active=True,
            created_at=NOW,
        )
        assert row.id == "org-1"
        assert row.name == "Acme"
        assert row.owner_id == "user-1"
        assert row.is_active is True

    def test_optional_fields_default_none(self):
        row = AdminOrgRow(
            id="org-2",
            name="BORG",
            owner_id="u2",
            is_active=False,
            created_at=NOW,
        )
        assert row.description is None
        assert row.website is None
        assert row.owner_username is None
        assert row.trust_score is None
        assert row.verified_at is None

    def test_full_optional_fields(self):
        row = AdminOrgRow(
            id="org-3",
            name="Detailed Org",
            owner_id="u3",
            owner_username="owner",
            description="Desc",
            website="https://example.com",
            trust_score=0.95,
            verified_at=NOW,
            is_active=True,
            created_at=NOW,
        )
        assert row.trust_score == 0.95
        assert row.website == "https://example.com"
        assert row.verified_at == NOW

    def test_from_attributes(self):
        class FakeOrg:
            id = "org-fa"
            name = "FA Corp"
            description = None
            website = None
            owner_id = "u-fa"
            owner_username = None
            trust_score = None
            verified_at = None
            is_active = True
            created_at = NOW

        row = AdminOrgRow.model_validate(FakeOrg())
        assert row.name == "FA Corp"


class TestAdminStatsResponse:
    def test_all_int_fields(self):
        stats = AdminStatsResponse(
            total_users=100,
            total_organizations=10,
            pending_org_approvals=3,
            assessments_today=50,
        )
        assert stats.total_users == 100
        assert stats.total_organizations == 10
        assert stats.pending_org_approvals == 3
        assert stats.assessments_today == 50

    def test_avg_aura_score_optional_none(self):
        stats = AdminStatsResponse(
            total_users=1,
            total_organizations=0,
            pending_org_approvals=0,
            assessments_today=0,
        )
        assert stats.avg_aura_score is None

    def test_avg_aura_score_present(self):
        stats = AdminStatsResponse(
            total_users=1,
            total_organizations=0,
            pending_org_approvals=0,
            assessments_today=0,
            avg_aura_score=72.5,
        )
        assert stats.avg_aura_score == 72.5

    def test_pending_grievances_default_zero(self):
        stats = AdminStatsResponse(
            total_users=1,
            total_organizations=0,
            pending_org_approvals=0,
            assessments_today=0,
        )
        assert stats.pending_grievances == 0

    def test_pending_grievances_explicit(self):
        stats = AdminStatsResponse(
            total_users=1,
            total_organizations=0,
            pending_org_approvals=0,
            assessments_today=0,
            pending_grievances=5,
        )
        assert stats.pending_grievances == 5

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            AdminStatsResponse(total_users=1)


class TestOrgApproveResponse:
    def test_approved_action(self):
        r = OrgApproveResponse(org_id="org-1", action="approved", verified_at=NOW)
        assert r.action == "approved"
        assert r.verified_at == NOW

    def test_rejected_action(self):
        r = OrgApproveResponse(org_id="org-1", action="rejected")
        assert r.action == "rejected"
        assert r.verified_at is None

    def test_verified_at_optional_none(self):
        r = OrgApproveResponse(org_id="x", action="rejected")
        assert r.verified_at is None

    def test_missing_org_id_raises(self):
        with pytest.raises(ValidationError):
            OrgApproveResponse(action="approved")


class TestAdminActivationFunnel:
    def test_valid(self):
        f = AdminActivationFunnel(
            product="volaura",
            signups_24h=100,
            activated_24h=40,
            activation_rate=0.4,
        )
        assert f.product == "volaura"
        assert f.activation_rate == 0.4

    def test_zero_signups_zero_rate(self):
        f = AdminActivationFunnel(
            product="mindshift",
            signups_24h=0,
            activated_24h=0,
            activation_rate=0.0,
        )
        assert f.activation_rate == 0.0

    def test_missing_product_raises(self):
        with pytest.raises(ValidationError):
            AdminActivationFunnel(signups_24h=10, activated_24h=5, activation_rate=0.5)


class TestAdminPresenceMatrix:
    def test_all_fields(self):
        m = AdminPresenceMatrix(
            volaura_only=50,
            mindshift_only=30,
            both_products=20,
            total_users=100,
        )
        assert m.volaura_only == 50
        assert m.mindshift_only == 30
        assert m.both_products == 20
        assert m.total_users == 100

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            AdminPresenceMatrix(volaura_only=1, mindshift_only=1, both_products=1)


class TestAdminOverviewResponse:
    def _presence(self):
        return AdminPresenceMatrix(volaura_only=10, mindshift_only=5, both_products=3, total_users=18)

    def _funnel(self):
        return AdminActivationFunnel(product="volaura", signups_24h=10, activated_24h=4, activation_rate=0.4)

    def test_valid(self):
        ov = AdminOverviewResponse(
            activation_rate_24h=0.42,
            w4_retention=0.6,
            dau_wau_ratio=0.35,
            errors_24h=2,
            runway_months=18.0,
            presence=self._presence(),
            funnels=[self._funnel()],
            computed_at=NOW,
        )
        assert ov.activation_rate_24h == 0.42
        assert ov.stale_after_seconds == 60

    def test_stale_after_seconds_default(self):
        ov = AdminOverviewResponse(
            activation_rate_24h=0.0,
            w4_retention=None,
            dau_wau_ratio=0.0,
            errors_24h=0,
            runway_months=None,
            presence=self._presence(),
            funnels=[],
            computed_at=NOW,
        )
        assert ov.stale_after_seconds == 60

    def test_nullable_fields(self):
        ov = AdminOverviewResponse(
            activation_rate_24h=0.0,
            w4_retention=None,
            dau_wau_ratio=0.0,
            errors_24h=0,
            runway_months=None,
            presence=self._presence(),
            funnels=[],
            computed_at=NOW,
        )
        assert ov.w4_retention is None
        assert ov.runway_months is None

    def test_empty_funnels_list(self):
        ov = AdminOverviewResponse(
            activation_rate_24h=0.1,
            w4_retention=None,
            dau_wau_ratio=0.1,
            errors_24h=0,
            runway_months=None,
            presence=self._presence(),
            funnels=[],
            computed_at=NOW,
        )
        assert ov.funnels == []


class TestAdminActivityEvent:
    def test_required_fields(self):
        ev = AdminActivityEvent(
            id="ev-1",
            product="volaura",
            event_type="assessment_started",
            user_id_prefix="abcd1234",
            created_at=NOW,
        )
        assert ev.id == "ev-1"
        assert ev.product == "volaura"
        assert ev.payload_summary is None

    def test_payload_summary_present(self):
        ev = AdminActivityEvent(
            id="ev-2",
            product="mindshift",
            event_type="session_ended",
            user_id_prefix="12345678",
            created_at=NOW,
            payload_summary="Session lasted 20 min",
        )
        assert ev.payload_summary == "Session lasted 20 min"

    def test_from_attributes(self):
        class FakeEvent:
            id = "ev-fa"
            product = "zeus"
            event_type = "agent_run"
            user_id_prefix = "deadbeef"
            created_at = NOW
            payload_summary = None

        ev = AdminActivityEvent.model_validate(FakeEvent())
        assert ev.product == "zeus"
        assert ev.payload_summary is None

    def test_missing_product_raises(self):
        with pytest.raises(ValidationError):
            AdminActivityEvent(
                id="x",
                event_type="e",
                user_id_prefix="00000000",
                created_at=NOW,
            )


# ═══════════════════════════════════════════════════════════════════════════
# PROFILE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class TestProfileBase:
    def test_required_username(self):
        p = ProfileBase(username="alice")
        assert p.username == "alice"

    def test_languages_default_empty_list(self):
        p = ProfileBase(username="bob")
        assert p.languages == []

    def test_social_links_default_empty_dict(self):
        p = ProfileBase(username="bob")
        assert p.social_links == {}

    def test_is_public_default_true(self):
        p = ProfileBase(username="bob")
        assert p.is_public is True

    def test_optional_fields_all_none(self):
        p = ProfileBase(username="x")
        assert p.display_name is None
        assert p.bio is None
        assert p.location is None

    def test_full_fields(self):
        p = ProfileBase(
            username="charlie",
            display_name="Charlie D",
            bio="Developer",
            location="Baku",
            languages=["az", "en"],
            social_links={"github": "charlie"},
            is_public=False,
        )
        assert p.location == "Baku"
        assert p.languages == ["az", "en"]
        assert p.is_public is False

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            ProfileBase()


class TestProfileCreate:
    def test_valid_username(self):
        p = ProfileCreate(username="alice-dev")
        assert p.username == "alice-dev"

    def test_username_stripped_and_lowercased(self):
        p = ProfileCreate(username="  ALICE  ")
        assert p.username == "alice"

    def test_username_too_short(self):
        with pytest.raises(ValidationError, match="3-30"):
            ProfileCreate(username="ab")

    def test_username_too_long(self):
        with pytest.raises(ValidationError, match="3-30"):
            ProfileCreate(username="a" * 31)

    def test_username_boundary_3_chars(self):
        p = ProfileCreate(username="abc")
        assert p.username == "abc"

    def test_username_boundary_30_chars(self):
        p = ProfileCreate(username="a" * 30)
        assert len(p.username) == 30

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError, match="letters, numbers"):
            ProfileCreate(username="alice@dev")

    def test_username_allows_hyphen_underscore(self):
        p = ProfileCreate(username="alice_dev-123")
        assert p.username == "alice_dev-123"

    def test_account_type_valid_values(self):
        for at in ("professional", "volunteer", "organization"):
            p = ProfileCreate(username="alice", account_type=at)
            assert p.account_type == at

    def test_account_type_invalid(self):
        with pytest.raises(ValidationError, match="account_type"):
            ProfileCreate(username="alice", account_type="admin")

    def test_account_type_default_professional(self):
        p = ProfileCreate(username="alice")
        assert p.account_type == "professional"

    def test_org_type_valid_values(self):
        for ot in ("ngo", "corporate", "government", "startup", "academic", "other"):
            p = ProfileCreate(username="org", account_type="organization", org_type=ot)
            assert p.org_type == ot

    def test_org_type_none_allowed(self):
        p = ProfileCreate(username="alice", org_type=None)
        assert p.org_type is None

    def test_org_type_invalid(self):
        with pytest.raises(ValidationError, match="Invalid org_type"):
            ProfileCreate(username="alice", org_type="school")

    def test_age_confirmed_default_false(self):
        p = ProfileCreate(username="alice")
        assert p.age_confirmed is False

    def test_terms_version_default(self):
        p = ProfileCreate(username="alice")
        assert p.terms_version == "1.0"

    def test_invited_by_org_id_optional(self):
        p = ProfileCreate(username="alice", invited_by_org_id="org-123")
        assert p.invited_by_org_id == "org-123"


class TestProfileUpdate:
    def test_all_fields_optional(self):
        p = ProfileUpdate()
        assert p.display_name is None
        assert p.bio is None
        assert p.location is None
        assert p.languages is None
        assert p.social_links is None
        assert p.is_public is None
        assert p.visible_to_orgs is None

    def test_partial_update(self):
        p = ProfileUpdate(display_name="New Name", is_public=False)
        assert p.display_name == "New Name"
        assert p.is_public is False
        assert p.bio is None

    def test_attribution_fields(self):
        p = ProfileUpdate(
            referral_code="REF123",
            utm_source="google",
            utm_campaign="spring2026",
        )
        assert p.referral_code == "REF123"
        assert p.utm_source == "google"

    def test_energy_level_field(self):
        p = ProfileUpdate(energy_level="full")
        assert p.energy_level == "full"


class TestProfileResponse:
    def test_from_attributes(self):
        class FakeProfile:
            id = "p-1"
            username = "alice"
            display_name = "Alice"
            bio = None
            location = None
            languages = []
            social_links = {}
            is_public = True
            avatar_url = None
            account_type = "professional"
            visible_to_orgs = False
            org_type = None
            badge_issued_at = None
            badge_open_badges_url = None
            created_at = NOW
            updated_at = NOW
            age_confirmed = True
            terms_version = "1.0"
            terms_accepted_at = NOW
            registration_number = 42
            registration_tier = "founding_100"
            subscription_status = "trial"
            trial_ends_at = FUTURE
            is_subscription_active = True

        r = ProfileResponse.model_validate(FakeProfile())
        assert r.id == "p-1"
        assert r.registration_number == 42
        assert r.registration_tier == "founding_100"
        assert r.is_subscription_active is True

    def test_subscription_status_default_trial(self):
        r = ProfileResponse(
            id="p",
            username="bob",
            created_at=NOW,
            updated_at=NOW,
        )
        assert r.subscription_status == "trial"

    def test_is_subscription_active_default_true(self):
        r = ProfileResponse(
            id="p",
            username="bob",
            created_at=NOW,
            updated_at=NOW,
        )
        assert r.is_subscription_active is True

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            ProfileResponse(username="bob", created_at=NOW, updated_at=NOW)


class TestPublicProfileResponse:
    def test_minimal(self):
        r = PublicProfileResponse(id="p", username="alice")
        assert r.id == "p"
        assert r.username == "alice"
        assert r.display_name is None
        assert r.languages == []

    def test_percentile_rank_optional(self):
        r = PublicProfileResponse(id="p", username="alice", percentile_rank=85.5)
        assert r.percentile_rank == 85.5

    def test_from_attributes(self):
        class FakePub:
            id = "pub-1"
            username = "public_user"
            display_name = None
            avatar_url = None
            bio = None
            location = None
            languages = ["en"]
            badge_issued_at = None
            registration_number = None
            registration_tier = None
            percentile_rank = None

        r = PublicProfileResponse.model_validate(FakePub())
        assert r.username == "public_user"
        assert r.languages == ["en"]

    def test_registration_tier_values(self):
        for tier in ("founding_100", "founding_1000", "early_adopter", "standard"):
            r = PublicProfileResponse(id="p", username="u", registration_tier=tier)
            assert r.registration_tier == tier


class TestDiscoverableProfessional:
    def test_minimal(self):
        r = DiscoverableProfessional(id="d", username="pro")
        assert r.total_score is None
        assert r.badge_tier is None

    def test_aura_fields_present(self):
        r = DiscoverableProfessional(
            id="d",
            username="pro",
            total_score=82.3,
            badge_tier="Gold",
        )
        assert r.total_score == 82.3
        assert r.badge_tier == "Gold"

    def test_from_attributes(self):
        class FakeDisc:
            id = "disc-1"
            username = "discoverable"
            display_name = "Disc"
            avatar_url = None
            bio = "Expert"
            location = "Baku"
            languages = ["en", "az"]
            total_score = 75.0
            badge_tier = "Silver"

        r = DiscoverableProfessional.model_validate(FakeDisc())
        assert r.total_score == 75.0
        assert r.badge_tier == "Silver"


# ═══════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class TestSubscriptionStatus:
    def test_valid(self):
        s = SubscriptionStatus(
            status="trial",
            trial_ends_at=FUTURE,
            subscription_ends_at=None,
            days_remaining=14,
            is_active=True,
        )
        assert s.status == "trial"
        assert s.is_active is True

    def test_expired_status(self):
        s = SubscriptionStatus(
            status="expired",
            trial_ends_at=None,
            subscription_ends_at=PAST,
            days_remaining=0,
            is_active=False,
        )
        assert s.days_remaining == 0
        assert s.is_active is False

    def test_both_ends_at_none(self):
        s = SubscriptionStatus(
            status="cancelled",
            trial_ends_at=None,
            subscription_ends_at=None,
            days_remaining=0,
            is_active=False,
        )
        assert s.trial_ends_at is None
        assert s.subscription_ends_at is None

    def test_from_attributes(self):
        class FakeSub:
            status = "active"
            trial_ends_at = None
            subscription_ends_at = FUTURE
            days_remaining = 14
            is_active = True

        s = SubscriptionStatus.model_validate(FakeSub())
        assert s.status == "active"


class TestCheckoutSessionResponse:
    def test_valid(self):
        r = CheckoutSessionResponse(checkout_url="https://checkout.stripe.com/abc")
        assert r.checkout_url == "https://checkout.stripe.com/abc"

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            CheckoutSessionResponse()


class TestWebhookAck:
    def test_default_received_true(self):
        r = WebhookAck()
        assert r.received is True

    def test_explicit_false(self):
        r = WebhookAck(received=False)
        assert r.received is False


class TestComputeDaysRemaining:
    def test_trial_status_returns_days(self):
        trial_end = datetime.now(UTC) + timedelta(days=7)
        result = compute_days_remaining("trial", trial_end, None)
        # timedelta.days truncates sub-day fractions: expect 6 or 7
        assert result in (6, 7)

    def test_active_status_returns_days(self):
        sub_end = datetime.now(UTC) + timedelta(days=30)
        result = compute_days_remaining("active", None, sub_end)
        assert result in (29, 30)

    def test_expired_status_returns_zero(self):
        result = compute_days_remaining("expired", PAST, PAST)
        assert result == 0

    def test_cancelled_status_returns_zero(self):
        result = compute_days_remaining("cancelled", None, None)
        assert result == 0

    def test_trial_already_ended_returns_zero(self):
        ended = datetime.now(UTC) - timedelta(days=3)
        result = compute_days_remaining("trial", ended, None)
        assert result == 0

    def test_active_already_ended_returns_zero(self):
        ended = datetime.now(UTC) - timedelta(days=1)
        result = compute_days_remaining("active", None, ended)
        assert result == 0

    def test_trial_no_trial_ends_at_returns_zero(self):
        result = compute_days_remaining("trial", None, None)
        assert result == 0

    def test_active_no_subscription_ends_at_returns_zero(self):
        result = compute_days_remaining("active", None, None)
        assert result == 0


class TestBuildSubscriptionStatus:
    def test_trial_profile(self):
        trial_end = datetime.now(UTC) + timedelta(days=10)
        row = {"subscription_status": "trial", "trial_ends_at": trial_end, "subscription_ends_at": None}
        s = build_subscription_status(row)
        assert s.status == "trial"
        assert s.is_active is True
        assert s.days_remaining in (9, 10)

    def test_active_profile(self):
        sub_end = datetime.now(UTC) + timedelta(days=25)
        row = {"subscription_status": "active", "trial_ends_at": None, "subscription_ends_at": sub_end}
        s = build_subscription_status(row)
        assert s.status == "active"
        assert s.is_active is True
        assert s.days_remaining in (24, 25)

    def test_expired_profile_is_not_active(self):
        row = {"subscription_status": "expired", "trial_ends_at": None, "subscription_ends_at": PAST}
        s = build_subscription_status(row)
        assert s.is_active is False
        assert s.days_remaining == 0

    def test_tz_naive_datetime_normalized_to_utc(self):
        naive_dt = datetime(2026, 5, 1, 12, 0, 0)  # no tzinfo
        row = {"subscription_status": "trial", "trial_ends_at": naive_dt, "subscription_ends_at": None}
        s = build_subscription_status(row)
        assert s.trial_ends_at is not None
        assert s.trial_ends_at.tzinfo is not None

    def test_iso_string_with_z_parsed(self):
        row = {
            "subscription_status": "active",
            "trial_ends_at": None,
            "subscription_ends_at": "2026-12-31T23:59:59Z",
        }
        s = build_subscription_status(row)
        assert s.subscription_ends_at is not None
        assert s.subscription_ends_at.year == 2026

    def test_iso_string_with_offset_parsed(self):
        row = {
            "subscription_status": "active",
            "trial_ends_at": None,
            "subscription_ends_at": "2026-12-31T23:59:59+04:00",
        }
        s = build_subscription_status(row)
        assert s.subscription_ends_at is not None

    def test_missing_status_defaults_to_trial(self):
        row = {"trial_ends_at": None, "subscription_ends_at": None}
        s = build_subscription_status(row)
        assert s.status == "trial"

    def test_none_datetimes_pass_through(self):
        row = {"subscription_status": "cancelled", "trial_ends_at": None, "subscription_ends_at": None}
        s = build_subscription_status(row)
        assert s.trial_ends_at is None
        assert s.subscription_ends_at is None


# ═══════════════════════════════════════════════════════════════════════════
# TRIBES SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class TestTribeMemberStatus:
    def test_required_fields(self):
        m = TribeMemberStatus(
            user_id="u1",
            display_name="Alice",
            active_this_week=True,
        )
        assert m.user_id == "u1"
        assert m.active_this_week is True

    def test_avatar_url_optional(self):
        m = TribeMemberStatus(user_id="u", display_name="Bob", active_this_week=False)
        assert m.avatar_url is None

    def test_avatar_url_present(self):
        m = TribeMemberStatus(
            user_id="u",
            display_name="Carol",
            active_this_week=True,
            avatar_url="https://example.com/avatar.jpg",
        )
        assert m.avatar_url == "https://example.com/avatar.jpg"

    def test_from_attributes(self):
        class FakeMember:
            user_id = "fa-u"
            display_name = "FA User"
            avatar_url = None
            active_this_week = False

        m = TribeMemberStatus.model_validate(FakeMember())
        assert m.display_name == "FA User"

    def test_missing_active_this_week_raises(self):
        with pytest.raises(ValidationError):
            TribeMemberStatus(user_id="u", display_name="X")


class TestTribeOut:
    def _member(self):
        return TribeMemberStatus(user_id="u", display_name="User", active_this_week=True)

    def test_valid_active(self):
        t = TribeOut(
            tribe_id="t1",
            expires_at=FUTURE,
            status="active",
            members=[self._member()],
            kudos_count_this_week=3,
            renewal_requested=False,
        )
        assert t.status == "active"
        assert t.kudos_count_this_week == 3

    def test_status_expired(self):
        t = TribeOut(
            tribe_id="t2",
            expires_at=PAST,
            status="expired",
            members=[self._member()],
            kudos_count_this_week=0,
            renewal_requested=True,
        )
        assert t.status == "expired"
        assert t.renewal_requested is True

    def test_status_dissolved(self):
        t = TribeOut(
            tribe_id="t3",
            expires_at=PAST,
            status="dissolved",
            members=[],
            kudos_count_this_week=0,
            renewal_requested=False,
        )
        assert t.status == "dissolved"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            TribeOut(
                tribe_id="t",
                expires_at=FUTURE,
                status="pending",
                members=[],
                kudos_count_this_week=0,
                renewal_requested=False,
            )

    def test_empty_members_list(self):
        t = TribeOut(
            tribe_id="t",
            expires_at=FUTURE,
            status="active",
            members=[],
            kudos_count_this_week=0,
            renewal_requested=False,
        )
        assert t.members == []


class TestTribeStreakOut:
    def test_valid(self):
        s = TribeStreakOut(
            current_streak=5,
            longest_streak=10,
            last_activity_week="2026-W15",
            consecutive_misses_count=0,
            crystal_fade_level=0,
        )
        assert s.current_streak == 5
        assert s.crystal_fade_level == 0

    def test_crystal_fade_level_1(self):
        s = TribeStreakOut(
            current_streak=3,
            longest_streak=10,
            last_activity_week="2026-W14",
            consecutive_misses_count=1,
            crystal_fade_level=1,
        )
        assert s.crystal_fade_level == 1

    def test_crystal_fade_level_2(self):
        s = TribeStreakOut(
            current_streak=0,
            longest_streak=10,
            last_activity_week=None,
            consecutive_misses_count=2,
            crystal_fade_level=2,
        )
        assert s.crystal_fade_level == 2

    def test_invalid_crystal_fade_level_raises(self):
        with pytest.raises(ValidationError):
            TribeStreakOut(
                current_streak=0,
                longest_streak=0,
                last_activity_week=None,
                consecutive_misses_count=3,
                crystal_fade_level=3,
            )

    def test_last_activity_week_optional(self):
        s = TribeStreakOut(
            current_streak=0,
            longest_streak=5,
            last_activity_week=None,
            consecutive_misses_count=0,
            crystal_fade_level=0,
        )
        assert s.last_activity_week is None

    def test_from_attributes(self):
        class FakeStreak:
            current_streak = 7
            longest_streak = 12
            last_activity_week = "2026-W16"
            consecutive_misses_count = 0
            crystal_fade_level = 0

        s = TribeStreakOut.model_validate(FakeStreak())
        assert s.current_streak == 7


class TestKudosResponse:
    def test_default(self):
        k = KudosResponse()
        assert k.sent is True
        assert "Kudos" in k.message

    def test_explicit(self):
        k = KudosResponse(sent=False, message="Already sent")
        assert k.sent is False


class TestOptOutResponse:
    def test_default(self):
        r = OptOutResponse()
        assert r.success is True
        assert "tribe" in r.message.lower()


class TestRenewalResponse:
    def test_required_message(self):
        r = RenewalResponse(message="Renewal requested.")
        assert r.renewal_requested is True
        assert r.all_members_requested is False

    def test_all_members_requested_true(self):
        r = RenewalResponse(message="All in!", all_members_requested=True)
        assert r.all_members_requested is True

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            RenewalResponse()


class TestTribeMatchPreview:
    def test_defaults(self):
        p = TribeMatchPreview()
        assert p.in_pool is True
        assert "24 hours" in p.estimated_wait


class TestPoolStatusOut:
    def test_in_pool_true(self):
        p = PoolStatusOut(in_pool=True, joined_at="2026-04-18T10:00:00Z")
        assert p.in_pool is True
        assert p.joined_at == "2026-04-18T10:00:00Z"

    def test_not_in_pool(self):
        p = PoolStatusOut(in_pool=False)
        assert p.in_pool is False
        assert p.joined_at is None

    def test_missing_in_pool_raises(self):
        with pytest.raises(ValidationError):
            PoolStatusOut()


class TestTribeMatchCandidate:
    def test_valid(self):
        c = TribeMatchCandidate(
            user_id="u1",
            aura_score=78.5,
            assessments_last_30d=3,
        )
        assert c.aura_score == 78.5
        assert c.previous_co_member_ids == []

    def test_previous_co_member_ids_default_factory(self):
        c1 = TribeMatchCandidate(user_id="u1", aura_score=70.0, assessments_last_30d=1)
        c2 = TribeMatchCandidate(user_id="u2", aura_score=80.0, assessments_last_30d=2)
        # Each instance must have an independent list
        c1.previous_co_member_ids.append("other")
        assert c2.previous_co_member_ids == []

    def test_previous_co_member_ids_populated(self):
        c = TribeMatchCandidate(
            user_id="u1",
            aura_score=60.0,
            assessments_last_30d=0,
            previous_co_member_ids=["u2", "u3"],
        )
        assert len(c.previous_co_member_ids) == 2

    def test_missing_aura_score_raises(self):
        with pytest.raises(ValidationError):
            TribeMatchCandidate(user_id="u", assessments_last_30d=1)


# ═══════════════════════════════════════════════════════════════════════════
# VERIFICATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class TestValidCompetencyIds:
    def test_has_all_eight(self):
        assert len(VALID_COMPETENCY_IDS) == 8

    def test_expected_ids_present(self):
        expected = {
            "communication",
            "reliability",
            "english_proficiency",
            "leadership",
            "event_performance",
            "tech_literacy",
            "adaptability",
            "empathy_safeguarding",
        }
        assert expected == VALID_COMPETENCY_IDS

    def test_is_frozenset(self):
        assert isinstance(VALID_COMPETENCY_IDS, frozenset)


class TestCreateVerificationLinkRequest:
    def test_valid_minimal(self):
        r = CreateVerificationLinkRequest(
            verifier_name="John Doe",
            competency_id="leadership",
        )
        assert r.verifier_name == "John Doe"
        assert r.verifier_org is None

    def test_verifier_name_stripped(self):
        r = CreateVerificationLinkRequest(
            verifier_name="  Jane Smith  ",
            competency_id="reliability",
        )
        assert r.verifier_name == "Jane Smith"

    def test_verifier_name_too_short(self):
        with pytest.raises(ValidationError):
            CreateVerificationLinkRequest(verifier_name="A", competency_id="leadership")

    def test_verifier_name_too_long(self):
        with pytest.raises(ValidationError):
            CreateVerificationLinkRequest(
                verifier_name="x" * 101,
                competency_id="leadership",
            )

    def test_verifier_name_boundary_2_chars(self):
        r = CreateVerificationLinkRequest(verifier_name="AB", competency_id="leadership")
        assert r.verifier_name == "AB"

    def test_verifier_name_boundary_100_chars(self):
        r = CreateVerificationLinkRequest(
            verifier_name="x" * 100,
            competency_id="reliability",
        )
        assert len(r.verifier_name) == 100

    def test_verifier_org_stripped(self):
        r = CreateVerificationLinkRequest(
            verifier_name="Tester",
            verifier_org="  ACME Corp  ",
            competency_id="communication",
        )
        assert r.verifier_org == "ACME Corp"

    def test_verifier_org_too_long(self):
        with pytest.raises(ValidationError):
            CreateVerificationLinkRequest(
                verifier_name="Tester",
                verifier_org="x" * 101,
                competency_id="leadership",
            )

    def test_verifier_org_none_becomes_none(self):
        r = CreateVerificationLinkRequest(
            verifier_name="Tester",
            verifier_org=None,
            competency_id="adaptability",
        )
        assert r.verifier_org is None

    def test_verifier_org_empty_string_becomes_none(self):
        r = CreateVerificationLinkRequest(
            verifier_name="Tester",
            verifier_org="",
            competency_id="adaptability",
        )
        assert r.verifier_org is None

    def test_all_valid_competency_ids(self):
        for cid in VALID_COMPETENCY_IDS:
            r = CreateVerificationLinkRequest(verifier_name="Tester", competency_id=cid)
            assert r.competency_id == cid

    def test_invalid_competency_id_raises(self):
        with pytest.raises(ValidationError, match="Invalid competency_id"):
            CreateVerificationLinkRequest(
                verifier_name="Tester",
                competency_id="charisma",
            )

    def test_empty_competency_id_raises(self):
        with pytest.raises(ValidationError, match="Invalid competency_id"):
            CreateVerificationLinkRequest(verifier_name="Tester", competency_id="")


class TestCreateVerificationLinkResponse:
    def test_valid(self):
        r = CreateVerificationLinkResponse(
            id="vl-1",
            token="tok-abc",
            verify_url="https://volaura.az/az/verify/tok-abc",
            expires_at=FUTURE,
            verifier_name="John",
            verifier_org=None,
            competency_id="leadership",
        )
        assert r.token == "tok-abc"
        assert r.verifier_org is None

    def test_from_attributes(self):
        class FakeLink:
            id = "vl-fa"
            token = "fa-tok"
            verify_url = "https://volaura.az/en/verify/fa-tok"
            expires_at = FUTURE
            verifier_name = "Jane"
            verifier_org = "ACME"
            competency_id = "reliability"

        r = CreateVerificationLinkResponse.model_validate(FakeLink())
        assert r.verifier_org == "ACME"

    def test_missing_token_raises(self):
        with pytest.raises(ValidationError):
            CreateVerificationLinkResponse(
                id="x",
                verify_url="https://example.com",
                expires_at=FUTURE,
                verifier_name="J",
                verifier_org=None,
                competency_id="leadership",
            )


class TestVerificationTokenInfo:
    def test_valid(self):
        info = VerificationTokenInfo(
            professional_display_name="Alice Pro",
            professional_username="alicepro",
            professional_avatar_url=None,
            verifier_name="Bob",
            verifier_org="ACME",
            competency_id="communication",
        )
        assert info.professional_username == "alicepro"
        assert info.professional_avatar_url is None

    def test_from_attributes(self):
        class FakeInfo:
            professional_display_name = "Pro User"
            professional_username = "prouser"
            professional_avatar_url = "https://example.com/img.jpg"
            verifier_name = "Verifier"
            verifier_org = None
            competency_id = "leadership"

        info = VerificationTokenInfo.model_validate(FakeInfo())
        assert info.verifier_org is None


class TestSubmitVerificationRequest:
    def test_valid_rating(self):
        r = SubmitVerificationRequest(rating=4.5)
        assert r.rating == 4.5
        assert r.comment is None

    def test_rating_min_boundary(self):
        r = SubmitVerificationRequest(rating=1.0)
        assert r.rating == 1.0

    def test_rating_max_boundary(self):
        r = SubmitVerificationRequest(rating=5.0)
        assert r.rating == 5.0

    def test_rating_below_min_raises(self):
        with pytest.raises(ValidationError):
            SubmitVerificationRequest(rating=0.9)

    def test_rating_above_max_raises(self):
        with pytest.raises(ValidationError):
            SubmitVerificationRequest(rating=5.1)

    def test_comment_stripped(self):
        r = SubmitVerificationRequest(rating=3.0, comment="  Great work!  ")
        assert r.comment == "Great work!"

    def test_comment_whitespace_only_becomes_none(self):
        r = SubmitVerificationRequest(rating=3.0, comment="   ")
        assert r.comment is None

    def test_comment_too_long_raises(self):
        with pytest.raises(ValidationError):
            SubmitVerificationRequest(rating=3.0, comment="x" * 501)

    def test_comment_max_boundary(self):
        r = SubmitVerificationRequest(rating=3.0, comment="x" * 500)
        assert r.comment == "x" * 500

    def test_comment_none_stays_none(self):
        r = SubmitVerificationRequest(rating=5.0, comment=None)
        assert r.comment is None

    def test_missing_rating_raises(self):
        with pytest.raises(ValidationError):
            SubmitVerificationRequest()


class TestSubmitVerificationResponse:
    def test_default_status(self):
        r = SubmitVerificationResponse(
            professional_display_name="Alice",
            competency_id="leadership",
            rating=4.5,
        )
        assert r.status == "verified"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            SubmitVerificationResponse(
                status="pending",
                professional_display_name="Alice",
                competency_id="leadership",
                rating=4.5,
            )

    def test_all_fields(self):
        r = SubmitVerificationResponse(
            status="verified",
            professional_display_name="Bob",
            competency_id="reliability",
            rating=3.0,
        )
        assert r.rating == 3.0
        assert r.competency_id == "reliability"


class TestTokenErrorCode:
    def test_token_invalid(self):
        e = TokenErrorCode(code="TOKEN_INVALID", message="Token not found")
        assert e.code == "TOKEN_INVALID"

    def test_token_expired(self):
        e = TokenErrorCode(code="TOKEN_EXPIRED", message="Token has expired")
        assert e.code == "TOKEN_EXPIRED"

    def test_token_already_used(self):
        e = TokenErrorCode(code="TOKEN_ALREADY_USED", message="Token already used")
        assert e.code == "TOKEN_ALREADY_USED"

    def test_invalid_code_raises(self):
        with pytest.raises(ValidationError):
            TokenErrorCode(code="TOKEN_REVOKED", message="msg")

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            TokenErrorCode(code="TOKEN_INVALID")

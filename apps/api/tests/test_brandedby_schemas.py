"""Unit tests for BrandedBy schemas — AI Twin + Generation models.

Covers:
- AITwinCreate: display_name whitespace collapse, min/max length, tagline max
- AITwinUpdate: partial updates, no-change detection
- AITwinOut: from_attributes construction
- GenerationCreate: gen_type validation, input_text 3-word minimum, skip_queue
- GenerationOut: construction with all fields
- Literal type enforcement for TwinStatus and GenerationType
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.brandedby import (
    AITwinCreate,
    AITwinOut,
    AITwinUpdate,
    GenerationCreate,
    GenerationOut,
)


class TestAITwinCreate:
    def test_valid_minimal(self):
        t = AITwinCreate(display_name="Yusif")
        assert t.display_name == "Yusif"
        assert t.tagline is None
        assert t.photo_url is None

    def test_whitespace_collapse(self):
        t = AITwinCreate(display_name="  John   Doe  ")
        assert t.display_name == "John Doe"

    def test_display_name_too_short(self):
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            AITwinCreate(display_name="")

    def test_display_name_too_long(self):
        with pytest.raises(ValidationError):
            AITwinCreate(display_name="x" * 101)

    def test_display_name_max_boundary(self):
        t = AITwinCreate(display_name="x" * 100)
        assert len(t.display_name) == 100

    def test_tagline_max_length(self):
        with pytest.raises(ValidationError):
            AITwinCreate(display_name="Test", tagline="x" * 201)

    def test_tagline_max_boundary(self):
        t = AITwinCreate(display_name="Test", tagline="y" * 200)
        assert len(t.tagline) == 200

    def test_full_create(self):
        t = AITwinCreate(
            display_name="Atlas Twin",
            tagline="Your AI companion",
            photo_url="https://example.com/photo.jpg",
        )
        assert t.display_name == "Atlas Twin"
        assert t.tagline == "Your AI companion"
        assert t.photo_url == "https://example.com/photo.jpg"

    def test_strip_whitespace(self):
        t = AITwinCreate(display_name="  trimmed  ", tagline="  tag  ")
        assert t.display_name == "trimmed"
        assert t.tagline == "tag"


class TestAITwinUpdate:
    def test_empty_update(self):
        u = AITwinUpdate()
        assert u.model_dump(exclude_unset=True) == {}

    def test_partial_update_display_name(self):
        u = AITwinUpdate(display_name="New Name")
        dumped = u.model_dump(exclude_unset=True)
        assert dumped == {"display_name": "New Name"}

    def test_partial_update_status(self):
        u = AITwinUpdate(status="active")
        dumped = u.model_dump(exclude_unset=True)
        assert dumped == {"status": "active"}

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="Input should be"):
            AITwinUpdate(status="deleted")

    def test_valid_statuses(self):
        for s in ("draft", "active", "suspended"):
            u = AITwinUpdate(status=s)
            assert u.status == s

    def test_display_name_min_length(self):
        with pytest.raises(ValidationError):
            AITwinUpdate(display_name="")

    def test_tagline_max(self):
        with pytest.raises(ValidationError):
            AITwinUpdate(tagline="z" * 201)


class TestAITwinOut:
    def _make(self, **overrides):
        defaults = {
            "id": uuid4(),
            "user_id": uuid4(),
            "display_name": "Twin",
            "status": "draft",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return AITwinOut(**defaults)

    def test_minimal_construction(self):
        t = self._make()
        assert t.tagline is None
        assert t.photo_url is None
        assert t.voice_id is None
        assert t.personality_prompt is None

    def test_full_construction(self):
        t = self._make(
            tagline="hello",
            photo_url="https://x.com/p.jpg",
            voice_id="v123",
            personality_prompt="You are a helpful twin",
        )
        assert t.voice_id == "v123"
        assert t.personality_prompt == "You are a helpful twin"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AITwinOut(id=uuid4(), display_name="X")


class TestGenerationCreate:
    def test_valid_minimal(self):
        g = GenerationCreate(
            twin_id=uuid4(),
            input_text="Please generate a greeting video",
        )
        assert g.gen_type == "video"
        assert g.skip_queue is False

    def test_valid_gen_types(self):
        for gt in ("video", "audio", "text_chat"):
            g = GenerationCreate(
                twin_id=uuid4(),
                gen_type=gt,
                input_text="Hello world test script",
            )
            assert g.gen_type == gt

    def test_invalid_gen_type(self):
        with pytest.raises(ValidationError, match="Input should be"):
            GenerationCreate(
                twin_id=uuid4(),
                gen_type="image",
                input_text="Hello world test script",
            )

    def test_input_text_too_short_empty(self):
        with pytest.raises(ValidationError):
            GenerationCreate(twin_id=uuid4(), input_text="")

    def test_input_text_fewer_than_3_words(self):
        with pytest.raises(ValidationError, match="3 words"):
            GenerationCreate(twin_id=uuid4(), input_text="hi there")

    def test_input_text_exactly_3_words(self):
        g = GenerationCreate(twin_id=uuid4(), input_text="hello world test")
        assert g.input_text == "hello world test"

    def test_input_text_max_length(self):
        with pytest.raises(ValidationError):
            GenerationCreate(twin_id=uuid4(), input_text="word " * 401)

    def test_input_text_max_boundary(self):
        text = "a " * 999 + "b"
        if len(text) <= 2000:
            g = GenerationCreate(twin_id=uuid4(), input_text=text)
            assert len(g.input_text.split()) >= 3

    def test_skip_queue_true(self):
        g = GenerationCreate(
            twin_id=uuid4(),
            input_text="Please create this video now",
            skip_queue=True,
        )
        assert g.skip_queue is True

    def test_strip_whitespace_input(self):
        g = GenerationCreate(
            twin_id=uuid4(),
            input_text="  hello world test  ",
        )
        assert g.input_text == "hello world test"

    def test_single_long_word_fails_3_word_check(self):
        with pytest.raises(ValidationError, match="3 words"):
            GenerationCreate(twin_id=uuid4(), input_text="superlongword")


class TestGenerationOut:
    def _make(self, **overrides):
        defaults = {
            "id": uuid4(),
            "twin_id": uuid4(),
            "user_id": uuid4(),
            "gen_type": "video",
            "input_text": "test script content here",
            "status": "queued",
            "crystal_cost": 0,
            "created_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return GenerationOut(**defaults)

    def test_minimal_construction(self):
        g = self._make()
        assert g.output_url is None
        assert g.thumbnail_url is None
        assert g.error_message is None
        assert g.queue_position is None
        assert g.duration_seconds is None
        assert g.processing_started_at is None
        assert g.completed_at is None

    def test_completed_generation(self):
        now = datetime.now(UTC)
        g = self._make(
            status="completed",
            output_url="https://cdn.example.com/video.mp4",
            thumbnail_url="https://cdn.example.com/thumb.jpg",
            crystal_cost=25,
            duration_seconds=30,
            queue_position=0,
            processing_started_at=now,
            completed_at=now,
        )
        assert g.status == "completed"
        assert g.crystal_cost == 25
        assert g.duration_seconds == 30

    def test_failed_generation(self):
        g = self._make(
            status="failed",
            error_message="GPU out of memory",
        )
        assert g.error_message == "GPU out of memory"

"""Unit tests for app.services.atlas_tools — @atlas_tool registry, ToolResult, ToolSpec, sha12."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ValidationError

from app.services.atlas_tools import (
    REGISTRY,
    AtlasTool,
    ToolResult,
    ToolSpec,
    atlas_tool,
    compute_payload_sha12,
    extract_action_payload,
)

# ── ToolResult ──────────────────────────────────────────────────────────────


class TestToolResult:
    def test_success_minimal(self):
        r = ToolResult.success()
        assert r.ok is True
        assert r.anchor is None
        assert r.error is None
        assert r.data == {}

    def test_success_with_anchor_and_data(self):
        r = ToolResult.success(anchor="https://github.com/issue/1", count=3)
        assert r.ok is True
        assert r.anchor == "https://github.com/issue/1"
        assert r.data == {"count": 3}

    def test_fail_minimal(self):
        r = ToolResult.fail("something broke")
        assert r.ok is False
        assert r.error == "something broke"

    def test_fail_truncates_error_at_500(self):
        long_error = "x" * 1000
        r = ToolResult.fail(long_error)
        assert len(r.error) == 500

    def test_fail_with_extra_data(self):
        r = ToolResult.fail("oops", code=422, detail="bad input")
        assert r.data == {"code": 422, "detail": "bad input"}

    def test_frozen(self):
        r = ToolResult.success()
        with pytest.raises(ValidationError):
            r.ok = False


# ── ToolSpec ────────────────────────────────────────────────────────────────


class TestToolSpec:
    def test_construction(self):
        s = ToolSpec(
            name="test_tool",
            description="A test",
            requires_approval=True,
            args_schema={"type": "object"},
        )
        assert s.name == "test_tool"
        assert s.requires_approval is True

    def test_frozen(self):
        s = ToolSpec(name="t", description="d", requires_approval=False, args_schema={})
        with pytest.raises(ValidationError):
            s.name = "changed"


# ── AtlasTool ───────────────────────────────────────────────────────────────


class _DummyArgs(BaseModel):
    text: str
    count: int = 1


async def _dummy_fn(args: _DummyArgs) -> ToolResult:
    return ToolResult.success(anchor=f"done:{args.count}")


class TestAtlasTool:
    def setup_method(self):
        self.tool = AtlasTool(
            name="dummy",
            description="A dummy tool",
            requires_approval=False,
            fn=_dummy_fn,
            args_model=_DummyArgs,
        )

    def test_spec(self):
        spec = self.tool.spec()
        assert spec.name == "dummy"
        assert "text" in json.dumps(spec.args_schema)

    def test_preview_dict(self):
        pretty, sha = self.tool.preview({"text": "hello", "count": 5})
        assert '"count": 5' in pretty
        assert len(sha) == 12

    def test_preview_model(self):
        args = _DummyArgs(text="hi", count=2)
        pretty, sha = self.tool.preview(args)
        assert '"text": "hi"' in pretty
        assert len(sha) == 12

    def test_preview_deterministic(self):
        _, sha1 = self.tool.preview({"text": "a", "count": 1})
        _, sha2 = self.tool.preview({"text": "a", "count": 1})
        assert sha1 == sha2

    @pytest.mark.asyncio
    async def test_invoke_dict(self):
        result = await self.tool.invoke({"text": "hello"})
        assert result.ok is True
        assert result.anchor == "done:1"

    @pytest.mark.asyncio
    async def test_invoke_model(self):
        result = await self.tool.invoke(_DummyArgs(text="hi", count=3))
        assert result.ok is True
        assert result.anchor == "done:3"

    @pytest.mark.asyncio
    async def test_invoke_bad_args(self):
        result = await self.tool.invoke({"count": "not_int"})
        assert result.ok is False
        assert "validation" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invoke_exception_in_fn(self):
        async def _exploding(args: _DummyArgs) -> ToolResult:
            raise RuntimeError("boom")

        tool = AtlasTool(
            name="boom",
            description="explodes",
            requires_approval=False,
            fn=_exploding,
            args_model=_DummyArgs,
        )
        result = await tool.invoke({"text": "x"})
        assert result.ok is False
        assert "RuntimeError" in result.error


# ── Registry ────────────────────────────────────────────────────────────────


class TestRegistry:
    def setup_method(self):
        self._backup = dict(REGISTRY._tools)

    def teardown_method(self):
        REGISTRY._tools.clear()
        REGISTRY._tools.update(self._backup)

    def test_starter_tools_registered(self):
        names = {s.name for s in REGISTRY.list_tools()}
        assert "create_github_issue" in names
        assert "create_inbox_file" in names

    def test_register_and_get(self):
        tool = AtlasTool(
            name="test_reg",
            description="test",
            requires_approval=False,
            fn=_dummy_fn,
            args_model=_DummyArgs,
        )
        REGISTRY.register(tool)
        assert REGISTRY.get("test_reg") is tool

    def test_get_missing(self):
        assert REGISTRY.get("nonexistent_tool_xyz") is None

    @pytest.mark.asyncio
    async def test_invoke_unknown_tool(self):
        result = await REGISTRY.invoke("no_such_tool", {})
        assert result.ok is False
        assert "unknown tool" in result.error

    def test_clear(self):
        REGISTRY.register(
            AtlasTool(
                name="clearme",
                description="",
                requires_approval=False,
                fn=_dummy_fn,
                args_model=_DummyArgs,
            )
        )
        REGISTRY.clear()
        assert REGISTRY.list_tools() == []


# ── @atlas_tool decorator ──────────────────────────────────────────────────


class _DecTestArgs(BaseModel):
    val: int


class _DecTooManyArgs(BaseModel):
    x: int


class TestDecorator:
    def setup_method(self):
        self._backup = dict(REGISTRY._tools)

    def teardown_method(self):
        REGISTRY._tools.clear()
        REGISTRY._tools.update(self._backup)

    def test_decorator_registers(self):
        @atlas_tool(name="dec_test", description="test decorator")
        async def _fn(args: _DecTestArgs) -> ToolResult:
            return ToolResult.success()

        assert REGISTRY.get("dec_test") is not None

    def test_decorator_rejects_sync_fn(self):
        with pytest.raises(TypeError):

            @atlas_tool(name="sync_bad", description="sync")
            def _fn(args: _DecTestArgs) -> ToolResult:  # type: ignore[return-type]
                pass

    def test_decorator_rejects_no_args(self):
        with pytest.raises(TypeError, match="exactly one"):

            @atlas_tool(name="noargs", description="noargs")
            async def _fn() -> ToolResult:
                return ToolResult.success()

    def test_decorator_rejects_non_basemodel_arg(self):
        with pytest.raises(TypeError, match="BaseModel subclass"):

            @atlas_tool(name="badarg", description="badarg")
            async def _fn(args: str) -> ToolResult:
                return ToolResult.success()

    def test_decorator_rejects_too_many_args(self):
        with pytest.raises(TypeError, match="exactly one"):

            @atlas_tool(name="toomany", description="toomany")
            async def _fn(args: _DecTooManyArgs, extra: str) -> ToolResult:
                return ToolResult.success()


# ── compute_payload_sha12 ──────────────────────────────────────────────────


class TestComputePayloadSha12:
    def test_deterministic(self):
        p = {"a": 1, "b": "hello"}
        assert compute_payload_sha12(p) == compute_payload_sha12(p)

    def test_length_12(self):
        assert len(compute_payload_sha12({"x": 1})) == 12

    def test_key_order_irrelevant(self):
        assert compute_payload_sha12({"a": 1, "b": 2}) == compute_payload_sha12({"b": 2, "a": 1})

    def test_different_payloads_differ(self):
        assert compute_payload_sha12({"a": 1}) != compute_payload_sha12({"a": 2})

    def test_unicode_preserved(self):
        sha = compute_payload_sha12({"text": "Баку əğış"})
        assert len(sha) == 12


# ── extract_action_payload ──────────────────────────────────────────────────


class TestExtractActionPayload:
    def test_action_payload_dict(self):
        p = {"action_payload": {"key": "val"}}
        assert extract_action_payload(p) == {"key": "val"}

    def test_tool_args_fallback(self):
        p = {"tool_name": "my_tool", "tool_args": {"x": 1}}
        result = extract_action_payload(p)
        assert result == {"tool": "my_tool", "args": {"x": 1}}

    def test_tool_args_missing_name(self):
        p = {"tool_args": {"x": 1}}
        result = extract_action_payload(p)
        assert result["tool"] == "?"

    def test_title_content_fallback(self):
        p = {"title": "Hello", "content": "World"}
        result = extract_action_payload(p)
        assert result == {"title": "Hello", "content": "World"}

    def test_content_truncated_at_1000(self):
        p = {"title": "T", "content": "x" * 2000}
        result = extract_action_payload(p)
        assert len(result["content"]) == 1000

    def test_empty_proposal(self):
        result = extract_action_payload({})
        assert result == {"title": "", "content": ""}

    def test_action_payload_takes_priority_over_tool_args(self):
        p = {"action_payload": {"a": 1}, "tool_args": {"b": 2}}
        assert extract_action_payload(p) == {"a": 1}

    def test_action_payload_non_dict_ignored(self):
        p = {"action_payload": "string", "title": "T"}
        result = extract_action_payload(p)
        assert result == {"title": "T", "content": ""}

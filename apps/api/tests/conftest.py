"""Pytest fixtures for Volaura API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.middleware.rate_limit import limiter
from app.services.assessment.helpers import clear_question_cache


@pytest.fixture(autouse=True)
def reset_question_cache():
    """Clear question cache before each test — prevents cross-test mock pollution."""
    clear_question_cache()
    yield


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """Disable rate limiter in tests — prevents cross-test rate limit exhaustion."""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
async def client():
    """Async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

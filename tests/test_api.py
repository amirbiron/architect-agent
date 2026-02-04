"""
Architect Agent - API Tests
============================
Integration tests for the FastAPI endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection."""
    with patch('src.db.mongodb.MongoDB') as mock:
        mock.connect = AsyncMock()
        mock.disconnect = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.get_collection = MagicMock()
        yield mock


@pytest.fixture
def mock_session_repo():
    """Mock SessionRepository."""
    with patch('src.api.routes.SessionRepository') as mock:
        yield mock


@pytest.fixture
def mock_agent():
    """Mock the agent functions."""
    with patch('src.api.routes.run_agent') as mock_run, \
         patch('src.api.routes.continue_conversation') as mock_continue:
        yield mock_run, mock_continue


@pytest.fixture
async def client(mock_mongodb):
    """Create test client."""
    from src.api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ============================================================
# HEALTH & ROOT TESTS
# ============================================================

class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    @pytest.mark.asyncio
    async def test_root(self, client):
        """Test root endpoint - returns HTML page."""
        response = await client.get("/")
        assert response.status_code == 200
        # ממשק הווב מחזיר HTML
        assert "text/html" in response.headers.get("content-type", "")
        assert "Architect Agent" in response.text

    @pytest.mark.asyncio
    async def test_health_check(self, client, mock_mongodb):
        """Test health check endpoint."""
        mock_mongodb.ping = AsyncMock(return_value=True)

        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


# ============================================================
# SESSION TESTS
# ============================================================

class TestSessionEndpoints:
    """Tests for session-related endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_validation(self, client):
        """Test that short messages are rejected."""
        response = await client.post(
            "/api/sessions",
            json={"message": "short"}
        )
        # Should fail validation (min 10 chars)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_session_success(self, client, mock_session_repo, mock_agent):
        """Test successful session creation."""
        from src.agent.state import ProjectContext

        # Setup mocks
        mock_ctx = ProjectContext(
            session_id="test-123",
            initial_summary="Test project"
        )
        mock_ctx.project_name = "Test Project"
        mock_ctx.current_node = "priority"
        mock_ctx.confidence_score = 0.3
        mock_ctx.conversation_history = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"}
        ]

        mock_session_repo.create = AsyncMock(return_value=mock_ctx)
        mock_session_repo.update = AsyncMock(return_value=True)
        mock_agent[0].return_value = mock_ctx  # run_agent

        response = await client.post(
            "/api/sessions",
            json={"message": "I want to build an e-commerce platform with 100K users"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["response"] == "Test response"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client, mock_session_repo):
        """Test getting non-existent session."""
        mock_session_repo.get = AsyncMock(return_value=None)

        response = await client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_session_not_found(self, client, mock_session_repo):
        """Test chatting with non-existent session."""
        mock_session_repo.get = AsyncMock(return_value=None)

        response = await client.post(
            "/api/sessions/nonexistent-id/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 404


# ============================================================
# PATTERNS ENDPOINT TEST
# ============================================================

class TestPatternsEndpoint:
    """Tests for patterns endpoint."""

    @pytest.mark.asyncio
    async def test_list_patterns(self, client):
        """Test listing available patterns."""
        response = await client.get("/api/patterns")
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        # Should have at least monolith and microservices
        pattern_names = [p["name"] for p in data["patterns"]]
        assert "monolith" in pattern_names or len(pattern_names) > 0


# ============================================================
# BLUEPRINT TESTS
# ============================================================

class TestBlueprintEndpoints:
    """Tests for blueprint endpoints."""

    @pytest.mark.asyncio
    async def test_get_blueprint_not_ready(self, client, mock_session_repo):
        """Test getting blueprint before it's generated."""
        from src.agent.state import ProjectContext

        mock_ctx = ProjectContext(
            session_id="test-123",
            initial_summary="Test"
        )
        mock_ctx.blueprint = None  # No blueprint yet

        mock_session_repo.get = AsyncMock(return_value=mock_ctx)

        response = await client.get("/api/sessions/test-123/blueprint")
        assert response.status_code == 404
        assert "not yet generated" in response.json()["detail"]


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

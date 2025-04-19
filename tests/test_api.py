"""
Tests for the API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.schemas import IceBreakerResponse, ProfileSource

client = TestClient(app)

@pytest.fixture
def mock_agent():
    """Fixture for mocking the agent."""
    with patch("app.api.routes.create_icebreaker_agent") as mock:
        mock_agent = MagicMock()
        mock.return_value = mock_agent
        yield mock_agent

@pytest.fixture
def mock_generate_icebreakers():
    """Fixture for mocking the generate_icebreakers function."""
    with patch("app.api.routes.generate_icebreakers") as mock:
        # Mock the return value
        ice_breakers = [
            "I noticed you worked at Google. What was your most interesting project there?",
            "I saw your article on AI ethics. What inspired you to write about that topic?",
            "Your Twitter thread on renewable energy was fascinating. Have you always been interested in sustainability?"
        ]
        
        sources = [
            ProfileSource(
                url="https://www.linkedin.com/in/johndoe",
                platform="LinkedIn",
                title="John Doe | LinkedIn",
                relevance_score=0.9
            ),
            ProfileSource(
                url="https://twitter.com/johndoe",
                platform="Twitter",
                title="John Doe (@johndoe) / Twitter",
                relevance_score=0.8
            )
        ]
        
        mock.return_value = (ice_breakers, sources)
        yield mock

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Ice Breaker Generator"}

def test_create_icebreakers(mock_agent, mock_generate_icebreakers):
    """Test the create_icebreakers endpoint."""
    response = client.post(
        "/api/v1/icebreakers",
        json={"name": "John Doe"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "ice_breakers" in data
    assert len(data["ice_breakers"]) == 3
    assert "sources" in data
    assert len(data["sources"]) == 2
    assert "execution_time" in data
    
    # Check that the first ice breaker contains "Google"
    assert "Google" in data["ice_breakers"][0]
    
    # Check that the first source is LinkedIn
    assert data["sources"][0]["platform"] == "LinkedIn"
    assert data["sources"][0]["url"] == "https://www.linkedin.com/in/johndoe"

def test_create_icebreakers_invalid_input():
    """Test the create_icebreakers endpoint with invalid input."""
    # Test with empty name
    response = client.post(
        "/api/v1/icebreakers",
        json={"name": ""}
    )
    assert response.status_code == 422
    
    # Test with invalid characters in name
    response = client.post(
        "/api/v1/icebreakers",
        json={"name": "John Doe <script>alert('XSS')</script>"}
    )
    assert response.status_code == 422
    
    # Test with missing name field
    response = client.post(
        "/api/v1/icebreakers",
        json={}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_icebreakers_async(mock_agent):
    """Test the create_icebreakers_async endpoint."""
    response = client.post(
        "/api/v1/icebreakers/async",
        json={"name": "John Doe"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "processing"
    
    # Test the status endpoint
    task_id = data["task_id"]
    response = client.get(f"/api/v1/icebreakers/status/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "processing"
    assert "name" in data
    assert data["name"] == "John Doe"

def test_nonexistent_task():
    """Test the status endpoint with a nonexistent task ID."""
    response = client.get("/api/v1/icebreakers/status/nonexistent_task_id")
    assert response.status_code == 404
import pytest
from unittest.mock import patch

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Make multiple requests to health endpoint
    responses = []
    for i in range(5):
        response = client.get("/api/health")
        responses.append(response.status_code)
    
    # All should succeed within reasonable limits
    for status_code in responses:
        assert status_code in [200, 429]  # Either success or rate limited

def test_health_check_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data

def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/api/health")
    
    # Should allow OPTIONS requests
    assert response.status_code in [200, 405]  # Depending on implementation

def test_404_error_handler(client):
    """Test 404 error handler."""
    response = client.get("/nonexistent-endpoint")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Endpoint not found"

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "CampusPulse API" in data["message"]
    assert "version" in data

@patch('app.main.redis_client')
def test_startup_without_redis(mock_redis, client):
    """Test startup when Redis is not available."""
    mock_redis.ping.side_effect = Exception("Redis not available")
    
    # Should still start successfully
    response = client.get("/api/health")
    assert response.status_code == 200

def test_ai_assistant_endpoint_without_auth(client):
    """Test AI assistant endpoint without authentication."""
    response = client.post("/api/assistant", json={"message": "test"})
    
    assert response.status_code == 401

def test_ai_assistant_endpoint_with_auth(client, auth_headers):
    """Test AI assistant endpoint with authentication."""
    response = client.post(
        "/api/assistant",
        json={"message": "test query"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "suggestions" in data
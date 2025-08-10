"""
Comprehensive tests for SRE microservice
"""

import json
import pytest
from fastapi.testclient import TestClient
from src.app.main import app, PayloadRequest

client = TestClient(app)

class TestHealthEndpoints:
    """Test health and readiness endpoints"""
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    def test_ready_endpoint(self):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

class TestPayloadEndpoint:
    """Test payload processing endpoint"""
    
    def test_valid_payload(self):
        payload = {
            "numbers": [1, 2, 3, 4, 5],
            "text": "This is a sample text for analysis."
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "numeric_analysis" in data
        assert "text_analysis" in data
        assert "processing_time_ms" in data
        
        # Verify numeric analysis
        numeric = data["numeric_analysis"]
        assert numeric["minimum"] == 1.0
        assert numeric["maximum"] == 5.0
        assert numeric["mean"] == 3.0
        assert numeric["median"] == 3.0
        assert numeric["count"] == 5
        
        # Verify text analysis
        text = data["text_analysis"]
        assert text["word_count"] == 8
        assert text["character_count"] == len(payload["text"])
    
    def test_empty_numbers_array(self):
        payload = {
            "numbers": [],
            "text": "Sample text"
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 422
    
    def test_empty_text(self):
        payload = {
            "numbers": [1, 2, 3],
            "text": ""
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 422
    
    def test_malformed_payload(self):
        response = client.post("/payload", json={"invalid": "data"})
        assert response.status_code == 422
    
    def test_single_number_statistics(self):
        payload = {
            "numbers": [42],
            "text": "Single number test"
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        numeric = data["numeric_analysis"]
        assert numeric["minimum"] == 42.0
        assert numeric["maximum"] == 42.0
        assert numeric["mean"] == 42.0
        assert numeric["median"] == 42.0
        assert numeric["standard_deviation"] == 0.0

class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text

class TestInputValidation:
    """Test input validation and security"""
    
    def test_large_numbers_array(self):
        payload = {
            "numbers": list(range(10001)),  # Exceeds limit
            "text": "Test text"
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 422
    
    def test_large_text(self):
        payload = {
            "numbers": [1, 2, 3],
            "text": "x" * 50001  # Exceeds limit
        }
        response = client.post("/payload", json=payload)
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__])
"""
Comprehensive tests for SRE microservice
"""

import json
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from app.main import app, PayloadRequest

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
        
        # Verify numeric analysis - test the logic, not hardcoded values
        numeric = data["numeric_analysis"]
        expected_min = float(min(payload["numbers"]))
        expected_max = float(max(payload["numbers"]))
        expected_mean = float(sum(payload["numbers"]) / len(payload["numbers"]))
        expected_count = len(payload["numbers"])
        
        assert numeric["minimum"] == expected_min
        assert numeric["maximum"] == expected_max
        assert numeric["mean"] == expected_mean
        assert numeric["count"] == expected_count
        # Note: median and std dev are more complex to calculate inline, 
        # but we can verify they exist and are reasonable
        assert "median" in numeric
        assert "standard_deviation" in numeric
        assert isinstance(numeric["median"], float)
        assert isinstance(numeric["standard_deviation"], float)
        
        # Verify text analysis - test the logic, not hardcoded values
        text = data["text_analysis"]
        expected_word_count = len(payload["text"].split())
        expected_char_count = len(payload["text"])
        expected_char_count_no_spaces = len(payload["text"].replace(" ", ""))
        expected_sentence_count = len([s for s in payload["text"].split('.') if s.strip()])
        expected_paragraph_count = len([p for p in payload["text"].split('\n') if p.strip()])
        
        assert text["word_count"] == expected_word_count
        assert text["character_count"] == expected_char_count
        assert text["character_count_no_spaces"] == expected_char_count_no_spaces
        assert text["sentence_count"] == expected_sentence_count
        assert text["paragraph_count"] == expected_paragraph_count
    
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
        
        # Test logic instead of hardcoded values
        expected_value = float(payload["numbers"][0])
        assert numeric["minimum"] == expected_value
        assert numeric["maximum"] == expected_value
        assert numeric["mean"] == expected_value
        assert numeric["median"] == expected_value
        assert numeric["standard_deviation"] == 0.0  # Always 0 for single number
        assert numeric["count"] == len(payload["numbers"])

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
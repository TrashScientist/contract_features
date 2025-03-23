"""Integration tests for the Contract Feature Engineering API endpoints.

Tests the API endpoints for:
- Root endpoint metadata
- Single application feature calculation
- Batch feature calculation
- Error handling and validation
"""

import sys
import os
import json
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test that root endpoint returns expected API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert all(key in data for key in ["name", "description", "version", "endpoints"])


def test_calculate_features_endpoint():
    """Test feature calculation for a single valid application."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": json.dumps([{
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "01.01.2024",
            "claim_id": "CL001",
            "contract_date": "01.01.2024"
        }])
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["id"] == 1234.0
    assert result["tot_claim_cnt_l180d"] >= 0
    assert isinstance(result["disb_bank_loan_wo_tbc"], (int, float))
    assert isinstance(result["day_sinlastloan"], int)


def test_calculate_features_with_empty_contracts():
    """Test feature calculation for application with no contracts."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": None
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["id"] == 1234.0
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1


def test_batch_calculate_features_endpoint():
    """Test batch feature calculation for multiple applications."""
    test_data = [
        {
            "id": 1234.0,
            "application_date": "2024-01-01T00:00:00",
            "contracts": json.dumps([{
                "contract_id": "1001",
                "bank": "001",
                "summa": 5000,
                "loan_summa": 5000,
                "claim_date": "01.01.2024",
                "claim_id": "CL001",
                "contract_date": "01.01.2024"
            }])
        },
        {
            "id": 5678.0,
            "application_date": "2024-01-02T00:00:00",
            "contracts": None
        }
    ]
    
    response = client.post("/batch-calculate-features", json=test_data)
    assert response.status_code == 200
    
    results = response.json()
    assert len(results) == 2
    assert results[0]["id"] == 1234.0
    assert results[1]["id"] == 5678.0
    
    # Verify default values for empty contracts
    assert results[1]["tot_claim_cnt_l180d"] == -3
    assert results[1]["disb_bank_loan_wo_tbc"] == -1
    assert results[1]["day_sinlastloan"] == -1


def test_invalid_application_data():
    """Test API validation for invalid/incomplete application data."""
    invalid_data = {
        "application_date": "2024-01-01T00:00:00",
        "contracts": None
        # Missing required 'id' field
    }
    
    response = client.post("/calculate-features", json=invalid_data)
    assert response.status_code == 422  # Unprocessable Entity
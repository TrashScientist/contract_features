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

from app.main import app

# Setup test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["API_VERSION"] = "1.0.0"

client = TestClient(app)

def teardown_module(module):
    """Cleanup after tests"""
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]
    if "API_VERSION" in os.environ:
        del os.environ["API_VERSION"]


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


def test_invalid_date_format():
    """Test API handling of invalid date formats."""
    test_data = {
        "id": 1234.0,
        "application_date": "invalid-date",
        "contracts": None
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200  # API handles invalid dates gracefully
    result = response.json()
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1


def test_invalid_contract_data():
    """Test API handling of invalid contract data structure."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": "invalid-json"
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200  # API handles invalid JSON gracefully
    result = response.json()
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1


def test_health_check_endpoint():
    """Test health check endpoint returns correct information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "test"


def test_excluded_banks():
    """Test handling of contracts with excluded banks."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": json.dumps([{
            "contract_id": "1001",
            "bank": "LIZ",  # Excluded bank
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
    assert result["disb_bank_loan_wo_tbc"] == -1  # Should not count excluded bank loans


def test_invalid_loan_amount():
    """Test handling of contracts with invalid loan amounts."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": json.dumps([{
            "contract_id": "1001",
            "bank": "001",
            "summa": "invalid",
            "loan_summa": "invalid",
            "claim_date": "01.01.2024",
            "claim_id": "CL001",
            "contract_date": "01.01.2024"
        }])
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["disb_bank_loan_wo_tbc"] == -1  # Should handle invalid loan amounts


def test_multiple_contracts():
    """Test handling of multiple contracts with different dates."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-02T00:00:00",  
        "contracts": json.dumps([
            {
                "contract_id": "1001",
                "bank": "001",
                "summa": 5000,
                "loan_summa": 5000,
                "claim_date": "01.01.2024",
                "claim_id": "CL001",
                "contract_date": "01.01.2024"
            },
            {
                "contract_id": "1002",
                "bank": "002",
                "summa": 3000,
                "loan_summa": 3000,
                "claim_date": "02.01.2024",
                "claim_id": "CL002",
                "contract_date": "02.01.2024"
            }
        ])
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["tot_claim_cnt_l180d"] == 2  # Both claims should be counted
    assert result["disb_bank_loan_wo_tbc"] == 8000  # Sum of both loans
    assert result["day_sinlastloan"] == 0  # Most recent contract is on application date
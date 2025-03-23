"""Integration tests for the Contract Feature Engineering API endpoints."""

import json
import os
import sys
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

from app.main import app, calculate_features_endpoint, batch_calculate_features
from app.models import ApplicationData

@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI application."""
    return TestClient(app)

def test_root_endpoint(client):
    """Test that root endpoint returns expected API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert all(key in data for key in ["name", "description", "version", "endpoints"])

def test_calculate_features_endpoint(client):
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

def test_calculate_features_with_empty_contracts(client):
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

def test_batch_calculate_features_endpoint(client):
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
    
    assert results[1]["tot_claim_cnt_l180d"] == -3
    assert results[1]["disb_bank_loan_wo_tbc"] == -1
    assert results[1]["day_sinlastloan"] == -1

def test_invalid_application_data(client):
    """Test API validation for invalid/incomplete application data."""
    invalid_data = {
        "application_date": "2024-01-01T00:00:00",
        "contracts": None
    }
    
    response = client.post("/calculate-features", json=invalid_data)
    assert response.status_code == 422

def test_single_application_value_error(client):
    """Test handling of ValueError in single application processing."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": "not a valid json"
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == 1234.0
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1

def test_batch_processing_value_error(client):
    """Test handling of ValueError in batch processing."""
    test_data = [
        {
            "id": 1234.0,
            "application_date": "2024-01-01T00:00:00",
            "contracts": "not a valid json"
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
    assert results[0]["tot_claim_cnt_l180d"] == -3
    assert results[0]["disb_bank_loan_wo_tbc"] == -1
    assert results[0]["day_sinlastloan"] == -1

def test_batch_processing_general_error(client):
    """Test handling of general exceptions in batch processing."""
    test_data = [
        {
            "id": 1234.0,
            "application_date": "2024-01-01T00:00:00",
            "contracts": json.dumps({
                "not": "a list"
            })
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
    assert results[0]["tot_claim_cnt_l180d"] == -3
    assert results[0]["disb_bank_loan_wo_tbc"] == -1
    assert results[0]["day_sinlastloan"] == -1

def test_invalid_json_contracts(client):
    """Test handling of invalid JSON in contracts field."""
    test_data = {
        "id": 1234.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": "invalid json"
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == 1234.0
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1

@patch('app.services.calculate_features')
def test_single_application_specific_value_error(mock_calculate, client):
    """Test specific ValueError handling in single application processing."""
    mock_calculate.side_effect = ValueError("Test value error")
    
    test_data = {
        "id": 9999.0,
        "application_date": "2024-01-01T00:00:00",
        "contracts": json.dumps([{"contract_id": "1001"}])
    }
    
    response = client.post("/calculate-features", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == 9999.0
    assert result["tot_claim_cnt_l180d"] == -3
    assert result["disb_bank_loan_wo_tbc"] == -1
    assert result["day_sinlastloan"] == -1

@patch('app.services.calculate_features')
def test_batch_processing_specific_value_error(mock_calculate, client):
    """Test specific ValueError handling in batch processing."""
    mock_calculate.side_effect = [ValueError("Test value error"), {"id": 5678.0, "tot_claim_cnt_l180d": -3, "disb_bank_loan_wo_tbc": -1, "day_sinlastloan": -1}]
    
    test_data = [
        {
            "id": 9999.0,
            "application_date": "2024-01-01T00:00:00", 
            "contracts": json.dumps([{"contract_id": "1001"}])
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
    assert results[0]["id"] == 9999.0
    assert results[0]["tot_claim_cnt_l180d"] == -3

@patch('app.main.batch_calculate_features')
def test_batch_processing_outer_exception(mock_batch, client):
    """Test outer exception handling in batch processing."""
    mock_batch.side_effect = Exception("Test batch exception")
    
    with patch('app.main.app', client.app):
        response = client.post("/batch-calculate-features", json=[{"id": 1234.0, "application_date": "2024-01-01T00:00:00", "contracts": None}])
    
    assert response.status_code == 200

@patch.dict(os.environ, {"API_VERSION": "", "ENVIRONMENT": ""})
def test_health_check_no_env_vars(client):
    """Test health check with no environment variables."""
    old_version = os.environ.pop("API_VERSION", None)
    old_env = os.environ.pop("ENVIRONMENT", None)
    
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
    finally:
        if old_version is not None:
            os.environ["API_VERSION"] = old_version
        if old_env is not None:
            os.environ["ENVIRONMENT"] = old_env

@pytest.mark.asyncio
async def test_direct_single_application_error():
    """Directly test the error handling in calculate_features_endpoint."""
    app_data = ApplicationData(id=1234.0, application_date="2024-01-01T00:00:00", contracts=None)
    
    with patch('app.services.calculate_features', side_effect=ValueError("Direct test error")):
        result = await calculate_features_endpoint(app_data)
        
    assert result.id == 1234.0
    assert result.tot_claim_cnt_l180d == -3
    assert result.disb_bank_loan_wo_tbc == -1
    assert result.day_sinlastloan == -1

@pytest.mark.asyncio
async def test_direct_batch_processing_error():
    """Directly test the error handling in batch_calculate_features."""
    app_data_list = [
        ApplicationData(id=1234.0, application_date="2024-01-01T00:00:00", contracts=None),
        ApplicationData(id=5678.0, application_date="2024-01-02T00:00:00", contracts=None)
    ]
    
    with patch('app.services.calculate_features', side_effect=ValueError("Inner test error")):
        results = await batch_calculate_features(app_data_list)
        
    assert len(results) == 2
    assert results[0].id == 1234.0
    assert results[0].tot_claim_cnt_l180d == -3
    assert results[0].disb_bank_loan_wo_tbc == -1

    with patch('app.services.calculate_features', side_effect=Exception("Inner general exception")):
        results = await batch_calculate_features(app_data_list)
        
    assert len(results) == 2
    assert results[0].id == 1234.0
    assert results[0].tot_claim_cnt_l180d == -3
    assert results[0].disb_bank_loan_wo_tbc == -1

@pytest.mark.asyncio
async def test_outer_batch_processing_exception():
    """Test the outer exception handling in batch_calculate_features."""
    app_data_list = [
        ApplicationData(id=1234.0, application_date="2024-01-01T00:00:00", contracts=None),
        ApplicationData(id=5678.0, application_date="2024-01-02T00:00:00", contracts=None)
    ]
    
    with patch('app.main.logger') as mock_logger:
        mock_logger.info.side_effect = Exception("Outer test exception")
        results = await batch_calculate_features(app_data_list)
        
    assert len(results) == 2
    for result in results:
        assert result.tot_claim_cnt_l180d == -3
        assert result.disb_bank_loan_wo_tbc == -1
        assert result.day_sinlastloan == -1

@pytest.mark.asyncio
async def test_single_application_specific_exception_paths():
    """Test each specific exception path in calculate_features_endpoint."""
    app_data = ApplicationData(id=1234.0, application_date="2024-01-01T00:00:00", contracts=None)
    
    with patch('app.main.calculate_features') as mock_calculate:
        mock_calculate.side_effect = ValueError("Specific ValueError test")
        result = await calculate_features_endpoint(app_data)
        assert result.id == 1234.0
        assert result.tot_claim_cnt_l180d == -3
        assert result.disb_bank_loan_wo_tbc == -1
        assert result.day_sinlastloan == -1
        
    with patch('app.main.calculate_features') as mock_calculate:
        mock_calculate.side_effect = Exception("Specific Exception test")
        result = await calculate_features_endpoint(app_data)
        assert result.id == 1234.0
        assert result.tot_claim_cnt_l180d == -3
        assert result.disb_bank_loan_wo_tbc == -1
        assert result.day_sinlastloan == -1

@pytest.mark.asyncio
async def test_batch_processing_specific_exception_paths():
    """Test each specific exception path in batch_calculate_features."""
    app_data_list = [
        ApplicationData(id=1234.0, application_date="2024-01-01T00:00:00", contracts=None),
        ApplicationData(id=5678.0, application_date="2024-01-02T00:00:00", contracts=None)
    ]
    
    with patch('app.main.calculate_features') as mock_calculate:
        mock_calculate.side_effect = [ValueError("Specific ValueError in batch"), None]
        results = await batch_calculate_features(app_data_list)
        assert len(results) == 2
        assert results[0].id == 1234.0
        assert results[0].tot_claim_cnt_l180d == -3
        assert results[0].disb_bank_loan_wo_tbc == -1
        assert results[0].day_sinlastloan == -1
        
    with patch('app.main.calculate_features') as mock_calculate:
        mock_calculate.side_effect = [Exception("Specific Exception in batch"), None]
        results = await batch_calculate_features(app_data_list)
        assert len(results) == 2
        assert results[0].id == 1234.0
        assert results[0].tot_claim_cnt_l180d == -3
        assert results[0].disb_bank_loan_wo_tbc == -1
        assert results[0].day_sinlastloan == -1
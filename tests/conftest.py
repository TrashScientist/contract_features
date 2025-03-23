import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from pathlib import Path

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "test_data"

@pytest.fixture
def sample_application_data():
    return {
        "id": "test123",
        "application_date": "2023-01-01",
        "contract_date": "2023-02-01"
    }

@pytest.fixture
def sample_batch_data():
    return [
        {
            "id": "test123",
            "application_date": "2023-01-01",
            "contract_date": "2023-02-01"
        },
        {
            "id": "test456",
            "application_date": "2023-03-01",
            "contract_date": "2023-04-01"
        }
    ]

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["API_VERSION"] = "1.0.0"
    yield
    # Cleanup after tests
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]
    if "API_VERSION" in os.environ:
        del os.environ["API_VERSION"] 
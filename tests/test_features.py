"""Unit tests for feature calculation logic.

Tests the calculation of various features from contract data, including:
- Empty/invalid contract handling
- Recent claims counting
- Disbursed loan calculations 
- Days since last loan
- Error handling for invalid dates and JSON
"""

import json
import pytest
from app.models import ApplicationData
from app.services import calculate_features


def test_empty_contracts():
    """Test feature calculation with empty contracts.
    
    Verifies that default values are returned when no contracts exist.
    """
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=None
    )
    
    features = calculate_features(app_data)
    
    assert features.id == 1234.0
    assert features.tot_claim_cnt_l180d == -3  # Default for no claims
    assert features.disb_bank_loan_wo_tbc == -1  # Default for no loans
    assert features.day_sinlastloan == -1  # Default for no loans


def test_recent_claims():
    """Test counting claims within the last 180 days.
    
    Verifies that only claims within the 180 day window are counted.
    """
    app_date = "2024-01-01T00:00:00"
    recent_claim = {
        "contract_id": "1001",
        "bank": "001", 
        "summa": 5000,
        "loan_summa": 5000,
        "claim_date": "15.07.2023",  # 170 days ago
        "claim_id": "CL001",
        "contract_date": "15.07.2023"
    }
    old_claim = {
        "contract_id": "1002",
        "bank": "002",
        "summa": 3000,
        "loan_summa": 3000,
        "claim_date": "15.06.2023",  # 200 days ago
        "claim_id": "CL002", 
        "contract_date": "15.06.2023"
    }
    
    app_data = ApplicationData(
        id=1234.0,
        application_date=app_date,
        contracts=json.dumps([recent_claim, old_claim])
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 1


def test_disbursed_loans():
    """Test calculation of disbursed loans excluding certain banks.
    
    Verifies that loans from excluded banks (LIZ, LOM, etc) are not counted
    in the total disbursed amount.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "001",  # Normal bank
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "01.01.2023",
            "claim_id": "CL001",
            "contract_date": "01.01.2023"
        },
        {
            "contract_id": "1002", 
            "bank": "LIZ",  # Excluded bank
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "01.02.2023",
            "claim_id": "CL002",
            "contract_date": "01.02.2023"
        },
        {
            "contract_id": "1003",
            "bank": "003",  # Normal bank
            "summa": 2000,
            "loan_summa": 2000,
            "claim_date": "01.03.2023",
            "claim_id": "CL003",
            "contract_date": "01.03.2023"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.disb_bank_loan_wo_tbc == 7000.0  # Sum of banks 001 and 003


def test_days_since_last_loan():
    """Test calculation of days since the last loan.
    
    Verifies that the most recent contract date is used to calculate
    days since last loan.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "01.10.2023",
            "claim_id": "CL001",
            "contract_date": "01.10.2023"  # 92 days before app_date
        },
        {
            "contract_id": "1002",
            "bank": "002", 
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "15.11.2023",
            "claim_id": "CL002",
            "contract_date": "15.11.2023"  # 47 days before app_date
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.day_sinlastloan == 47  # Days since 15.11.2023


def test_invalid_date_formats():
    """Test handling of invalid date formats.
    
    Verifies that the system gracefully handles invalid date strings
    without raising errors.
    """
    contract = {
        "contract_id": "1001",
        "bank": "001",
        "summa": 5000,
        "loan_summa": 5000,
        "claim_date": "invalid-date",  # Invalid format
        "claim_id": "CL001",
        "contract_date": "01.01.2023"  # Valid format
    }
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps([contract])
    )
    
    features = calculate_features(app_data)
    assert features.id == 1234.0


def test_malformed_json():
    """Test handling of malformed JSON.
    
    Verifies that invalid JSON strings are handled gracefully and
    return default values.
    """
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts="This is not valid JSON"
    )
    
    features = calculate_features(app_data)
    assert features.id == 1234.0
    assert features.tot_claim_cnt_l180d == -3  # Default for no claims
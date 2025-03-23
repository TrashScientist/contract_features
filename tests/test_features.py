"""Unit tests for feature calculation logic.

Tests the calculation of various features from contract data, including:
- Empty/invalid contract handling
- Recent claims counting
- Disbursed loan calculations 
- Days since last loan
- Error handling for invalid dates and JSON
"""

import json
from datetime import datetime
import pytest
from app.models import ApplicationData
from app.services import calculate_features, _parse_application_date, _parse_contracts
from app.utils import parse_date


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


def test_multiple_claims_same_day():
    """Test handling of multiple claims on the same day.
    
    Verifies that all claims on the same day are counted correctly.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "15.11.2023",  # Same day as other claim
            "claim_id": "CL001",
            "contract_date": "15.11.2023"
        },
        {
            "contract_id": "1002",
            "bank": "002",
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "15.11.2023",  # Same day as other claim
            "claim_id": "CL002",
            "contract_date": "15.11.2023"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 2  # Both claims should be counted
    assert features.disb_bank_loan_wo_tbc == 8000.0  # Sum of both loans


def test_excluded_banks_comprehensive():
    """Test comprehensive handling of excluded banks.
    
    Verifies handling of all excluded bank types and their combinations.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "LIZ",  # Excluded bank
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "15.11.2023",
            "claim_id": "CL001",
            "contract_date": "15.11.2023"
        },
        {
            "contract_id": "1002",
            "bank": "LOM",  # Excluded bank
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "15.11.2023",
            "claim_id": "CL002",
            "contract_date": "15.11.2023"
        },
        {
            "contract_id": "1003",
            "bank": "001",  # Normal bank
            "summa": 2000,
            "loan_summa": 2000,
            "claim_date": "15.11.2023",
            "claim_id": "CL003",
            "contract_date": "15.11.2023"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.disb_bank_loan_wo_tbc == 2000.0  # Only bank 001 should be counted


def test_edge_case_dates():
    """Test edge cases in date calculations.
    
    Verifies handling of dates at the boundaries of the 180-day window.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "25.07.2023",  # Exactly 180 days ago
            "claim_id": "CL001",
            "contract_date": "25.07.2023"
        },
        {
            "contract_id": "1002",
            "bank": "002",
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "24.07.2023",  # 181 days ago
            "claim_id": "CL002",
            "contract_date": "24.07.2023"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-21T00:00:00",  # Exactly 180 days after first claim
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 1  # Only the first claim should be counted


def test_contract_vs_claim_dates():
    """Test handling of different contract and claim dates.
    
    Verifies that the system correctly handles cases where contract_date
    and claim_date differ.
    """
    contracts = [
        {
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "15.11.2023",
            "claim_id": "CL001",
            "contract_date": "01.11.2023"  # Contract date is earlier
        },
        {
            "contract_id": "1002",
            "bank": "002",
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "01.11.2023",
            "claim_id": "CL002",
            "contract_date": "15.11.2023"  # Contract date is later
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.day_sinlastloan == 47  # Should use the latest contract_date
    assert features.tot_claim_cnt_l180d == 2  # Both claims should be counted


def test_parse_date_formats():
    """Test date parsing with various formats."""
    # Valid date
    assert parse_date("01.12.2023") == datetime(2023, 12, 1)
    
    # Empty string
    assert parse_date("") is None
    
    # Invalid format
    assert parse_date("2023-12-01") is None
    
    # Invalid values
    assert parse_date("32.13.2023") is None
    
    # Wrong number of parts
    assert parse_date("01.2023") is None


def test_parse_application_date():
    """Test application date parsing with various formats."""
    # ISO format
    assert _parse_application_date("2024-01-01T00:00:00") == datetime(2024, 1, 1)
    
    # With timezone
    assert _parse_application_date("2024-01-01T00:00:00Z") == datetime(2024, 1, 1)
    
    # Invalid format should return current date
    result = _parse_application_date("invalid")
    assert isinstance(result, datetime)
    
    # None should return current date
    result = _parse_application_date(None)
    assert isinstance(result, datetime)


def test_parse_contracts_formats():
    """Test contract parsing with various input formats."""
    # List input
    contracts = [{"id": 1}, {"id": 2}]
    assert _parse_contracts(contracts) == contracts
    
    # JSON string input
    json_str = '[{"id": 1}, {"id": 2}]'
    assert _parse_contracts(json_str) == [{"id": 1}, {"id": 2}]
    
    # Invalid JSON
    assert _parse_contracts("invalid") == []
    
    # None input
    assert _parse_contracts(None) == []
    
    # Empty string
    assert _parse_contracts("") == []


def test_invalid_contract_structures():
    """Test handling of invalid contract structures."""
    contracts = [
        None,  # Invalid contract
        {},    # Empty contract
        {"contract_id": "1001"},  # Missing required fields
        {      # Invalid numeric values but valid dates
            "contract_id": "1001",
            "bank": "001",
            "summa": "invalid",
            "loan_summa": "invalid",
            "claim_date": "01.01.2024",
            "claim_id": "CL001",
            "contract_date": "01.01.2024"
        },
        "not_a_dict"  # Wrong type
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 1  # One valid claim date
    assert features.disb_bank_loan_wo_tbc == -1  # No valid loans
    assert features.day_sinlastloan == 0  # One valid contract date


def test_mixed_valid_invalid_contracts():
    """Test handling of mixed valid and invalid contracts."""
    contracts = [
        {  # Valid contract
            "contract_id": "1001",
            "bank": "001",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "01.01.2024",
            "claim_id": "CL001",
            "contract_date": "01.01.2024"
        },
        None,  # Invalid contract
        {  # Valid contract with invalid loan amount
            "contract_id": "1002",
            "bank": "002",
            "summa": "invalid",
            "loan_summa": "invalid",
            "claim_date": "01.01.2024",
            "claim_id": "CL002",
            "contract_date": "01.01.2024"
        },
        {  # Valid contract
            "contract_id": "1003",
            "bank": "003",
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "01.01.2024",
            "claim_id": "CL003",
            "contract_date": "01.01.2024"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 3  # All valid claim dates count
    assert features.disb_bank_loan_wo_tbc == 8000.0  # Sum of valid loan amounts
    assert features.day_sinlastloan == 0  # Most recent valid contract date


def test_all_excluded_banks():
    """Test case where all contracts are from excluded banks."""
    contracts = [
        {
            "contract_id": "1001",
            "bank": "LIZ",
            "summa": 5000,
            "loan_summa": 5000,
            "claim_date": "01.01.2024",
            "claim_id": "CL001",
            "contract_date": "01.01.2024"
        },
        {
            "contract_id": "1002",
            "bank": "LOM",
            "summa": 3000,
            "loan_summa": 3000,
            "claim_date": "01.01.2024",
            "claim_id": "CL002",
            "contract_date": "01.01.2024"
        },
        {
            "contract_id": "1003",
            "bank": "MKO",
            "summa": 2000,
            "loan_summa": 2000,
            "claim_date": "01.01.2024",
            "claim_id": "CL003",
            "contract_date": "01.01.2024"
        }
    ]
    
    app_data = ApplicationData(
        id=1234.0,
        application_date="2024-01-01T00:00:00",
        contracts=json.dumps(contracts)
    )
    
    features = calculate_features(app_data)
    assert features.tot_claim_cnt_l180d == 3  # Claims still count
    assert features.disb_bank_loan_wo_tbc == -1  # No valid bank loans
    assert features.day_sinlastloan == 0  # Contract dates still count
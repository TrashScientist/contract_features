from datetime import datetime, timedelta
import json
from app.models import ApplicationData, FeatureResponse
from app.utils import parse_date


def calculate_features(app_data: ApplicationData) -> FeatureResponse:
    """Calculate features from application data.
    
    Args:
        app_data: Application data containing contracts and metadata
        
    Returns:
        FeatureResponse with calculated features:
        - tot_claim_cnt_l180d: Number of claims in last 180 days (-3 if none)
        - disb_bank_loan_wo_tbc: Sum of disbursed bank loans (-1 if none) 
        - day_sinlastloan: Days since last loan (-1 if none)
    """
    app_date = _parse_application_date(app_data.application_date)
    
    # Default values if no valid contracts data
    features = {
        'tot_claim_cnt_l180d': -3,  # No claims
        'disb_bank_loan_wo_tbc': -1,  # No loans
        'day_sinlastloan': -1  # No loans
    }
    
    contracts = _parse_contracts(app_data.contracts)
    if not contracts:
        return FeatureResponse(id=app_data.id, **features)
        
    # Calculate features from valid contracts
    features.update({
        'tot_claim_cnt_l180d': _calculate_recent_claims(contracts, app_date),
        'disb_bank_loan_wo_tbc': _calculate_disbursed_loans(contracts),
        'day_sinlastloan': _calculate_days_since_last_loan(contracts, app_date)
    })

    return FeatureResponse(id=app_data.id, **features)


def _parse_application_date(date_str: str) -> datetime:
    """Parse application date string to datetime, defaulting to now on error."""
    try:
        # Convert to naive datetime
        date_str = date_str.replace('Z', '+00:00')
        app_date = datetime.fromisoformat(date_str)
        return app_date.replace(tzinfo=None)
    except (ValueError, AttributeError):
        return datetime.now()


def _parse_contracts(contracts_data) -> list:
    """Parse contracts data to list, handling various input formats."""
    if not contracts_data:
        return []
        
    try:
        if isinstance(contracts_data, list):
            return contracts_data
        return json.loads(contracts_data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing contracts JSON: {e}")
        return []


def _calculate_recent_claims(contracts: list, app_date: datetime) -> int:
    """Calculate number of claims in last 180 days."""
    date_180d_before = app_date - timedelta(days=180)
    
    claim_count = sum(
        1 for contract in contracts
        if isinstance(contract, dict)
        and (claim_date := parse_date(contract.get('claim_date', '')))
        and date_180d_before <= claim_date <= app_date
    )
    
    return claim_count if claim_count > 0 else -3


def _calculate_disbursed_loans(contracts: list) -> float:
    """Calculate sum of disbursed bank loans excluding certain banks."""
    excluded_banks = {'LIZ', 'LOM', 'MKO', 'SUG', None}
    loan_sum = 0
    
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
            
        if not (contract.get('contract_date') and 
                contract.get('bank') not in excluded_banks and
                contract.get('loan_summa')):
            continue
            
        try:
            loan_sum += float(contract['loan_summa'])
        except (ValueError, TypeError):
            continue
            
    return loan_sum if loan_sum > 0 else -1


def _calculate_days_since_last_loan(contracts: list, app_date: datetime) -> int:
    """Calculate days since most recent loan."""
    last_loan_date = None
    
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
            
        if not (contract.get('contract_date') and contract.get('summa')):
            continue
            
        contract_date = parse_date(contract['contract_date'])
        if contract_date and (not last_loan_date or contract_date > last_loan_date):
            last_loan_date = contract_date
            
    return (app_date - last_loan_date).days if last_loan_date else -1
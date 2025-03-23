"""Data models for the Contract Feature Engineering API."""

from pydantic import BaseModel, Field
from typing import Optional


class ApplicationData(BaseModel):
    """Model representing an application data request.
    
    Attributes:
        id: Unique identifier for the application
        application_date: ISO format date string of the application
        contracts: Optional JSON string containing contract data
    """
    id: float = Field(..., description="Unique identifier for the application")
    application_date: str = Field(..., description="ISO format date string (e.g. 2024-01-01T00:00:00)")
    contracts: Optional[str] = Field(
        None,
        description="JSON string containing contract data, or null if no contracts"
    )


class FeatureResponse(BaseModel):
    """Model representing calculated features response.
    
    Attributes:
        id: Application ID from the request
        tot_claim_cnt_l180d: Number of claims in last 180 days (-3 if none)
        disb_bank_loan_wo_tbc: Sum of disbursed bank loans (-1 if none)
        day_sinlastloan: Days since last loan (-1 if none)
    """
    id: float = Field(..., description="Application ID from the request")
    tot_claim_cnt_l180d: int = Field(..., description="Number of claims in last 180 days (-3 if none)")
    disb_bank_loan_wo_tbc: float = Field(..., description="Sum of disbursed bank loans (-1 if none)")
    day_sinlastloan: int = Field(..., description="Days since last loan (-1 if none)")
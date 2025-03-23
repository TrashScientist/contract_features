"""Process contract data from CSV files and calculate features.

This script reads contract data from a CSV file, calculates features using the
contract feature engineering service, and outputs the results to a new CSV file.

Example:
    python process_csv.py --input data.csv --output features.csv
"""

import logging
import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from tqdm import tqdm

# Add parent directory to path to enable importing from app package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from app.models import ApplicationData
from app.services import calculate_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_arg_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Process contracts data and calculate features",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data.csv",
        help="Path to input CSV file containing contract data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="contract_features.csv",
        help="Path to output CSV file for calculated features"
    )
    return parser


def validate_files(input_path: str, output_path: str) -> Tuple[bool, Optional[str]]:
    """Validate input and output file paths.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"
        
    if not input_path.endswith('.csv'):
        return False, f"Input file must be CSV format: {input_path}"
        
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        return False, f"Output directory does not exist: {output_dir}"
        
    return True, None


def process_row(row: pd.Series) -> dict:
    """Process a single row of contract data.
    
    Args:
        row: Pandas Series containing row data
        
    Returns:
        Dictionary of calculated features
    """
    try:
        # Handle NaN values in contracts
        contracts = None if pd.isna(row['contracts']) else str(row['contracts'])
        
        app_data = ApplicationData(
            id=row['id'],
            application_date=row['application_date'],
            contracts=contracts
        )
        
        features = calculate_features(app_data)
        return {
            'id': features.id,
            'tot_claim_cnt_l180d': features.tot_claim_cnt_l180d,
            'disb_bank_loan_wo_tbc': features.disb_bank_loan_wo_tbc,
            'day_sinlastloan': features.day_sinlastloan
        }
        
    except Exception as e:
        logger.error(f"Error processing row {row['id']}: {str(e)}")
        return {
            'id': row['id'],
            'tot_claim_cnt_l180d': -3,
            'disb_bank_loan_wo_tbc': -1, 
            'day_sinlastloan': -1
        }


def process_csv_file(input_file: str, output_file: str) -> bool:
    """Process a CSV file and generate output with calculated features.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        
    Returns:
        True if processing successful, False otherwise
    """
    try:
        # Validate files
        is_valid, error = validate_files(input_file, output_file)
        if not is_valid:
            logger.error(error)
            return False
            
        # Read input CSV
        logger.info(f"Reading data from {input_file}")
        df = pd.read_csv(input_file)
        
        logger.info(f"Processing {len(df):,} rows")
        
        # Process rows with progress bar
        results = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
            results.append(process_row(row))
            
        # Create and save output DataFrame
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_file, index=False)
        
        logger.info(f"Successfully processed {len(output_df):,} rows")
        logger.info(f"Results saved to {output_file}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error processing CSV file: {str(e)}")
        return False


if __name__ == "__main__":
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    success = process_csv_file(args.input, args.output)
    sys.exit(0 if success else 1)
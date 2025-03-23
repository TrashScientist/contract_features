from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time
import os
from dotenv import load_dotenv

from app.models import ApplicationData, FeatureResponse
from app.services import calculate_features
from app.logging_config import logger

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Contract Feature Engineering API",
    description="API service for calculating features from contract data",
    version=os.getenv("API_VERSION", "1.0.0"),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.post(
    "/calculate-features",
    response_model=FeatureResponse,
    summary="Calculate features for a single application",
    description="Processes a single application and returns calculated features",
    response_description="Calculated features including claim counts and loan metrics",
    status_code=200,
    tags=["Features"]
)
async def calculate_features_endpoint(app_data: ApplicationData) -> FeatureResponse:
    """
    Calculate features from single application data.
    
    Args:
        app_data (ApplicationData): Application data containing ID and dates
        
    Returns:
        FeatureResponse: Calculated features including claim counts and loan metrics
        
    Raises:
        HTTPException: If feature calculation fails or input validation fails
    """
    try:
        logger.info(f"Processing single application with ID: {app_data.id}")
        result = calculate_features(app_data)
        logger.info(f"Successfully processed application {app_data.id}")
        return result
    except ValueError as e:
        logger.warning(f"Validation error for application {app_data.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing application {app_data.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(
    "/batch-calculate-features", 
    response_model=List[FeatureResponse],
    summary="Calculate features for multiple applications",
    description="Processes multiple applications in batch and returns features for each",
    response_description="List of calculated features for each application",
    status_code=200,
    tags=["Features"]
)
async def batch_calculate_features(app_data_list: List[ApplicationData]) -> List[FeatureResponse]:
    """
    Calculate features for multiple applications in batch.
    
    Args:
        app_data_list (List[ApplicationData]): List of application data
        
    Returns:
        List[FeatureResponse]: List of calculated features for each application
        
    Raises:
        HTTPException: If batch processing fails or input validation fails
    """
    try:
        logger.info(f"Processing batch of {len(app_data_list)} applications")
        results = []
        for app_data in app_data_list:
            try:
                result = calculate_features(app_data)
                results.append(result)
                logger.debug(f"Successfully processed application {app_data.id}")
            except ValueError as e:
                logger.warning(f"Validation error for application {app_data.id}: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid data for application {app_data.id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing application {app_data.id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")
        
        logger.info("Successfully processed all applications in batch")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the API",
    response_description="Health status information",
    status_code=200,
    tags=["System"]
)
async def health_check() -> dict:
    """
    Health check endpoint for monitoring API status.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "version": os.getenv("API_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get(
    "/",
    summary="API Information",
    description="Returns metadata about the API service",
    response_description="API metadata and documentation",
    status_code=200,
    tags=["System"]
)
async def root() -> dict:
    """
    Root endpoint providing API metadata and documentation.
    
    Returns:
        dict: API information including name, description, version and endpoints
    """
    return {
        "name": "Contract Feature Engineering API",
        "description": "API for calculating features from contract data",
        "version": os.getenv("API_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "/calculate-features": "Calculate features for a single application",
            "/batch-calculate-features": "Calculate features for multiple applications",
            "/health": "Health check endpoint",
            "/docs": "OpenAPI documentation",
            "/redoc": "ReDoc documentation"
        }
    }
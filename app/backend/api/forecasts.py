"""
Forecasts API router for AQI forecasting endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional

from ..models.schemas import (
    ForecastResponse, ForecastListResponse
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get forecast service
def get_forecast_service():
    from ..main import forecast_service
    if forecast_service is None:
        raise HTTPException(status_code=503, detail="Forecast service not available")
    return forecast_service

@router.get("/forecasts/latest", response_model=ForecastResponse, tags=["Forecasts"])
async def get_latest_forecast(
    forecast_service = Depends(get_forecast_service)
):
    """
    Get the latest available forecast
    
    Returns the most recent 72-hour AQI forecast with all data points
    and metadata. Data is cached for 10 minutes to improve performance.
    """
    try:
        forecast = forecast_service.get_latest_forecast()
        if forecast is None:
            raise HTTPException(
                status_code=404,
                detail="No forecasts available. Please run the forecasting script first."
            )
        return forecast
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest forecast: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving latest forecast: {str(e)}"
        )

@router.get("/forecasts/{forecast_id}", response_model=ForecastResponse, tags=["Forecasts"])
async def get_forecast_by_id(
    forecast_id: str = Path(..., description="Forecast ID to retrieve"),
    forecast_service = Depends(get_forecast_service)
):
    """
    Get a specific forecast by ID
    
    Retrieves a forecast using its unique identifier.
    The forecast ID is typically derived from the filename.
    """
    try:
        forecast = forecast_service.get_forecast_by_id(forecast_id)
        if forecast is None:
            raise HTTPException(
                status_code=404,
                detail=f"Forecast with ID '{forecast_id}' not found"
            )
        return forecast
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast by ID {forecast_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving forecast: {str(e)}"
        )

@router.get("/forecasts", response_model=ForecastListResponse, tags=["Forecasts"])
async def get_forecast_list(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of forecasts to return"),
    forecast_service = Depends(get_forecast_service)
):
    """
    Get list of available forecasts
    
    Returns a paginated list of available forecasts with metadata.
    Forecasts are sorted by creation time (newest first).
    """
    try:
        forecast_list = forecast_service.get_forecast_list(limit=limit)
        return forecast_list
        
    except Exception as e:
        logger.error(f"Error getting forecast list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving forecast list: {str(e)}"
        )

@router.get("/forecasts/statistics", tags=["Forecasts"])
async def get_forecast_statistics(
    hours_back: int = Query(default=24, ge=1, le=168, description="Hours to look back for statistics"),
    forecast_service = Depends(get_forecast_service)
):
    """
    Get statistics about forecasts in the last N hours
    
    Returns comprehensive statistics about forecast files including
    count, total size, models used, and horizon information.
    """
    try:
        stats = forecast_service.get_forecast_statistics(hours_back=hours_back)
        
        if "error" in stats:
            raise HTTPException(
                status_code=404,
                detail=stats["error"]
            )
        
        return {
            "success": True,
            "message": f"Forecast statistics for last {hours_back} hours",
            "data": stats,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating forecast statistics: {str(e)}"
        )

@router.get("/forecasts/models/info", tags=["Forecasts"])
async def get_forecast_models_info(
    forecast_service = Depends(get_forecast_service)
):
    """
    Get information about available forecasting models
    
    Returns detailed information about each forecasting model including
    type, horizon, advantages, limitations, and descriptions.
    """
    try:
        models_info = forecast_service.get_forecast_models_info()
        
        if "error" in models_info:
            raise HTTPException(
                status_code=500,
                detail=models_info["error"]
            )
        
        return {
            "success": True,
            "message": "Forecast models information retrieved",
            "data": models_info,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast models info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving forecast models information: {str(e)}"
        )

@router.post("/forecasts/cache/clear", tags=["Forecasts"])
async def clear_forecast_cache(
    forecast_service = Depends(get_forecast_service)
):
    """
    Clear the forecast service cache
    
    Forces the forecast service to reload forecast data on the next request.
    Useful for ensuring fresh forecasts after new predictions are generated.
    """
    try:
        forecast_service.clear_cache()
        return {
            "success": True,
            "message": "Forecast cache cleared successfully",
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error clearing forecast cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing forecast cache: {str(e)}"
        )

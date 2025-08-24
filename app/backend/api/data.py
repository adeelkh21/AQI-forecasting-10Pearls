"""
Data API router for AQI and weather data endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from ..models.schemas import (
    CurrentDataResponse, DataSourceStatus, TimeRangeParams
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get data service
def get_data_service():
    from ..main import data_service
    if data_service is None:
        raise HTTPException(status_code=503, detail="Data service not available")
    return data_service

@router.get("/data/current", response_model=CurrentDataResponse, tags=["Data"])
async def get_current_data(
    data_service = Depends(get_data_service)
):
    """
    Get current AQI and weather data
    
    Returns the latest available AQI value, pollutant levels, and weather information.
    Data is cached for 5 minutes to improve performance.
    """
    try:
        current_data = data_service.get_current_data()
        if current_data is None:
            raise HTTPException(
                status_code=404,
                detail="No current data available. Please check if data collection is running."
            )
        return current_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving current data: {str(e)}"
        )

@router.get("/data/sources/status", response_model=list[DataSourceStatus], tags=["Data"])
async def get_data_sources_status(
    data_service = Depends(get_data_service)
):
    """
    Get status of all data sources
    
    Returns the status of merged data, features data, and forecast-ready data files.
    Status includes file age, error counts, and last update information.
    """
    try:
        sources_status = data_service.get_data_sources_status()
        return sources_status
        
    except Exception as e:
        logger.error(f"Error getting data sources status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving data sources status: {str(e)}"
        )

@router.get("/data/summary", tags=["Data"])
async def get_data_summary(
    hours_back: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
    data_service = Depends(get_data_service)
):
    """
    Get data summary for the last N hours
    
    Returns statistical summary of AQI values, pollutant levels, and weather data
    for the specified time period.
    """
    try:
        summary = data_service.get_data_summary(hours_back=hours_back)
        
        if "error" in summary:
            raise HTTPException(
                status_code=404,
                detail=summary["error"]
            )
        
        return {
            "success": True,
            "message": f"Data summary for last {hours_back} hours",
            "data": summary,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating data summary: {str(e)}"
        )

@router.get("/data/forecast/info", tags=["Data"])
async def get_latest_forecast_info(
    data_service = Depends(get_data_service)
):
    """
    Get information about the latest forecast
    
    Returns metadata about the most recent forecast file including
    forecast count, horizon hours, models used, and file size.
    """
    try:
        forecast_info = data_service.get_latest_forecast_info()
        
        if forecast_info is None:
            raise HTTPException(
                status_code=404,
                detail="No forecast information available"
            )
        
        return {
            "success": True,
            "message": "Latest forecast information retrieved",
            "data": forecast_info,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving forecast information: {str(e)}"
        )

@router.post("/data/cache/clear", tags=["Data"])
async def clear_data_cache(
    data_service = Depends(get_data_service)
):
    """
    Clear the data service cache
    
    Forces the data service to reload data on the next request.
    Useful for ensuring fresh data after data updates.
    """
    try:
        data_service.clear_cache()
        return {
            "success": True,
            "message": "Data cache cleared successfully",
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error clearing data cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data cache: {str(e)}"
        )

@router.get("/data/aqi-timeline", tags=["Data"])
async def get_aqi_timeline(
    data_service = Depends(get_data_service)
):
    """
    Get complete AQI timeline for the entire dataset
    
    Returns the complete AQI timeline with EPA-compliant calculations for all historical data.
    This provides context for current AQI values and shows long-term air quality trends.
    """
    try:
        timeline_data = data_service.get_complete_aqi_timeline()
        
        if "error" in timeline_data:
            raise HTTPException(
                status_code=404,
                detail=timeline_data["error"]
            )
        
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AQI timeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving AQI timeline: {str(e)}"
        )

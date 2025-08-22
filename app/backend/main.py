from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from .jobs import create_job, update_step, set_status, get_job
    from .services.collect import collect_data
    from .services.preprocess import preprocess_data
    from .services.forecast import run_forecast, get_latest_forecast, get_forecast_by_id
    from .services.data_access import get_latest_aqi, get_aqi_history, get_latest_weather, get_latest_pollutants
    from .models.schemas import CollectResponse, PreprocessResponse, ForecastResponse, JobStatus
    from .utils.logging import get_logger
except ImportError:
    # Fallback for direct module execution
    from app.backend.jobs import create_job, update_step, set_status, get_job
    from app.backend.services.collect import collect_data
    from app.backend.services.preprocess import preprocess_data
    from app.backend.services.forecast import run_forecast, get_latest_forecast, get_forecast_by_id
    from app.backend.services.data_access import get_latest_aqi, get_aqi_history, get_latest_weather, get_latest_pollutants
    from app.backend.models.schemas import CollectResponse, PreprocessResponse, ForecastResponse, JobStatus
    from app.backend.utils.logging import get_logger

# Configure logging
logger = get_logger('main')

# Create FastAPI app
app = FastAPI(
    title="AQI Forecasting API",
    description="Real-time AQI forecasting system with data collection and preprocessing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    try:
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "type": "internal_error",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as handler_error:
        # Fallback if even the error handler fails
        return JSONResponse(
            status_code=500,
            content={
                "error": "Critical error",
                "message": "System error handler failed",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed system status."""
    try:
        try:
            from .services.data_access import get_data_summary
            from .utils.paths import ROOT, FEATURES_CSV, MERGED_CSV
        except ImportError:
            from app.backend.services.data_access import get_data_summary
            from app.backend.utils.paths import ROOT, FEATURES_CSV, MERGED_CSV
        
        # Get system status
        data_summary = get_data_summary()
        
        # Check critical files
        critical_files = {
            "merged_data": MERGED_CSV.exists(),
            "features_data": FEATURES_CSV.exists(),
            "project_root": ROOT.exists()
        }
        
        # Calculate system health score
        health_score = sum(critical_files.values()) / len(critical_files) * 100
        
        return {
            "status": "healthy" if health_score >= 75 else "degraded" if health_score >= 50 else "unhealthy",
            "health_score": round(health_score, 1),
            "timestamp": datetime.now().isoformat(),
            "critical_files": critical_files,
            "data_summary": data_summary,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": "Health check failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/collect", response_model=CollectResponse)
async def collect_data_endpoint(hours_backfill: int = Query(24, ge=1, le=168)):
    """Collect new data and merge with existing dataset."""
    try:
        logger.info(f"Data collection requested with {hours_backfill} hours backfill")
        
        # Validate input parameters
        if hours_backfill < 1 or hours_backfill > 168:
            raise HTTPException(
                status_code=400, 
                detail="hours_backfill must be between 1 and 168"
            )
        
        # Run data collection
        result = await collect_data(hours_backfill)
        
        if not result.get("collection_success", False):
            error_msg = result.get("error", "Unknown collection error")
            logger.error(f"Data collection failed: {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=f"Data collection failed: {error_msg}"
            )
        
        # Log success with details
        rows_collected = result.get("rows_collected", 0)
        rows_added = result.get("rows_added", 0)
        validation_errors = result.get("validation_errors", [])
        
        if validation_errors:
            logger.warning(f"Collection completed with validation warnings: {validation_errors}")
        
        logger.info(f"Data collection completed: {rows_collected} collected, {rows_added} added")
        
        return {
            "success": True,
            "rows_collected": rows_collected,
            "rows_added": rows_added,
            "last_timestamp": result.get("last_timestamp"),
            "validation_errors": validation_errors,
            "duplicates_removed": result.get("duplicates_removed", 0),
            "message": f"Successfully collected {rows_collected} rows and added {rows_added} new rows"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data collection endpoint failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Data collection failed with unexpected error: {str(e)}"
        )


@app.post("/preprocess", response_model=PreprocessResponse)
async def preprocess_data_endpoint():
    """Run data preprocessing pipeline (Phase2 + Phase3)."""
    try:
        logger.info("Data preprocessing requested")
        
        # Run preprocessing
        result = await preprocess_data()
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown preprocessing error")
            logger.error(f"Data preprocessing failed: {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=f"Data preprocessing failed: {error_msg}"
            )
        
        logger.info("Data preprocessing completed successfully")
        
        return {
            "success": True,
            "phase2_success": result.get("phase2_success", False),
            "phase3_success": result.get("phase3_success", False),
            "artifacts": result.get("artifacts", []),
            "message": "Data preprocessing completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data preprocessing endpoint failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Data preprocessing failed with unexpected error: {str(e)}"
        )


@app.post("/pipeline/collect-and-prep")
async def collect_and_preprocess_pipeline(background_tasks: BackgroundTasks):
    """Run complete data collection and preprocessing pipeline in background."""
    try:
        logger.info("Collect and preprocess pipeline requested")
        
        # Create background job
        job_id = create_job([
            "data_collection",
            "data_merging", 
            "phase2_preprocessing",
            "phase3_feature_selection"
        ])
        
        # Add background task
        background_tasks.add_task(run_collect_prep_pipeline, job_id)
        
        logger.info(f"Pipeline job {job_id} started in background")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Pipeline job started in background",
            "steps": ["data_collection", "data_merging", "phase2_preprocessing", "phase3_feature_selection"]
        }
        
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to start pipeline: {str(e)}"
        )


async def run_collect_prep_pipeline(job_id: str):
    """Run the complete collect and preprocess pipeline."""
    try:
        logger.info(f"Starting pipeline execution for job {job_id}")
        
        # Step 1: Data Collection
        update_step(job_id, "data_collection", "running", "Collecting new data...")
        collect_result = await collect_data()
        
        if not collect_result.get("collection_success", False):
            error_msg = collect_result.get("error", "Collection failed")
            update_step(job_id, "data_collection", "failed", f"Collection failed: {error_msg}")
            set_status(job_id, "failed", f"Data collection failed: {error_msg}")
            return
        
        update_step(job_id, "data_collection", "completed", 
                   f"Collected {collect_result.get('rows_collected', 0)} rows")
        
        # Step 2: Data Merging
        update_step(job_id, "data_merging", "running", "Merging data...")
        rows_added = collect_result.get("rows_added", 0)
        update_step(job_id, "data_merging", "completed", 
                   f"Added {rows_added} new rows to dataset")
        
        # Step 3: Phase2 Preprocessing
        update_step(job_id, "phase2_preprocessing", "running", "Running Phase2 preprocessing...")
        preprocess_result = await preprocess_data()
        
        if not preprocess_result.get("success", False):
            error_msg = preprocess_result.get("error", "Phase2 failed")
            update_step(job_id, "phase2_preprocessing", "failed", f"Phase2 failed: {error_msg}")
            set_status(job_id, "failed", f"Phase2 preprocessing failed: {error_msg}")
            return
        
        update_step(job_id, "phase2_preprocessing", "completed", "Phase2 preprocessing completed")
        
        # Step 4: Phase3 Feature Selection
        update_step(job_id, "phase3_feature_selection", "running", "Running Phase3 feature selection...")
        update_step(job_id, "phase3_feature_selection", "completed", "Phase3 feature selection completed")
        
        # Pipeline completed successfully
        set_status(job_id, "completed", "Pipeline completed successfully")
        logger.info(f"Pipeline job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed for job {job_id}: {e}")
        set_status(job_id, "failed", f"Pipeline failed with unexpected error: {str(e)}")


@app.post("/forecast", response_model=ForecastResponse)
async def forecast_endpoint():
    """Run AQI forecasting for next 72 hours."""
    try:
        logger.info("Forecast execution requested")
        
        # Run forecast
        result = await run_forecast()
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown forecast error")
            logger.error(f"Forecast failed: {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=f"Forecast failed: {error_msg}"
            )
        
        logger.info("Forecast completed successfully")
        
        return {
            "success": True,
            "forecast_id": result.get("metadata", {}).get("forecast_id"),
            "outputs": result.get("outputs", []),
            "metadata": result.get("metadata", {}),
            "message": "Forecast completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast endpoint failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Forecast failed with unexpected error: {str(e)}"
        )


@app.get("/forecast/latest", response_model=ForecastResponse)
async def get_latest_forecast_endpoint():
    """Get the latest forecast."""
    try:
        result = await get_latest_forecast()
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail="No forecast data available. Run a forecast first."
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest forecast: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get latest forecast: {str(e)}"
        )


@app.get("/forecast/{forecast_id}", response_model=ForecastResponse)
async def get_forecast_by_id_endpoint(forecast_id: str):
    """Get a specific forecast by its ID."""
    try:
        # Validate forecast ID format
        if not forecast_id.startswith("forecast_"):
            raise HTTPException(
                status_code=400, 
                detail="Invalid forecast ID format. Must start with 'forecast_'"
            )
        
        result = await get_forecast_by_id(forecast_id)
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Forecast with ID '{forecast_id}' not found"
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get forecast by ID {forecast_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get forecast by ID {forecast_id}: {str(e)}"
        )


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status_endpoint(job_id: str):
    """Get the status of a background job."""
    try:
        job = get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Job with ID '{job_id}' not found"
            )
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get job status: {str(e)}"
        )


@app.get("/aqi/latest")
async def get_latest_aqi_endpoint():
    """Get the latest AQI data."""
    try:
        result = await get_latest_aqi()
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail="No AQI data available. Run data collection first."
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest AQI: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get latest AQI: {str(e)}"
        )


@app.get("/aqi/history")
async def get_aqi_history_endpoint(hours: int = Query(168, ge=1, le=720)):
    """Get historical AQI data for plotting."""
    try:
        # Validate input parameters
        if hours < 1 or hours > 720:
            raise HTTPException(
                status_code=400, 
                detail="hours must be between 1 and 720 (30 days)"
            )
        
        result = await get_aqi_history(hours)
        
        return {
            "hours": hours,
            "data": result,
            "count": len(result),
            "message": f"Retrieved {len(result)} AQI data points for last {hours} hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AQI history: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get AQI history: {str(e)}"
        )


@app.get("/weather/latest")
async def get_latest_weather_endpoint():
    """Get the latest weather data."""
    try:
        result = await get_latest_weather()
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail="No weather data available. Run data collection first."
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest weather: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get latest weather: {str(e)}"
        )


@app.get("/pollutants/latest")
async def get_latest_pollutants_endpoint():
    """Get the latest pollutant data."""
    try:
        result = await get_latest_pollutants()
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail="No pollutant data available. Run data collection first."
            )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest pollutants: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get latest pollutants: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    try:
        from .utils.paths import ENV_CONFIG
    except ImportError:
        from app.backend.utils.paths import ENV_CONFIG
    uvicorn.run(
        app, 
        host=ENV_CONFIG["API_HOST"], 
        port=ENV_CONFIG["API_PORT"]
    )



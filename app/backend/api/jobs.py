"""
Jobs API router for background job execution endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Body
from typing import Optional

from ..models.schemas import (
    JobRequest, JobResponse, JobStatusResponse, JobListResponse, JobStatus
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get job service
def get_job_service():
    from ..main import job_service
    if job_service is None:
        raise HTTPException(status_code=503, detail="Job service not available")
    return job_service

@router.post("/jobs", response_model=JobResponse, tags=["Jobs"])
async def create_job(
    job_request: JobRequest = Body(..., description="Job creation request"),
    job_service = Depends(get_job_service)
):
    """
    Create a new background job
    
    Creates and queues a new job for execution. Supported job types:
    - data_collection: Runs the data collection script
    - data_processing: Runs the data preprocessing pipeline
    - forecasting: Runs the AQI forecasting script
    
    Jobs are executed asynchronously with priority-based queuing.
    """
    try:
        job_response = await job_service.create_job(job_request)
        return job_response
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating job: {str(e)}"
        )

@router.get("/jobs/statistics", tags=["Jobs"])
async def get_job_statistics(
    job_service = Depends(get_job_service)
):
    """
    Get job service statistics
    
    Returns comprehensive statistics about the job service including
    total jobs, completed jobs, failed jobs, and current queue status.
    """
    try:
        stats = job_service.get_service_statistics()
        return {
            "success": True,
            "message": "Job service statistics retrieved",
            "data": stats,
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error getting job statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job statistics: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(
    job_id: str = Path(..., description="Job ID to check"),
    job_service = Depends(get_job_service)
):
    """
    Get the status of a specific job
    
    Returns detailed information about a job including its current status,
    progress, execution time, and any error messages.
    """
    try:
        job_status = await job_service.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{job_id}' not found"
            )
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job status: {str(e)}"
        )

@router.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
async def get_job_list(
    status: Optional[JobStatus] = Query(None, description="Filter jobs by status"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of jobs to return"),
    job_service = Depends(get_job_service)
):
    """
    Get list of jobs with optional filtering
    
    Returns a list of jobs with optional status filtering.
    Jobs are sorted by creation time (newest first).
    """
    try:
        job_list = await job_service.get_job_list(status_filter=status, limit=limit)
        return job_list
        
    except Exception as e:
        logger.error(f"Error getting job list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job list: {str(e)}"
        )

@router.delete("/jobs/{job_id}", tags=["Jobs"])
async def cancel_job(
    job_id: str = Path(..., description="Job ID to cancel"),
    job_service = Depends(get_job_service)
):
    """
    Cancel a running or pending job
    
    Cancels a job if it's currently running or waiting in the queue.
    Completed or failed jobs cannot be cancelled.
    """
    try:
        success = await job_service.cancel_job(job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Job '{job_id}' cannot be cancelled (may be completed or failed)"
            )
        
        return {
            "success": True,
            "message": f"Job '{job_id}' cancelled successfully",
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling job: {str(e)}"
        )

@router.post("/jobs/quick/collect", tags=["Jobs"])
async def quick_data_collection(
    job_service = Depends(get_job_service)
):
    """
    Quick data collection job
    
    Creates a high-priority data collection job with default settings.
    This is a convenience endpoint for quick data updates.
    """
    try:
        from ..models.schemas import JobType
        
        job_request = JobRequest(
            job_type=JobType.DATA_COLLECTION,
            priority=10,  # High priority
            timeout=1800  # 30 minutes
        )
        
        job_response = await job_service.create_job(job_request)
        return {
            "success": True,
            "message": "Quick data collection job created",
            "job": job_response,
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error creating quick data collection job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating quick data collection job: {str(e)}"
        )

@router.post("/jobs/quick/process", tags=["Jobs"])
async def quick_data_processing(
    job_service = Depends(get_job_service)
):
    """
    Quick data processing job
    
    Creates a high-priority data processing job with default settings.
    This is a convenience endpoint for quick data preprocessing.
    """
    try:
        from ..models.schemas import JobType
        
        job_request = JobRequest(
            job_type=JobType.DATA_PROCESSING,
            priority=10,  # High priority
            timeout=3600  # 1 hour
        )
        
        job_response = await job_service.create_job(job_request)
        return {
            "success": True,
            "message": "Quick data processing job created",
            "job": job_response,
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error creating quick data processing job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating quick data processing job: {str(e)}"
        )

@router.post("/jobs/quick/forecast", tags=["Jobs"])
async def quick_forecasting(
    job_service = Depends(get_job_service)
):
    """
    Quick forecasting job
    
    Creates a high-priority forecasting job with default settings.
    This is a convenience endpoint for quick AQI predictions.
    """
    try:
        from ..models.schemas import JobType
        
        job_request = JobRequest(
            job_type=JobType.FORECASTING,
            priority=10,  # High priority
            timeout=1800  # 30 minutes
        )
        
        job_response = await job_service.create_job(job_request)
        return {
            "success": True,
            "message": "Quick forecasting job created",
            "job": job_response,
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error creating quick forecasting job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating quick forecasting job: {str(e)}"
        )

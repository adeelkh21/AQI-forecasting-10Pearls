import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .utils.logging import get_logger

logger = get_logger('jobs')

# In-memory job storage
jobs: Dict[str, Dict[str, Any]] = {}


def create_job(steps: List[str]) -> str:
    """Create a new background job."""
    job_id = str(uuid.uuid4())
    
    job = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "steps": {step: {"status": "pending", "message": "", "started_at": None, "completed_at": None} for step in steps},
        "error": None,
        "meta": {}
    }
    
    jobs[job_id] = job
    logger.info(f"Created job {job_id} with {len(steps)} steps: {steps}")
    
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a job by ID."""
    return jobs.get(job_id)


def update_step(job_id: str, step: str, status: str, message: str = ""):
    """Update the status of a specific step in a job."""
    if job_id not in jobs:
        logger.warning(f"Attempted to update step for non-existent job: {job_id}")
        return
    
    job = jobs[job_id]
    if step not in job["steps"]:
        logger.warning(f"Attempted to update non-existent step '{step}' in job {job_id}")
        return
    
    now = datetime.now().isoformat()
    
    if status == "running" and job["steps"][step]["started_at"] is None:
        job["steps"][step]["started_at"] = now
    elif status in ["completed", "failed"] and job["steps"][step]["completed_at"] is None:
        job["steps"][step]["completed_at"] = now
    
    job["steps"][step]["status"] = status
    job["steps"][step]["message"] = message
    job["updated_at"] = now
    
    logger.info(f"Job {job_id} step '{step}' updated to {status}: {message}")


def set_status(job_id: str, status: str, message: str = ""):
    """Set the overall status of a job."""
    if job_id not in jobs:
        logger.warning(f"Attempted to set status for non-existent job: {job_id}")
        return
    
    job = jobs[job_id]
    job["status"] = status
    job["updated_at"] = datetime.now().isoformat()
    
    if message:
        job["error"] = message if status == "failed" else None
    
    logger.info(f"Job {job_id} status set to {status}: {message}")


def get_job_summary(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a summary of job progress."""
    job = get_job(job_id)
    if not job:
        return None
    
    steps = job["steps"]
    total_steps = len(steps)
    completed_steps = sum(1 for step in steps.values() if step["status"] == "completed")
    failed_steps = sum(1 for step in steps.values() if step["status"] == "failed")
    running_steps = sum(1 for step in steps.values() if step["status"] == "running")
    
    progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    return {
        "id": job_id,
        "status": job["status"],
        "progress": round(progress, 1),
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "failed_steps": failed_steps,
        "running_steps": running_steps,
        "created_at": job["created_at"],
        "updated_at": job["updated_at"]
    }


def cleanup_old_jobs(max_age_hours: int = 24):
    """Clean up old completed/failed jobs to prevent memory leaks."""
    try:
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        jobs_to_remove = []
        
        for job_id, job in jobs.items():
            try:
                job_time = datetime.fromisoformat(job["created_at"]).timestamp()
                if job_time < cutoff_time and job["status"] in ["completed", "failed"]:
                    jobs_to_remove.append(job_id)
            except Exception as e:
                logger.warning(f"Failed to parse job time for {job_id}: {e}")
                continue
        
        for job_id in jobs_to_remove:
            del jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")


def get_all_jobs() -> List[Dict[str, Any]]:
    """Get all jobs (for monitoring purposes)."""
    return [
        {
            "id": job_id,
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "steps_count": len(job["steps"])
        }
        for job_id, job in jobs.items()
    ]



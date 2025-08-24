"""
Job service for managing background job execution
"""
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.runner import ScriptRunner, ExecutionResult, format_execution_result
from ..utils.logging import get_logger, log_job_start, log_job_complete
from ..models.schemas import (
    JobStatus, JobType, JobRequest, JobResponse, JobStatusResponse,
    JobListResponse
)

logger = get_logger(__name__)

@dataclass
class Job:
    """Internal job representation"""
    job_id: str
    job_type: JobType
    status: JobStatus
    parameters: Optional[Dict[str, Any]]
    priority: int
    timeout: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_result: Optional[ExecutionResult] = None
    progress: float = 0.0
    error_message: Optional[str] = None

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15

class JobService:
    """Service for managing background job execution"""
    
    def __init__(self, max_concurrent_jobs: int = 3):
        self.logger = logger
        self.max_concurrent_jobs = max_concurrent_jobs
        self.script_runner = ScriptRunner()
        
        # Job storage
        self._jobs: Dict[str, Job] = {}
        self._job_queue: List[str] = []
        self._running_jobs: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self._total_jobs = 0
        self._completed_jobs = 0
        self._failed_jobs = 0
        
        # Background task for job processing
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the job service"""
        try:
            self.logger.info("Starting job service...")
            self._queue_processor_task = asyncio.create_task(self._process_job_queue())
            self.logger.info("Job service started successfully")
        except Exception as e:
            self.logger.error(f"Error starting job service: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the job service"""
        try:
            self.logger.info("Stopping job service...")
            self._shutdown_event.set()
            
            # Cancel all running jobs
            for task in self._running_jobs.values():
                task.cancel()
            
            # Wait for queue processor to stop
            if self._queue_processor_task:
                self._queue_processor_task.cancel()
                try:
                    await self._queue_processor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Job service stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping job service: {str(e)}")
    
    async def create_job(self, job_request: JobRequest) -> JobResponse:
        """Create a new job"""
        try:
            # Generate unique job ID
            job_id = f"job_{uuid.uuid4().hex[:8]}"
            
            # Create job object
            job = Job(
                job_id=job_id,
                job_type=job_request.job_type,
                status=JobStatus.PENDING,
                parameters=job_request.parameters,
                priority=job_request.priority,
                timeout=job_request.timeout or self._get_default_timeout(job_request.job_type),
                created_at=datetime.utcnow()
            )
            
            # Store job
            self._jobs[job_id] = job
            self._total_jobs += 1
            
            # Add to queue
            self._add_to_queue(job_id)
            
            # Log job creation
            log_job_start(self.logger, job_id, job_request.job_type.value)
            
            # Estimate duration
            estimated_duration = self._estimate_job_duration(job_request.job_type)
            
            return JobResponse(
                success=True,
                message="Job created successfully",
                job_id=job_id,
                job_type=job_request.job_type,
                status=JobStatus.PENDING,
                estimated_duration=estimated_duration
            )
            
        except Exception as e:
            self.logger.error(f"Error creating job: {str(e)}")
            return JobResponse(
                success=False,
                message=f"Error creating job: {str(e)}",
                job_id="",
                job_type=job_request.job_type,
                status=JobStatus.FAILED
            )
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Get the status of a specific job"""
        try:
            if job_id not in self._jobs:
                return None
            
            job = self._jobs[job_id]
            
            # Calculate execution time if completed
            execution_time = None
            if job.completed_at and job.started_at:
                execution_time = (job.completed_at - job.started_at).total_seconds()
            
            # Format execution result
            stdout = ""
            stderr = ""
            if job.execution_result:
                stdout = job.execution_result.stdout
                stderr = job.execution_result.stderr
            
            return JobStatusResponse(
                success=True,
                message="Job status retrieved successfully",
                job_id=job.job_id,
                job_type=job.job_type,
                status=job.status,
                progress=job.progress,
                start_time=job.started_at,
                end_time=job.completed_at,
                execution_time=execution_time,
                stdout=stdout,
                stderr=stderr,
                error_message=job.error_message
            )
            
        except Exception as e:
            self.logger.error(f"Error getting job status for {job_id}: {str(e)}")
            return None
    
    async def get_job_list(self, status_filter: Optional[JobStatus] = None, limit: int = 50) -> JobListResponse:
        """Get list of jobs with optional filtering"""
        try:
            # Filter jobs
            filtered_jobs = []
            for job in self._jobs.values():
                if status_filter is None or job.status == status_filter:
                    filtered_jobs.append(job)
            
            # Sort by creation time (newest first)
            filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)
            
            # Apply limit
            filtered_jobs = filtered_jobs[:limit]
            
            # Convert to response format
            job_responses = []
            for job in filtered_jobs:
                job_status = await self.get_job_status(job.job_id)
                if job_status:
                    job_responses.append(job_status)
            
            # Count jobs by status
            status_counts = self._count_jobs_by_status()
            
            return JobListResponse(
                success=True,
                message=f"Retrieved {len(job_responses)} jobs",
                jobs=job_responses,
                total_count=len(self._jobs),
                active_count=status_counts.get(JobStatus.RUNNING, 0) + status_counts.get(JobStatus.PENDING, 0),
                completed_count=status_counts.get(JobStatus.COMPLETED, 0),
                failed_count=status_counts.get(JobStatus.FAILED, 0) + status_counts.get(JobStatus.TIMEOUT, 0)
            )
            
        except Exception as e:
            self.logger.error(f"Error getting job list: {str(e)}")
            return JobListResponse(
                success=False,
                message=f"Error retrieving jobs: {str(e)}",
                jobs=[],
                total_count=0,
                active_count=0,
                completed_count=0,
                failed_count=0
            )
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or pending job"""
        try:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.TIMEOUT]:
                return False
            
            # Cancel running job
            if job.status == JobStatus.RUNNING and job_id in self._running_jobs:
                self._running_jobs[job_id].cancel()
                del self._running_jobs[job_id]
            
            # Update job status
            job.status = JobStatus.FAILED
            job.error_message = "Job cancelled by user"
            job.completed_at = datetime.utcnow()
            
            # Remove from queue
            if job_id in self._job_queue:
                self._job_queue.remove(job_id)
            
            self.logger.info(f"Job {job_id} cancelled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    def _add_to_queue(self, job_id: str):
        """Add job to the priority queue"""
        if job_id not in self._job_queue:
            self._job_queue.append(job_id)
            # Sort by priority (higher priority first)
            self._job_queue.sort(key=lambda jid: self._jobs[jid].priority, reverse=True)
    
    async def _process_job_queue(self):
        """Background task to process the job queue"""
        while not self._shutdown_event.is_set():
            try:
                # Check if we can start more jobs
                if len(self._running_jobs) < self.max_concurrent_jobs and self._job_queue:
                    # Get next job from queue
                    job_id = self._job_queue.pop(0)
                    job = self._jobs[job_id]
                    
                    # Start job execution
                    task = asyncio.create_task(self._execute_job(job))
                    self._running_jobs[job_id] = task
                    
                    # Update job status
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.utcnow()
                    
                    self.logger.info(f"Started job {job_id} ({job.job_type.value})")
                
                # Wait a bit before checking again
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in job queue processor: {str(e)}")
                await asyncio.sleep(5)
    
    async def _execute_job(self, job: Job):
        """Execute a job"""
        try:
            # Execute the appropriate script based on job type
            if job.job_type == JobType.DATA_COLLECTION:
                result = await self._run_data_collection_job(job)
            elif job.job_type == JobType.DATA_PROCESSING:
                result = await self._run_data_processing_job(job)
            elif job.job_type == JobType.FORECASTING:
                result = await self._run_forecasting_job(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            # Update job with result
            job.execution_result = result
            job.completed_at = datetime.utcnow()
            
            if result.success:
                job.status = JobStatus.COMPLETED
                job.progress = 100.0
                self._completed_jobs += 1
                log_job_complete(self.logger, job.job_id, job.job_type.value, True)
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.error_message
                self._failed_jobs += 1
                log_job_complete(self.logger, job.job_id, job.job_type.value, False)
            
        except asyncio.CancelledError:
            # Job was cancelled
            job.status = JobStatus.FAILED
            job.error_message = "Job cancelled"
            job.completed_at = datetime.utcnow()
            self._failed_jobs += 1
            log_job_complete(self.logger, job.job_id, job.job_type.value, False)
            raise
        
        except Exception as e:
            # Job failed with exception
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self._failed_jobs += 1
            log_job_complete(self.logger, job.job_id, job.job_type.value, False)
            self.logger.error(f"Job {job.job_id} failed with exception: {str(e)}")
        
        finally:
            # Remove from running jobs
            if job.job_id in self._running_jobs:
                del self._running_jobs[job.job_id]
    
    async def _run_data_collection_job(self, job: Job) -> ExecutionResult:
        """Run data collection job"""
        return self.script_runner.run_collect_script(timeout=job.timeout)
    
    async def _run_data_processing_job(self, job: Job) -> ExecutionResult:
        """Run data processing job"""
        return self.script_runner.run_pipeline_script(timeout=job.timeout)
    
    async def _run_forecasting_job(self, job: Job) -> ExecutionResult:
        """Run forecasting job"""
        return self.script_runner.run_forecast_script(timeout=job.timeout)
    
    def _get_default_timeout(self, job_type: JobType) -> int:
        """Get default timeout for job type"""
        timeouts = {
            JobType.DATA_COLLECTION: 1800,  # 30 minutes
            JobType.DATA_PROCESSING: 3600,  # 1 hour
            JobType.FORECASTING: 1800       # 30 minutes
        }
        return timeouts.get(job_type, 1800)
    
    def _estimate_job_duration(self, job_type: JobType) -> int:
        """Estimate job duration in seconds"""
        estimates = {
            JobType.DATA_COLLECTION: 300,   # 5 minutes
            JobType.DATA_PROCESSING: 1800,  # 30 minutes
            JobType.FORECASTING: 600        # 10 minutes
        }
        return estimates.get(job_type, 600)
    
    def _count_jobs_by_status(self) -> Dict[JobStatus, int]:
        """Count jobs by status"""
        counts = {}
        for job in self._jobs.values():
            counts[job.status] = counts.get(job.status, 0) + 1
        return counts
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get job service statistics"""
        status_counts = self._count_jobs_by_status()
        
        return {
            "total_jobs": self._total_jobs,
            "completed_jobs": self._completed_jobs,
            "failed_jobs": self._failed_jobs,
            "current_status": {
                "pending": status_counts.get(JobStatus.PENDING, 0),
                "running": status_counts.get(JobStatus.RUNNING, 0),
                "completed": status_counts.get(JobStatus.COMPLETED, 0),
                "failed": status_counts.get(JobStatus.FAILED, 0),
                "timeout": status_counts.get(JobStatus.TIMEOUT, 0)
            },
            "queue_length": len(self._job_queue),
            "running_jobs": len(self._running_jobs),
            "max_concurrent_jobs": self.max_concurrent_jobs
        }

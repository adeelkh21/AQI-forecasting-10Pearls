"""
Pydantic schemas for the AQI Forecasting System API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums
class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class JobType(str, Enum):
    """Types of jobs that can be executed"""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    FORECASTING = "forecasting"

class ForecastModel(str, Enum):
    """Available forecasting models"""
    CATBOOST = "catboost"
    TCN_48H = "tcn_48h"
    TCN_72H = "tcn_72h"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive model names"""
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower == "catboost" or value_lower == "catboost":
                return cls.CATBOOST
            elif value_lower == "tcn_48h" or value_lower == "tcn_48h":
                return cls.TCN_48H
            elif value_lower == "tcn_72h" or value_lower == "tcn_72h":
                return cls.TCN_72H
        return None

# Base Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Job Management Models
class JobRequest(BaseModel):
    """Request to start a new job"""
    job_type: JobType
    parameters: Optional[Dict[str, Any]] = None
    priority: int = Field(default=1, ge=1, le=10)
    timeout: Optional[int] = Field(default=None, ge=60, le=7200)

class JobResponse(BaseResponse):
    """Job creation response"""
    job_id: str
    job_type: JobType
    status: JobStatus
    estimated_duration: Optional[int] = None

class JobStatusResponse(BaseResponse):
    """Job status response"""
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None

class JobListResponse(BaseResponse):
    """List of jobs response"""
    jobs: List[JobStatusResponse]
    total_count: int
    active_count: int
    completed_count: int
    failed_count: int

# Data Models
class CurrentDataResponse(BaseResponse):
    """Current AQI and weather data response"""
    timestamp: datetime
    aqi_value: float
    aqi_category: str
    pollutants: Dict[str, float]
    weather: Dict[str, Any]
    location: str

class ForecastData(BaseModel):
    """Individual forecast data point"""
    timestamp: datetime
    hours_ahead: int
    forecast_value: float
    model_used: str  # Changed from ForecastModel to str to handle validation manually
    confidence: Optional[float] = None
    
    @validator('model_used')
    def validate_model_used(cls, v):
        """Validate and normalize model names"""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ['catboost', 'catboost']:
                return 'catboost'
            elif v_lower in ['tcn_48h', 'tcn_48h']:
                return 'tcn_48h'
            elif v_lower in ['tcn_72h', 'tcn_72h']:
                return 'tcn_72h'
            else:
                raise ValueError(f"Invalid model name: {v}. Expected: catboost, tcn_48h, or tcn_72h")
        return v

class ForecastResponse(BaseResponse):
    """Forecast response"""
    forecast_id: str
    base_timestamp: datetime
    forecast_horizon: int  # hours
    forecasts: List[ForecastData]
    metadata: Dict[str, Any]

class ForecastListResponse(BaseResponse):
    """List of available forecasts"""
    forecasts: List[ForecastResponse]
    total_count: int
    latest_forecast_id: Optional[str] = None

# System Status Models
class SystemHealthResponse(BaseResponse):
    """System health status"""
    status: str
    version: str
    uptime: float
    active_jobs: int
    system_resources: Dict[str, Any]
    last_data_update: Optional[datetime] = None
    last_forecast_update: Optional[datetime] = None

class DataSourceStatus(BaseModel):
    """Status of a data source"""
    name: str
    status: str
    last_update: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None

class SystemStatusResponse(BaseResponse):
    """Detailed system status"""
    overall_status: str
    data_sources: List[DataSourceStatus]
    model_status: Dict[str, str]
    storage_status: Dict[str, Any]

# Configuration Models
class ConfigurationUpdate(BaseModel):
    """Configuration update request"""
    key: str
    value: Any
    description: Optional[str] = None

class ConfigurationResponse(BaseResponse):
    """Configuration response"""
    config: Dict[str, Any]
    last_updated: datetime

# Utility Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class TimeRangeParams(BaseModel):
    """Time range parameters"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    hours_back: Optional[int] = Field(default=None, ge=1, le=168)

# Validation Methods
class JobRequestValidator:
    """Custom validation for job requests"""
    
    @validator('timeout')
    def validate_timeout(cls, v, values):
        if v is not None:
            job_type = values.get('job_type')
            if job_type == JobType.DATA_COLLECTION and v > 1800:
                raise ValueError("Data collection timeout cannot exceed 30 minutes")
            elif job_type == JobType.DATA_PROCESSING and v > 3600:
                raise ValueError("Data processing timeout cannot exceed 1 hour")
            elif job_type == JobType.FORECASTING and v > 1800:
                raise ValueError("Forecasting timeout cannot exceed 30 minutes")
        return v

# Response Examples
class ResponseExamples:
    """Example responses for API documentation"""
    
    SUCCESS_RESPONSE = {
        "success": True,
        "message": "Operation completed successfully",
        "timestamp": "2025-08-24T17:30:00Z"
    }
    
    ERROR_RESPONSE = {
        "success": False,
        "message": "An error occurred",
        "error_code": "VALIDATION_ERROR",
        "details": {"field": "job_type", "issue": "Invalid job type"},
        "timestamp": "2025-08-24T17:30:00Z"
    }
    
    JOB_RESPONSE = {
        "success": True,
        "message": "Job created successfully",
        "job_id": "job_12345",
        "job_type": "data_collection",
        "status": "pending",
        "estimated_duration": 300,
        "timestamp": "2025-08-24T17:30:00Z"
    }

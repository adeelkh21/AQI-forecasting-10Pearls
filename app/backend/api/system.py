"""
System API router for system status and monitoring endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import psutil
import os

from ..utils.logging import get_logger
from ..utils.paths import get_env_var

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get services
def get_services():
    from ..main import data_service, forecast_service, job_service
    if any(service is None for service in [data_service, forecast_service, job_service]):
        raise HTTPException(status_code=503, detail="One or more services not available")
    return data_service, forecast_service, job_service

@router.get("/system/status", tags=["System"])
async def get_system_status(
    services = Depends(get_services)
):
    """
    Get comprehensive system status
    
    Returns detailed status information about all system components
    including data sources, models, storage, and active jobs.
    """
    try:
        data_service, forecast_service, job_service = services
        
        # Get data sources status
        data_sources = data_service.get_data_sources_status()
        
        # Get model status
        model_status = {
            "catboost": "available" if os.path.exists("saved_models/champions/catboost_24h.txt") else "missing",
            "tcn_48h": "available" if os.path.exists("saved_models/champions/tcn_48h.pth") else "missing",
            "tcn_72h": "available" if os.path.exists("saved_models/champions/tcn_72h.pth") else "missing"
        }
        
        # Get storage status
        storage_status = {
            "data_repositories": {
                "exists": os.path.exists("data_repositories"),
                "size_mb": round(psutil.disk_usage("data_repositories").used / (1024 * 1024), 2) if os.path.exists("data_repositories") else 0
            },
            "saved_models": {
                "exists": os.path.exists("saved_models"),
                "size_mb": round(psutil.disk_usage("saved_models").used / (1024 * 1024), 2) if os.path.exists("saved_models") else 0
            }
        }
        
        # Get job service statistics
        job_stats = job_service.get_service_statistics()
        
        # Determine overall status
        overall_status = "healthy"
        if any(source.status in ["missing", "error"] for source in data_sources):
            overall_status = "degraded"
        if any(model == "missing" for model in model_status.values()):
            overall_status = "degraded"
        if job_stats["failed_jobs"] > 0:
            overall_status = "warning"
        
        return {
            "success": True,
            "message": "System status retrieved successfully",
            "data": {
                "overall_status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "data_sources": data_sources,
                "model_status": model_status,
                "storage_status": storage_status,
                "job_service": job_stats
            },
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving system status: {str(e)}"
        )

@router.get("/system/health", tags=["System"])
async def get_system_health(
    services = Depends(get_services)
):
    """
    Get system health information
    
    Returns basic health metrics including service availability,
    system resources, and uptime information.
    """
    try:
        data_service, forecast_service, job_service = services
        
        # Get system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get service status
        services_status = {
            "data_service": data_service is not None,
            "forecast_service": forecast_service is not None,
            "job_service": job_service is not None
        }
        
        # Get job counts
        job_stats = job_service.get_service_statistics()
        active_jobs = job_stats["current_status"]["running"] + job_stats["current_status"]["pending"]
        
        # Get last data update
        data_sources = data_service.get_data_sources_status()
        last_data_update = None
        for source in data_sources:
            if source.last_update and (last_data_update is None or source.last_update > last_data_update):
                last_data_update = source.last_update
        
        # Get last forecast update
        forecast_info = data_service.get_latest_forecast_info()
        last_forecast_update = datetime.fromtimestamp(forecast_info["timestamp"]) if forecast_info else None
        
        # Calculate uptime (simplified - could be enhanced with actual start time tracking)
        uptime = 0  # Placeholder - would need to track actual start time
        
        return {
            "success": True,
            "message": "System health check completed",
            "data": {
                "status": "healthy" if all(services_status.values()) else "degraded",
                "version": "1.0.0",
                "uptime": uptime,
                "active_jobs": active_jobs,
                "system_resources": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                "last_data_update": last_data_update.isoformat() if last_data_update else None,
                "last_forecast_update": last_forecast_update.isoformat() if last_forecast_update else None
            },
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving system health: {str(e)}"
        )

@router.get("/system/info", tags=["System"])
async def get_system_info():
    """
    Get basic system information
    
    Returns general system information including environment,
    configuration, and version details.
    """
    try:
        # Get environment information
        env_info = {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.sys.platform,
            "api_host": get_env_var("API_HOST", "127.0.0.1"),
            "api_port": get_env_var("API_PORT", "8000"),
            "streamlit_port": get_env_var("STREAMLIT_SERVER_PORT", "8501"),
            "log_level": get_env_var("LOG_LEVEL", "INFO"),
            "max_concurrent_jobs": get_env_var("MAX_CONCURRENT_JOBS", "3")
        }
        
        # Get working directory and file structure
        current_dir = os.getcwd()
        file_structure = {
            "current_directory": current_dir,
            "data_repositories_exists": os.path.exists("data_repositories"),
            "saved_models_exists": os.path.exists("saved_models"),
            "app_directory_exists": os.path.exists("app")
        }
        
        return {
            "success": True,
            "message": "System information retrieved successfully",
            "data": {
                "system_info": env_info,
                "file_structure": file_structure,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving system information: {str(e)}"
        )

@router.get("/system/metrics", tags=["System"])
async def get_system_metrics():
    """
    Get system performance metrics
    
    Returns detailed performance metrics including CPU, memory,
    disk usage, and network statistics.
    """
    try:
        # CPU metrics
        cpu_metrics = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_metrics = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        }
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_metrics = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }
        
        # Network metrics
        network = psutil.net_io_counters()
        network_metrics = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        return {
            "success": True,
            "message": "System metrics retrieved successfully",
            "data": {
                "cpu": cpu_metrics,
                "memory": memory_metrics,
                "disk": disk_metrics,
                "network": network_metrics,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving system metrics: {str(e)}"
        )

@router.post("/system/restart", tags=["System"])
async def restart_system():
    """
    Request system restart
    
    This endpoint can be used to request a system restart.
    Note: This is a placeholder for future implementation.
    """
    try:
        # This would be implemented based on your deployment strategy
        # For now, just return a message
        return {
            "success": True,
            "message": "System restart requested (not implemented in development mode)",
            "warning": "This endpoint is a placeholder for production deployment",
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Error requesting system restart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error requesting system restart: {str(e)}"
        )

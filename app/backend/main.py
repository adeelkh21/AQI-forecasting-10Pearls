"""
Main FastAPI application for the AQI Forecasting System
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .utils.paths import API_HOST, API_PORT, API_RELOAD
from .utils.logging import setup_logging, get_logger
from .services.data_service import DataService
from .services.forecast_service import ForecastService
from .services.job_service import JobService

# Setup logging
logger = get_logger(__name__)

# Global service instances
data_service: DataService = None
forecast_service: ForecastService = None
job_service: JobService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting AQI Forecasting System...")
    
    global data_service, forecast_service, job_service
    
    try:
        # Initialize services
        data_service = DataService()
        forecast_service = ForecastService()
        job_service = JobService()
        
        # Start job service
        await job_service.start()
        
        logger.info("✅ All services started successfully")
        
    except Exception as e:
        logger.error(f"❌ Error starting services: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AQI Forecasting System...")
    
    try:
        if job_service:
            await job_service.stop()
        logger.info("✅ All services stopped successfully")
        
    except Exception as e:
        logger.error(f"❌ Error stopping services: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="AQI Forecasting System API",
    description="Real-time AQI forecasting system with data collection, processing, and prediction capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": None
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "details": None,
            "timestamp": None
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": str(exc) if app.debug else "An unexpected error occurred",
            "timestamp": None
        }
    )

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    try:
        # Check if services are available
        services_status = {
            "data_service": data_service is not None,
            "forecast_service": forecast_service is not None,
            "job_service": job_service is not None
        }
        
        overall_status = "healthy" if all(services_status.values()) else "degraded"
        
        return {
            "success": True,
            "message": "System health check completed",
            "status": overall_status,
            "services": services_status,
            "timestamp": None
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Health check failed",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": None
            }
        )

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "success": True,
        "message": "AQI Forecasting System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": None
    }

# Import and include routers
from .api import data, forecasts, jobs, system

app.include_router(data.router, prefix="/api/v1", tags=["Data"])
app.include_router(forecasts.router, prefix="/api/v1", tags=["Forecasts"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "app.backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD,
        log_level="info"
    )

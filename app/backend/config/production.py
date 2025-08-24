"""
Production configuration for the AQI Forecasting System
"""
import os
from typing import Dict, Any
from pathlib import Path

# Production environment settings
PRODUCTION_CONFIG = {
    # Server Configuration
    "server": {
        "host": os.getenv("PROD_HOST", "0.0.0.0"),
        "port": int(os.getenv("PROD_PORT", "8000")),
        "workers": int(os.getenv("PROD_WORKERS", "4")),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "max_requests": 1000,
        "max_requests_jitter": 100,
        "timeout": 120,
        "keepalive": 5,
        "backlog": 2048
    },
    
    # Database & Caching
    "cache": {
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "cache_ttl": 300,  # 5 minutes
        "max_cache_size": 1000,
        "cache_eviction_policy": "lru"
    },
    
    # Security
    "security": {
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:8501,https://yourdomain.com").split(","),
        "rate_limit": {
            "requests_per_minute": 100,
            "burst_size": 20
        },
        "api_keys": {
            "enabled": os.getenv("API_KEYS_ENABLED", "false").lower() == "true",
            "header_name": "X-API-Key"
        }
    },
    
    # Logging
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "json",
        "file_path": "/var/log/aqi-forecasting/app.log",
        "max_file_size": "100MB",
        "backup_count": 5,
        "syslog": {
            "enabled": os.getenv("SYSLOG_ENABLED", "false").lower() == "true",
            "host": os.getenv("SYSLOG_HOST", "localhost"),
            "port": int(os.getenv("SYSLOG_PORT", "514"))
        }
    },
    
    # Monitoring
    "monitoring": {
        "health_check_interval": 30,
        "metrics_collection": True,
        "alerting": {
            "enabled": os.getenv("ALERTING_ENABLED", "false").lower() == "true",
            "webhook_url": os.getenv("ALERT_WEBHOOK_URL", ""),
            "thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90
            }
        }
    },
    
    # Performance
    "performance": {
        "connection_pool_size": 20,
        "max_concurrent_jobs": int(os.getenv("MAX_CONCURRENT_JOBS", "5")),
        "job_timeout": int(os.getenv("JOB_TIMEOUT", "7200")),  # 2 hours
        "compression": True,
        "gzip_level": 6
    },
    
    # Data Management
    "data": {
        "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",
        "backup_interval_hours": 24,
        "backup_retention_days": 30,
        "data_validation": True,
        "auto_cleanup": True,
        "cleanup_threshold_days": 90
    }
}

def get_production_config() -> Dict[str, Any]:
    """Get production configuration"""
    return PRODUCTION_CONFIG

def get_production_env_vars() -> Dict[str, str]:
    """Get required production environment variables"""
    return {
        "PROD_HOST": "Production server host (default: 0.0.0.0)",
        "PROD_PORT": "Production server port (default: 8000)",
        "PROD_WORKERS": "Number of worker processes (default: 4)",
        "REDIS_URL": "Redis connection URL for caching",
        "CORS_ORIGINS": "Comma-separated list of allowed origins",
        "API_KEYS_ENABLED": "Enable API key authentication (true/false)",
        "LOG_LEVEL": "Logging level (DEBUG, INFO, WARNING, ERROR)",
        "SYSLOG_ENABLED": "Enable syslog integration (true/false)",
        "ALERTING_ENABLED": "Enable system alerting (true/false)",
        "ALERT_WEBHOOK_URL": "Webhook URL for alerts",
        "BACKUP_ENABLED": "Enable automatic backups (true/false)",
        "MAX_CONCURRENT_JOBS": "Maximum concurrent background jobs",
        "JOB_TIMEOUT": "Job execution timeout in seconds"
    }

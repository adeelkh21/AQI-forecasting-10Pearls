"""
Centralized path management for the AQI Forecasting System
"""
import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")

# Get the project root directory (3 levels up from this file)
ROOT = Path(__file__).resolve().parents[3]

# Data repositories
DATA_REPOSITORIES = ROOT / "data_repositories"
HISTORICAL_DATA = DATA_REPOSITORIES / "historical_data"
PROCESSED_DATA = HISTORICAL_DATA / "processed"
FEATURES_DIR = DATA_REPOSITORIES / "features"

# Key data files
MERGED_CSV = PROCESSED_DATA / "merged_data.csv"
FEATURES_CSV = FEATURES_DIR / "phase1_fixed_selected_features.csv"
FEATURE_COLS_PKL = FEATURES_DIR / "phase1_fixed_feature_columns.pkl"
FEATURE_SCALER_PKL = FEATURES_DIR / "phase1_fixed_feature_scaler.pkl"

# Forecast-ready files (from combined_data_pipeline.py)
FORECAST_READY_CSV = FEATURES_DIR / "forecast_ready_features.csv"
FORECAST_READY_COLS_PKL = FEATURES_DIR / "forecast_ready_feature_columns.pkl"
FORECAST_READY_SCALER_PKL = FEATURES_DIR / "forecast_ready_scaler.pkl"

# Models and forecasts
MODELS_DIR = ROOT / "saved_models"
CHAMPIONS_DIR = MODELS_DIR / "champions"
FORECASTS_DIR = MODELS_DIR / "forecasts"

# Python interpreter paths
def get_python_executable() -> str:
    """Get the Python executable path, preferring venv if available"""
    # Try venv first
    venv_python = ROOT / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    
    # Fallback to system python
    return "python"

# Script paths
SCRIPTS_DIR = ROOT
COLLECT_SCRIPT = SCRIPTS_DIR / "collect_1hour.py"
COMBINED_PIPELINE_SCRIPT = SCRIPTS_DIR / "combined_data_pipeline.py"
FORECAST_SCRIPT = SCRIPTS_DIR / "forecast_continuous_72h.py"

# Environment variables
def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable with fallback to default"""
    return os.getenv(key, default)

# API Configuration
API_HOST = get_env_var("API_HOST", "127.0.0.1")
API_PORT = int(get_env_var("API_PORT", "8000"))
API_RELOAD = get_env_var("API_RELOAD", "true").lower() == "true"

# Streamlit Configuration
STREAMLIT_API_BASE = get_env_var("STREAMLIT_API_BASE", "http://127.0.0.1:8501")
STREAMLIT_SERVER_PORT = int(get_env_var("STREAMLIT_SERVER_PORT", "8501"))

# Job Configuration
JOB_TIMEOUT = int(get_env_var("JOB_TIMEOUT", "3600"))
MAX_CONCURRENT_JOBS = int(get_env_var("MAX_CONCURRENT_JOBS", "3"))

# Logging Configuration
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO")
LOG_FORMAT = get_env_var("LOG_FORMAT", "json")

# Validation functions
def validate_paths() -> bool:
    """Validate that all required paths exist"""
    required_paths = [
        ROOT,
        DATA_REPOSITORIES,
        HISTORICAL_DATA,
        PROCESSED_DATA,
        FEATURES_DIR,
        MODELS_DIR,
        CHAMPIONS_DIR,
        FORECASTS_DIR
    ]
    
    missing_paths = []
    for path in required_paths:
        if not path.exists():
            missing_paths.append(str(path))
    
    if missing_paths:
        print(f"❌ Missing required paths: {missing_paths}")
        return False
    
    print("✅ All required paths validated successfully")
    return True

def get_latest_forecast_file() -> Optional[Path]:
    """Get the latest forecast file from the forecasts directory"""
    if not FORECASTS_DIR.exists():
        return None
    
    forecast_files = list(FORECASTS_DIR.glob("forecast_continuous_72h_*_timeline.csv"))
    if not forecast_files:
        return None
    
    # Sort by modification time and return the latest
    latest_file = max(forecast_files, key=lambda f: f.stat().st_mtime)
    return latest_file

if __name__ == "__main__":
    print("🔍 Validating AQI Forecasting System paths...")
    print(f"📁 Project Root: {ROOT}")
    print(f"🐍 Python Executable: {get_python_executable()}")
    print(f"📊 Data Directory: {DATA_REPOSITORIES}")
    print(f"🤖 Models Directory: {MODELS_DIR}")
    
    if validate_paths():
        print("✅ Path validation successful!")
    else:
        print("❌ Path validation failed!")

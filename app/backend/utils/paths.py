from pathlib import Path
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (3 levels up from this file: utils/backend/app/ -> project_root)
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print(f"⚠️ .env file not found at: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")


ROOT = Path(__file__).resolve().parents[3]  # Fixed: 3 levels up to get to project root

# Data repositories
DATA_REPO = ROOT / "data_repositories"
HIST_PROCESSED = DATA_REPO / "historical_data" / "processed"
MERGED_CSV = HIST_PROCESSED / "merged_data.csv"

# Features
FEATURES_DIR = DATA_REPO / "features"
FEATURES_CSV = FEATURES_DIR / "phase1_fixed_selected_features.csv"
FEATURE_COLS_PKL = FEATURES_DIR / "phase1_fixed_feature_columns.pkl"
FEATURE_SCALER_PKL = FEATURES_DIR / "phase1_fixed_feature_scaler.pkl"

# Models and outputs
SAVED_MODELS = ROOT / "saved_models"
FORECASTS_DIR = SAVED_MODELS / "forecasts"
MODELS_DIR = SAVED_MODELS
CHAMPIONS_DIR = SAVED_MODELS / "champions"
REPORTS_DIR = SAVED_MODELS / "reports"

# Ensure critical directories exist
FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
CHAMPIONS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Script paths
SCRIPTS_DIR = ROOT
PHASE1_SCRIPT = SCRIPTS_DIR / "phase1_data_collection.py"
PHASE2_SCRIPT = SCRIPTS_DIR / "phase2_data_preprocessing.py"
PHASE3_SCRIPT = SCRIPTS_DIR / "phase3_feature_selection.py"
FORECAST_SCRIPT = SCRIPTS_DIR / "forecast.py"


def resolve_python_executable() -> str:
    win_py = ROOT / "venv" / "Scripts" / "python.exe"
    if win_py.exists():
        return str(win_py)
    nix_py = ROOT / "venv" / "bin" / "python"
    if nix_py.exists():
        return str(nix_py)
    return os.environ.get("PYTHON_EXECUTABLE", "python")


RUN_PY = resolve_python_executable()

# Environment configuration
def get_env_config():
    return {
        "API_HOST": os.getenv("API_HOST", "127.0.0.1"),
        "API_PORT": int(os.getenv("API_PORT", "8000")),
        "STREAMLIT_API_BASE": os.getenv("STREAMLIT_API_BASE", "http://127.0.0.1:8000"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY", ""),
    }


ENV_CONFIG = get_env_config()



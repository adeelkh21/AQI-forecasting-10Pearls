# Data preprocessing service - wraps phase2 + phase3
import asyncio
from pathlib import Path
from typing import Dict, Any

from ..utils.paths import PHASE2_SCRIPT, PHASE3_SCRIPT, FEATURES_CSV, FEATURE_COLS_PKL, FEATURE_SCALER_PKL
from ..utils.runner import run_script
from ..utils.logging import get_logger

logger = get_logger('preprocess')


async def preprocess_data() -> Dict[str, Any]:
    """
    Run data preprocessing (phase2 + phase3).
    
    Returns:
        Dict with success status and artifact paths
    """
    try:
        logger.info("Starting data preprocessing pipeline")
        
        # Step 1: Run phase2 data preprocessing
        logger.info("Running phase2 data preprocessing...")
        phase2_result = run_script(PHASE2_SCRIPT, timeout=3600)  # 1 hour timeout
        
        if not phase2_result.success:
            logger.error(f"Phase2 preprocessing failed: {phase2_result.stderr}")
            return {
                "success": False,
                "phase2_success": False,
                "phase3_success": False,
                "error": f"Phase2 failed: {phase2_result.stderr}",
                "features_csv": None,
                "feature_cols_pkl": None,
                "feature_scaler_pkl": None
            }
        
        logger.info("Phase2 preprocessing completed successfully")
        
        # Step 2: Run phase3 feature selection
        logger.info("Running phase3 feature selection...")
        phase3_result = run_script(PHASE3_SCRIPT, timeout=1800)  # 30 min timeout
        
        if not phase3_result.success:
            logger.error(f"Phase3 feature selection failed: {phase3_result.stderr}")
            return {
                "success": False,
                "phase2_success": True,
                "phase3_success": False,
                "error": f"Phase3 failed: {phase3_result.stderr}",
                "features_csv": None,
                "feature_cols_pkl": None,
                "feature_scaler_pkl": None
            }
        
        logger.info("Phase3 feature selection completed successfully")
        
        # Step 3: Verify artifacts were created
        artifacts_status = _verify_artifacts()
        
        if not artifacts_status["all_exist"]:
            logger.warning("Some artifacts missing after preprocessing")
            return {
                "success": False,
                "phase2_success": True,
                "phase3_success": True,
                "error": f"Missing artifacts: {artifacts_status['missing']}",
                "features_csv": artifacts_status["features_csv"],
                "feature_cols_pkl": artifacts_status["feature_cols_pkl"],
                "feature_scaler_pkl": artifacts_status["feature_scaler_pkl"]
            }
        
        logger.info("Data preprocessing pipeline completed successfully")
        
        return {
            "success": True,
            "phase2_success": True,
            "phase3_success": True,
            "error": None,
            "features_csv": str(FEATURES_CSV) if FEATURES_CSV.exists() else None,
            "feature_cols_pkl": str(FEATURE_COLS_PKL) if FEATURE_COLS_PKL.exists() else None,
            "feature_scaler_pkl": str(FEATURE_SCALER_PKL) if FEATURE_SCALER_PKL.exists() else None,
            "message": "Preprocessing completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Data preprocessing failed: {e}")
        return {
            "success": False,
            "phase2_success": False,
            "phase3_success": False,
            "error": str(e),
            "features_csv": None,
            "feature_cols_pkl": None,
            "feature_scaler_pkl": None
        }


def _verify_artifacts() -> Dict[str, Any]:
    """
    Verify that all required preprocessing artifacts exist.
    
    Returns:
        Dict with artifact verification status
    """
    artifacts = {
        "features_csv": FEATURES_CSV,
        "feature_cols_pkl": FEATURE_COLS_PKL,
        "feature_scaler_pkl": FEATURE_SCALER_PKL
    }
    
    status = {}
    missing = []
    
    for name, path in artifacts.items():
        exists = path.exists()
        status[name] = str(path) if exists else None
        if not exists:
            missing.append(name)
    
    status["all_exist"] = len(missing) == 0
    status["missing"] = missing
    
    return status

# Forecast service - wraps forecast.py execution
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from ..utils.paths import FORECAST_SCRIPT, FORECASTS_DIR
from ..utils.runner import run_script
from ..utils.logging import get_logger

logger = get_logger('forecast')


async def run_forecast() -> Dict[str, Any]:
    """
    Run the AQI forecasting pipeline.
    
    Returns:
        Dict with forecast results and metadata
    """
    try:
        logger.info("Starting AQI forecast pipeline")
        
        # Ensure forecasts directory exists
        FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run the forecast script
        logger.info("Executing forecast script...")
        result = run_script(FORECAST_SCRIPT, timeout=3600)  # 1 hour timeout
        
        if not result.success:
            logger.error(f"Forecast script failed: {result.stderr}")
            raise RuntimeError(f"Forecast failed: {result.stderr}")
        
        logger.info("Forecast script completed successfully")
        
        # Find and normalize forecast outputs
        forecast_outputs = _find_forecast_outputs()
        
        if not forecast_outputs:
            logger.warning("No forecast outputs found")
            return {
                "success": False,
                "error": "No forecast outputs generated",
                "outputs": []
            }
        
        # Normalize and validate each forecast output
        normalized_outputs = []
        for output in forecast_outputs:
            try:
                normalized = _normalize_forecast_output(output)
                if normalized:
                    normalized_outputs.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize forecast output {output}: {e}")
        
        if not normalized_outputs:
            logger.error("No forecast outputs could be normalized")
            return {
                "success": False,
                "error": "All forecast outputs failed normalization",
                "outputs": []
            }
        
        # Create forecast metadata
        metadata = _create_forecast_metadata(normalized_outputs)
        
        # Save metadata
        metadata_file = FORECASTS_DIR / f"forecast_metadata_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Forecast completed successfully with {len(normalized_outputs)} outputs")
        
        return {
            "success": True,
            "outputs": normalized_outputs,
            "metadata": metadata,
            "metadata_file": str(metadata_file),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Forecast pipeline failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "outputs": [],
            "timestamp": datetime.now().isoformat()
        }


def _find_forecast_outputs() -> List[Path]:
    """
    Find forecast output files.
    
    Returns:
        List of forecast output file paths
    """
    outputs = []
    
    # Look for forecast CSV files
    csv_pattern = FORECASTS_DIR / "*.csv"
    for csv_file in Path(FORECASTS_DIR).glob("*.csv"):
        if "forecast" in csv_file.name.lower():
            outputs.append(csv_file)
    
    # Look for forecast plot files
    plot_pattern = FORECASTS_DIR / "*.png"
    for plot_file in Path(FORECASTS_DIR).glob("*.png"):
        if "forecast" in plot_file.name.lower():
            outputs.append(plot_file)
    
    # Look for forecast plot files
    plot_pattern = FORECASTS_DIR / "*.jpg"
    for plot_file in Path(FORECASTS_DIR).glob("*.jpg"):
        if "forecast" in plot_file.name.lower():
            outputs.append(plot_file)
    
    logger.info(f"Found {len(outputs)} forecast outputs: {[f.name for f in outputs]}")
    return outputs


def _normalize_forecast_output(output_file: Path) -> Optional[Dict[str, Any]]:
    """
    Normalize a forecast output file.
    
    Args:
        output_file: Path to forecast output file
        
    Returns:
        Normalized output metadata or None
    """
    try:
        if not output_file.exists():
            logger.warning(f"Forecast output file does not exist: {output_file}")
            return None
        
        file_info = {
            "file_path": str(output_file),
            "file_name": output_file.name,
            "file_size": output_file.stat().st_size,
            "last_modified": datetime.fromtimestamp(output_file.stat().st_mtime).isoformat(),
            "file_type": output_file.suffix.lower()
        }
        
        # Handle CSV files specifically
        if output_file.suffix.lower() == '.csv':
            csv_info = _normalize_forecast_csv(output_file)
            if csv_info:
                file_info.update(csv_info)
        
        # Handle plot files
        elif output_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            file_info.update({
                "plot_type": "forecast_visualization",
                "dimensions": _get_image_dimensions(output_file)
            })
        
        logger.info(f"Normalized forecast output: {output_file.name}")
        return file_info
        
    except Exception as e:
        logger.error(f"Failed to normalize forecast output {output_file}: {e}")
        return None


def _normalize_forecast_csv(csv_file: Path) -> Optional[Dict[str, Any]]:
    """
    Normalize a forecast CSV file.
    
    Args:
        csv_file: Path to forecast CSV file
        
    Returns:
        CSV metadata or None
    """
    try:
        # Read CSV to validate and extract metadata
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning(f"Forecast CSV is empty: {csv_file}")
            return None
        
        # Validate required columns
        required_columns = ['timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing required columns in forecast CSV: {missing_columns}")
            return None
        
        # Validate timestamp column
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        invalid_timestamps = df['timestamp'].isna().sum()
        if invalid_timestamps > 0:
            logger.warning(f"Found {invalid_timestamps} invalid timestamps in forecast CSV")
            df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            logger.warning(f"No valid timestamps found in forecast CSV: {csv_file}")
            return None
        
        # Extract forecast metadata
        forecast_start = df['timestamp'].min()
        forecast_end = df['timestamp'].max()
        forecast_hours = len(df)
        
        # Check for AQI prediction columns
        aqi_columns = [col for col in df.columns if 'aqi' in col.lower() or 'predicted' in col.lower()]
        
        # Validate AQI values if present
        aqi_validation = {}
        for col in aqi_columns:
            try:
                aqi_values = pd.to_numeric(df[col], errors='coerce')
                valid_count = aqi_values.notna().sum()
                if valid_count > 0:
                    aqi_validation[col] = {
                        "valid_count": int(valid_count),
                        "min_value": float(aqi_values.min()),
                        "max_value": float(aqi_values.max()),
                        "mean_value": float(aqi_values.mean())
                    }
            except Exception as e:
                logger.warning(f"Failed to validate AQI column {col}: {e}")
        
        return {
            "forecast_type": "csv",
            "forecast_start": forecast_start.isoformat(),
            "forecast_end": forecast_end.isoformat(),
            "forecast_hours": forecast_hours,
            "total_columns": len(df.columns),
            "aqi_columns": aqi_columns,
            "aqi_validation": aqi_validation,
            "row_count": len(df),
            "columns": list(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Failed to normalize forecast CSV {csv_file}: {e}")
        return None


def _get_image_dimensions(image_file: Path) -> Dict[str, Any]:
    """
    Get image dimensions for plot files.
    
    Args:
        image_file: Path to image file
        
    Returns:
        Image dimensions or error info
    """
    try:
        from PIL import Image
        with Image.open(image_file) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
    except ImportError:
        logger.warning("PIL not available, cannot get image dimensions")
        return {"error": "PIL not available"}
    except Exception as e:
        logger.warning(f"Failed to get image dimensions: {e}")
        return {"error": str(e)}


def _create_forecast_metadata(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create comprehensive forecast metadata.
    
    Args:
        outputs: List of normalized forecast outputs
        
    Returns:
        Forecast metadata dictionary
    """
    try:
        # Separate outputs by type
        csv_outputs = [o for o in outputs if o.get('forecast_type') == 'csv']
        plot_outputs = [o for o in outputs if o.get('plot_type') == 'forecast_visualization']
        
        # Extract forecast information
        forecast_info = {}
        if csv_outputs:
            # Get the main forecast CSV (usually the first one)
            main_csv = csv_outputs[0]
            forecast_info = {
                "forecast_start": main_csv.get('forecast_start'),
                "forecast_end": main_csv.get('forecast_end'),
                "forecast_hours": main_csv.get('forecast_hours'),
                "forecast_columns": main_csv.get('aqi_columns', [])
            }
        
        metadata = {
            "forecast_id": f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "outputs_count": len(outputs),
            "csv_outputs": len(csv_outputs),
            "plot_outputs": len(plot_outputs),
            "forecast_info": forecast_info,
            "outputs": outputs
        }
        
        logger.info(f"Created forecast metadata: {metadata['forecast_id']}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to create forecast metadata: {e}")
        return {
            "forecast_id": f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
            "outputs": outputs
        }


async def get_latest_forecast() -> Optional[Dict[str, Any]]:
    """
    Get metadata for the latest forecast.
    
    Returns:
        Latest forecast metadata or None
    """
    try:
        if not FORECASTS_DIR.exists():
            logger.warning("Forecasts directory does not exist")
            return None
        
        # Find the most recent forecast metadata file
        metadata_files = list(FORECASTS_DIR.glob("forecast_metadata_*.json"))
        if not metadata_files:
            logger.info("No forecast metadata files found")
            return None
        
        # Get the most recent one
        latest_metadata = max(metadata_files, key=lambda f: f.stat().st_mtime)
        
        # Read and return metadata
        with open(latest_metadata, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"Retrieved latest forecast metadata: {metadata.get('forecast_id', 'unknown')}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to get latest forecast: {e}")
        return None


async def get_forecast_by_id(forecast_id: str) -> Optional[Dict[str, Any]]:
    """
    Get forecast metadata by ID.
    
    Args:
        forecast_id: Forecast ID to retrieve
        
    Returns:
        Forecast metadata or None
    """
    try:
        if not FORECASTS_DIR.exists():
            return None
        
        # Search for metadata file with matching ID
        for metadata_file in FORECASTS_DIR.glob("forecast_metadata_*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata.get('forecast_id') == forecast_id:
                        return metadata
            except Exception as e:
                logger.warning(f"Failed to read metadata file {metadata_file}: {e}")
                continue
        
        logger.info(f"Forecast with ID {forecast_id} not found")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get forecast by ID: {e}")
        return None

"""
Forecast service for AQI forecasting operations
"""
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils.paths import FORECASTS_DIR, get_latest_forecast_file
from ..utils.logging import get_logger, log_data_operation
from ..models.schemas import (
    ForecastResponse, ForecastData, ForecastListResponse,
    ForecastModel, JobType
)

logger = get_logger(__name__)

class ForecastService:
    """Service for managing AQI forecasts"""
    
    def __init__(self):
        self.logger = logger
        self._forecast_cache = {}
        self._cache_ttl = 600  # 10 minutes cache TTL
    
    def get_latest_forecast(self) -> Optional[ForecastResponse]:
        """Get the latest available forecast"""
        try:
            latest_file = get_latest_forecast_file()
            if not latest_file:
                return None
            
            # Check cache first
            cache_key = str(latest_file)
            if self._is_cache_valid(cache_key):
                return self._forecast_cache[cache_key]['data']
            
            # Load and parse forecast data
            forecast_data = self._load_forecast_from_file(latest_file)
            if forecast_data:
                # Update cache
                self._update_cache(cache_key, forecast_data)
                return forecast_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest forecast: {str(e)}")
            return None
    
    def get_forecast_by_id(self, forecast_id: str) -> Optional[ForecastResponse]:
        """Get a specific forecast by ID"""
        try:
            # Look for forecast file with matching ID
            forecast_files = list(FORECASTS_DIR.glob(f"*{forecast_id}*.csv"))
            if not forecast_files:
                return None
            
            forecast_file = forecast_files[0]
            return self._load_forecast_from_file(forecast_file)
            
        except Exception as e:
            self.logger.error(f"Error getting forecast by ID {forecast_id}: {str(e)}")
            return None
    
    def get_forecast_list(self, limit: int = 10) -> ForecastListResponse:
        """Get list of available forecasts"""
        try:
            if not FORECASTS_DIR.exists():
                return ForecastListResponse(
                    success=False,
                    message="Forecasts directory not found",
                    forecasts=[],
                    total_count=0,
                    latest_forecast_id=None
                )
            
            # Get all forecast files
            forecast_files = list(FORECASTS_DIR.glob("forecast_continuous_72h_*.csv"))
            forecast_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Limit results
            forecast_files = forecast_files[:limit]
            
            forecasts = []
            for file_path in forecast_files:
                try:
                    forecast_data = self._load_forecast_from_file(file_path)
                    if forecast_data:
                        forecasts.append(forecast_data)
                except Exception as e:
                    self.logger.warning(f"Error loading forecast from {file_path}: {str(e)}")
                    continue
            
            # Get latest forecast ID
            latest_forecast_id = None
            if forecasts:
                latest_forecast_id = forecasts[0].forecast_id
            
            return ForecastListResponse(
                success=True,
                message=f"Retrieved {len(forecasts)} forecasts",
                forecasts=forecasts,
                total_count=len(forecasts),
                latest_forecast_id=latest_forecast_id
            )
            
        except Exception as e:
            self.logger.error(f"Error getting forecast list: {str(e)}")
            return ForecastListResponse(
                success=False,
                message=f"Error retrieving forecasts: {str(e)}",
                forecasts=[],
                total_count=0,
                latest_forecast_id=None
            )
    
    def get_forecast_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get statistics about forecasts in the last N hours"""
        try:
            if not FORECASTS_DIR.exists():
                return {"error": "Forecasts directory not found"}
            
            # Get recent forecast files
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            forecast_files = []
            
            for file_path in FORECASTS_DIR.glob("forecast_continuous_72h_*.csv"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time >= cutoff_time:
                    forecast_files.append(file_path)
            
            if not forecast_files:
                return {"error": f"No forecasts found in the last {hours_back} hours"}
            
            # Calculate statistics
            stats = {
                "period_hours": hours_back,
                "forecast_count": len(forecast_files),
                "total_size_mb": sum(f.stat().st_size for f in forecast_files) / (1024 * 1024),
                "models_used": set(),
                "horizon_hours": 0,
                "accuracy_metrics": {}
            }
            
            # Analyze each forecast file
            for file_path in forecast_files:
                try:
                    df = pd.read_csv(file_path)
                    
                    # Update models used
                    if 'model_used' in df.columns:
                        stats["models_used"].update(df['model_used'].unique())
                    
                    # Update horizon hours
                    if 'hours_ahead' in df.columns:
                        stats["horizon_hours"] = max(stats["horizon_hours"], df['hours_ahead'].max())
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing forecast file {file_path}: {str(e)}")
                    continue
            
            # Convert set to list for JSON serialization
            stats["models_used"] = list(stats["models_used"])
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            
            log_data_operation(self.logger, "forecast_statistics_generated", str(FORECASTS_DIR), hours_back=hours_back)
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating forecast statistics: {str(e)}")
            return {"error": str(e)}
    
    def _load_forecast_from_file(self, file_path: Path) -> Optional[ForecastResponse]:
        """Load forecast data from a CSV file"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return None
            
            # Extract forecast ID from filename
            forecast_id = file_path.stem
            
            # Parse timestamp column
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                base_timestamp = df['timestamp'].min()
            else:
                base_timestamp = datetime.now()
            
            # Create forecast data points
            forecasts = []
            for _, row in df.iterrows():
                try:
                    # Normalize model name to handle case variations
                    model_used = row['model_used']
                    if isinstance(model_used, str):
                        model_lower = model_used.lower()
                        if 'catboost' in model_lower:
                            model_used = 'catboost'
                        elif 'tcn_48h' in model_lower:
                            model_used = 'tcn_48h'
                        elif 'tcn_72h' in model_lower:
                            model_used = 'tcn_72h'
                        else:
                            self.logger.warning(f"Unknown model name: {model_used}, using 'catboost' as default")
                            model_used = 'catboost'
                    
                    forecast_data = ForecastData(
                        timestamp=row['timestamp'],
                        hours_ahead=int(row['hours_ahead']),
                        forecast_value=float(row['forecast_value']),
                        model_used=model_used,
                        confidence=row.get('confidence') if 'confidence' in row else None
                    )
                    forecasts.append(forecast_data)
                except Exception as e:
                    self.logger.warning(f"Error parsing forecast row: {str(e)}")
                    continue
            
            if not forecasts:
                return None
            
            # Create metadata
            metadata = {
                "source_file": str(file_path),
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "total_forecasts": len(forecasts),
                "models_used": list(set(f.model_used for f in forecasts)),
                "horizon_hours": max(f.hours_ahead for f in forecasts)
            }
            
            return ForecastResponse(
                success=True,
                message="Forecast loaded successfully",
                forecast_id=forecast_id,
                base_timestamp=base_timestamp,
                forecast_horizon=metadata["horizon_hours"],
                forecasts=forecasts,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error loading forecast from {file_path}: {str(e)}")
            return None
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached forecast is still valid"""
        if cache_key not in self._forecast_cache:
            return False
        
        cache_entry = self._forecast_cache[cache_key]
        cache_age = datetime.now().timestamp() - cache_entry['timestamp']
        return cache_age < self._cache_ttl
    
    def _update_cache(self, cache_key: str, data: ForecastResponse):
        """Update the forecast cache"""
        self._forecast_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        self.logger.debug(f"Forecast cache updated for {cache_key}")
    
    def clear_cache(self):
        """Clear the forecast cache"""
        self._forecast_cache.clear()
        self.logger.debug("Forecast cache cleared")
    
    def get_forecast_models_info(self) -> Dict[str, Any]:
        """Get information about available forecasting models"""
        try:
            models_info = {
                "catboost": {
                    "name": "CatBoost",
                    "type": "Gradient Boosting",
                    "horizon": "24 hours",
                    "description": "Fast gradient boosting model for short-term forecasts",
                    "advantages": ["Fast training", "Handles categorical features", "Good for short horizons"],
                    "limitations": ["Limited to 24-hour horizon", "May not capture long-term patterns"]
                },
                "tcn_48h": {
                    "name": "TCN 48H",
                    "type": "Temporal Convolutional Network",
                    "horizon": "48 hours",
                    "description": "Deep learning model for medium-term forecasts",
                    "advantages": ["Captures temporal patterns", "Good for medium horizons", "Handles complex relationships"],
                    "limitations": ["Slower inference", "Requires more data", "Computationally intensive"]
                },
                "tcn_72h": {
                    "name": "TCN 72H",
                    "type": "Temporal Convolutional Network",
                    "horizon": "72 hours",
                    "description": "Deep learning model for long-term forecasts",
                    "advantages": ["Longest forecast horizon", "Captures complex temporal patterns", "Good for planning"],
                    "limitations": ["Highest uncertainty", "Requires most data", "Most computationally intensive"]
                }
            }
            
            return models_info
            
        except Exception as e:
            self.logger.error(f"Error getting forecast models info: {str(e)}")
            return {"error": str(e)}

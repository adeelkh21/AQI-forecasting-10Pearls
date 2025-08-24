"""
Data service for AQI and weather data management
"""
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils.paths import (
    MERGED_CSV, FEATURES_CSV, FORECAST_READY_CSV,
    get_latest_forecast_file
)
from ..utils.logging import get_logger, log_data_operation
from ..models.schemas import CurrentDataResponse, DataSourceStatus

logger = get_logger(__name__)

class DataService:
    """Service for managing AQI and weather data"""
    
    def __init__(self):
        self.logger = logger
        self._cached_data = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def get_current_data(self) -> Optional[CurrentDataResponse]:
        """Get current AQI and weather data"""
        try:
            # Check cache first
            if self._is_cache_valid():
                return self._cached_data
            
            # Load latest data
            current_data = self._load_latest_data()
            if current_data:
                self._update_cache(current_data)
                return current_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current data: {str(e)}")
            return None
    
    def get_data_sources_status(self) -> List[DataSourceStatus]:
        """Get status of all data sources"""
        try:
            sources = []
            
            # Check merged data source
            merged_status = self._check_file_status(MERGED_CSV, "merged_data")
            sources.append(merged_status)
            
            # Check features data source
            features_status = self._check_file_status(FEATURES_CSV, "features_data")
            sources.append(features_status)
            
            # Check forecast-ready data source
            forecast_status = self._check_file_status(FORECAST_READY_CSV, "forecast_ready_data")
            sources.append(forecast_status)
            
            return sources
            
        except Exception as e:
            self.logger.error(f"Error getting data sources status: {str(e)}")
            return []
    
    def get_latest_forecast_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the latest forecast"""
        try:
            latest_file = get_latest_forecast_file()
            if not latest_file:
                return None
            
            # Read forecast metadata
            forecast_df = pd.read_csv(latest_file)
            
            info = {
                "forecast_file": str(latest_file),
                "timestamp": latest_file.stat().st_mtime,
                "forecast_count": len(forecast_df),
                "horizon_hours": forecast_df['hours_ahead'].max() if 'hours_ahead' in forecast_df.columns else 0,
                "models_used": forecast_df['model_used'].unique().tolist() if 'model_used' in forecast_df.columns else [],
                "file_size_mb": round(latest_file.stat().st_size / (1024 * 1024), 2)
            }
            
            log_data_operation(self.logger, "forecast_info_retrieved", str(latest_file))
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting latest forecast info: {str(e)}")
            return None
    
    def get_data_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get data summary for the last N hours"""
        try:
            if not MERGED_CSV.exists():
                return {"error": "Merged data file not found"}
            
            # Read recent data
            df = pd.read_csv(MERGED_CSV)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_df = df[df['timestamp'] >= cutoff_time]
            
            if recent_df.empty:
                return {"error": f"No data found in the last {hours_back} hours"}
            
            # Calculate summary statistics
            summary = {
                "period_hours": hours_back,
                "data_points": len(recent_df),
                "start_time": recent_df['timestamp'].min().isoformat(),
                "end_time": recent_df['timestamp'].max().isoformat(),
                "aqi_stats": {
                    "mean": round(recent_df['AQI'].mean(), 2) if 'AQI' in recent_df.columns else None,
                    "min": recent_df['AQI'].min() if 'AQI' in recent_df.columns else None,
                    "max": recent_df['AQI'].max() if 'AQI' in recent_df.columns else None,
                    "std": round(recent_df['AQI'].std(), 2) if 'AQI' in recent_df.columns else None
                },
                "pollutants": self._get_pollutant_summary(recent_df),
                "weather": self._get_weather_summary(recent_df)
            }
            
            log_data_operation(self.logger, "data_summary_generated", str(MERGED_CSV), hours_back=hours_back)
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating data summary: {str(e)}")
            return {"error": str(e)}
    
    def _load_latest_data(self) -> Optional[CurrentDataResponse]:
        """Load the latest available data"""
        try:
            if not MERGED_CSV.exists():
                return None
            
            # Read the last row of merged data
            df = pd.read_csv(MERGED_CSV)
            if df.empty:
                return None
            
            latest_row = df.iloc[-1]
            timestamp = pd.to_datetime(latest_row['timestamp'])
            
            # Extract AQI and pollutants
            # Convert aqi_category (1-6) to actual AQI values
            aqi_category_num = float(latest_row.get('aqi_category', 1))
            aqi_value = self._convert_aqi_category_to_value(aqi_category_num)
            aqi_category = self._categorize_aqi(aqi_value)
            
            pollutants = {}
            # Map the actual column names from historical data
            pollutant_mapping = {
                'pm2_5': 'PM2.5',
                'pm10': 'PM10', 
                'no2': 'NO2',
                'so2': 'SO2',
                'co': 'CO',
                'o3': 'O3'
            }
            
            for col, display_name in pollutant_mapping.items():
                if col in latest_row and pd.notna(latest_row[col]):
                    pollutants[display_name] = float(latest_row[col])
            
            # Extract weather data
            weather = {}
            weather_columns = ['temperature', 'relative_humidity', 'pressure', 'wind_speed', 'wind_direction']
            for col in weather_columns:
                if col in latest_row and pd.notna(latest_row[col]):
                    # Map humidity column name
                    if col == 'relative_humidity':
                        weather['humidity'] = float(latest_row[col])
                    else:
                        weather[col] = float(latest_row[col])
            
            return CurrentDataResponse(
                success=True,
                message="Current data retrieved successfully",
                timestamp=timestamp,
                aqi_value=aqi_value,
                aqi_category=aqi_category,
                pollutants=pollutants,
                weather=weather,
                location="Default Location"  # Could be made configurable
            )
            
        except Exception as e:
            self.logger.error(f"Error loading latest data: {str(e)}")
            return None
    
    def _convert_aqi_category_to_value(self, aqi_category: float) -> float:
        """Convert AQI category (1-6) to actual AQI values"""
        # AQI categories: 1=Good, 2=Moderate, 3=Unhealthy for Sensitive Groups, 4=Unhealthy, 5=Very Unhealthy, 6=Hazardous
        category_ranges = {
            1: (0, 50),      # Good
            2: (51, 100),    # Moderate  
            3: (101, 150),   # Unhealthy for Sensitive Groups
            4: (151, 200),   # Unhealthy
            5: (201, 300),   # Very Unhealthy
            6: (301, 500)    # Hazardous
        }
        
        if aqi_category in category_ranges:
            min_val, max_val = category_ranges[aqi_category]
            # Return middle value of the range
            return (min_val + max_val) / 2
        else:
            # Default to moderate if category is unknown
            return 75.0
    
    def _categorize_aqi(self, aqi_value: float) -> str:
        """Categorize AQI value into health category"""
        if aqi_value <= 50:
            return "Good"
        elif aqi_value <= 100:
            return "Moderate"
        elif aqi_value <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi_value <= 200:
            return "Unhealthy"
        elif aqi_value <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def _check_file_status(self, file_path: Path, source_name: str) -> DataSourceStatus:
        """Check status of a data source file"""
        try:
            if not file_path.exists():
                return DataSourceStatus(
                    name=source_name,
                    status="missing",
                    last_update=None,
                    error_count=1,
                    last_error="File not found"
                )
            
            # Check file age
            file_age = datetime.now().timestamp() - file_path.stat().st_mtime
            file_age_hours = file_age / 3600
            
            if file_age_hours > 6:  # More than 6 hours old
                status = "stale"
            elif file_age_hours > 1:  # More than 1 hour old
                status = "delayed"
            else:
                status = "current"
            
            return DataSourceStatus(
                name=source_name,
                status=status,
                last_update=datetime.fromtimestamp(file_path.stat().st_mtime),
                error_count=0
            )
            
        except Exception as e:
            return DataSourceStatus(
                name=source_name,
                status="error",
                last_update=None,
                error_count=1,
                last_error=str(e)
            )
    
    def _get_pollutant_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for pollutants"""
        pollutant_columns = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
        summary = {}
        
        for col in pollutant_columns:
            if col in df.columns:
                col_data = df[col].dropna()
                if not col_data.empty:
                    summary[col] = {
                        "mean": round(col_data.mean(), 2),
                        "min": col_data.min(),
                        "max": col_data.max(),
                        "count": len(col_data)
                    }
        
        return summary
    
    def _get_weather_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for weather data"""
        weather_columns = ['temperature', 'humidity', 'pressure', 'wind_speed']
        summary = {}
        
        for col in weather_columns:
            if col in df.columns:
                col_data = df[col].dropna()
                if not col_data.empty:
                    summary[col] = {
                        "mean": round(col_data.mean(), 2),
                        "min": col_data.min(),
                        "max": col_data.max(),
                        "count": len(col_data)
                    }
        
        return summary
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if self._cached_data is None or self._cache_timestamp is None:
            return False
        
        cache_age = datetime.now().timestamp() - self._cache_timestamp
        return cache_age < self._cache_ttl
    
    def _update_cache(self, data: CurrentDataResponse):
        """Update the data cache"""
        self._cached_data = data
        self._cache_timestamp = datetime.now().timestamp()
        self.logger.debug("Data cache updated")
    
    def clear_cache(self):
        """Clear the data cache"""
        self._cached_data = None
        self._cache_timestamp = None
        self.logger.debug("Data cache cleared")

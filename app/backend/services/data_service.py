"""
Data service for AQI and weather data management
"""
import pandas as pd
import numpy as np
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
    
    def get_complete_aqi_timeline(self) -> Dict[str, Any]:
        """Get complete AQI timeline for the entire dataset"""
        try:
            if not MERGED_CSV.exists():
                return {"error": "Merged data file not found"}
            
            # Read complete dataset
            df = pd.read_csv(MERGED_CSV)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if df.empty:
                return {"error": "Dataset is empty"}
            
            print(f"📊 Processing {len(df):,} records for complete AQI timeline...")
            
            # Calculate AQI for each row
            aqi_timeline = []
            
            for idx, row in df.iterrows():
                if idx % 1000 == 0:  # Progress indicator
                    print(f"   Processing record {idx:,}/{len(df):,}")
                
                # Extract pollutants for this row
                pollutants_raw = {}
                pollutant_mapping = {
                    'pm2_5': 'pm2_5',
                    'pm10': 'pm10', 
                    'no2': 'no2',
                    'so2': 'so2',
                    'co': 'co',
                    'o3': 'o3'
                }
                
                for col, internal_name in pollutant_mapping.items():
                    if col in row and pd.notna(row[col]):
                        pollutants_raw[internal_name] = float(row[col])
                
                if pollutants_raw:
                    # Convert units to EPA standard
                    pollutants_converted = self._convert_units_to_epa_standard(pollutants_raw)
                    
                    # Calculate EPA AQI
                    aqi_value = self._calculate_epa_aqi(pollutants_converted)
                    
                    # Add to timeline
                    aqi_timeline.append({
                        "timestamp": row['timestamp'].isoformat(),
                        "aqi_value": round(aqi_value, 1),
                        "aqi_category": self._categorize_aqi(aqi_value),
                        "pollutants": pollutants_converted
                    })
            
            print(f"✅ AQI timeline calculated: {len(aqi_timeline):,} data points")
            
            # Calculate timeline statistics
            aqi_values = [point['aqi_value'] for point in aqi_timeline]
            
            timeline_data = {
                "success": True,
                "message": "Complete AQI timeline generated successfully",
                "total_records": len(aqi_timeline),
                "date_range": {
                    "start": df['timestamp'].min().isoformat(),
                    "end": df['timestamp'].max().isoformat()
                },
                "aqi_statistics": {
                    "min": min(aqi_values),
                    "max": max(aqi_values),
                    "mean": round(sum(aqi_values) / len(aqi_values), 1),
                    "median": sorted(aqi_values)[len(aqi_values) // 2]
                },
                "timeline": aqi_timeline
            }
            
            log_data_operation(self.logger, "aqi_timeline_generated", str(MERGED_CSV), record_count=len(aqi_timeline))
            return timeline_data
            
        except Exception as e:
            self.logger.error(f"Error generating AQI timeline: {str(e)}")
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
            
            # Extract pollutants first (we need these for EPA AQI calculation)
            pollutants_raw = {}
            pollutant_mapping = {
                'pm2_5': 'pm2_5',
                'pm10': 'pm10', 
                'no2': 'no2',
                'so2': 'so2',
                'co': 'co',
                'o3': 'o3'
            }
            
            for col, internal_name in pollutant_mapping.items():
                if col in latest_row and pd.notna(latest_row[col]):
                    pollutants_raw[internal_name] = float(latest_row[col])
            
            # CRITICAL: Convert units to EPA standard BEFORE AQI calculation
            pollutants_raw = self._convert_units_to_epa_standard(pollutants_raw)
            
            # Calculate EPA AQI using the same method as combined_data_pipeline.py
            if pollutants_raw:
                aqi_value = self._calculate_epa_aqi(pollutants_raw)
            else:
                # Fallback to category-based calculation if no pollutant data
                aqi_category_num = float(latest_row.get('aqi_category', 1))
                aqi_value = self._convert_aqi_category_to_value(aqi_category_num)
            
            aqi_category = self._categorize_aqi(aqi_value)
            
            # Convert pollutants to display format
            pollutants = {}
            for internal_name, display_name in pollutant_mapping.items():
                if internal_name in pollutants_raw:
                    pollutants[display_name.upper()] = pollutants_raw[internal_name]
            
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
    
    def _calculate_epa_aqi(self, pollutants: Dict[str, float]) -> float:
        """Calculate EPA AQI using EXACTLY the same method as phase2_data_preprocessing.py"""
        # EPA AQI breakpoints (EXACTLY as in preprocessing script)
        aqi_breakpoints = {
            'pm2_5': [  # µg/m³ (24-hr average) - truncate to 0.1 µg/m³
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 350.4, 301, 400),
                (350.5, 500.4, 401, 500)
            ],
            'pm10': [  # µg/m³ (24-hr average) - truncate to 1 µg/m³
                (0, 54, 0, 50),
                (55, 154, 51, 100),
                (155, 254, 101, 150),
                (255, 354, 151, 200),
                (355, 424, 201, 300),
                (425, 504, 301, 400),
                (505, 604, 401, 500)
            ],
            'o3_8hr': [  # ppb (8-hr average) - truncate to 1 ppb
                (0, 54, 0, 50),
                (55, 70, 51, 100),
                (71, 85, 101, 150),
                (86, 105, 151, 200),
                (106, 200, 201, 300)
            ],
            'o3_1hr': [  # ppb (1-hr average) - truncate to 1 ppb
                (125, 164, 101, 150),
                (165, 204, 151, 200),
                (205, 404, 201, 300),
                (405, 504, 301, 400),
                (505, 604, 401, 500)
            ],
            'co': [  # ppm (8-hr average) - truncate to 0.1 ppm
                (0.0, 4.4, 0, 50),
                (4.5, 9.4, 51, 100),
                (9.5, 12.4, 101, 150),
                (12.5, 15.4, 151, 200),
                (15.5, 30.4, 201, 300),
                (30.5, 40.4, 301, 400),
                (40.5, 50.4, 401, 500)
            ],
            'so2': [  # ppb (1-hr average) - truncate to 1 ppb
                (0, 35, 0, 50),
                (36, 75, 51, 100),
                (76, 185, 101, 150),
                (186, 304, 151, 200),
                (305, 604, 201, 300),
                (605, 804, 301, 400),
                (805, 1004, 401, 500)
            ],
            'no2': [  # ppb (1-hr average) - truncate to 1 ppb
                (0, 53, 0, 50),
                (54, 100, 51, 100),
                (101, 360, 101, 150),
                (361, 649, 151, 200),
                (650, 1249, 201, 300),
                (1250, 1649, 301, 400),
                (1650, 2049, 401, 500)
            ]
        }
        
        # EPA truncation rules (EXACTLY as in preprocessing script)
        truncation_rules = {
            'pm2_5': 0.1,      # µg/m³ to 0.1 µg/m³
            'pm10': 1.0,       # µg/m³ to 1 µg/m³
            'o3': 1.0,         # ppb to 1 ppb
            'co': 0.1,         # ppm to 0.1 ppm
            'so2': 1.0,        # ppb to 1 ppb
            'no2': 1.0         # ppb to 1 ppb
        }
        
        def apply_epa_truncation(concentration: float, pollutant: str) -> float:
            """Apply EPA truncation rules (EXACTLY as in preprocessing script)"""
            if pd.isna(concentration) or concentration < 0:
                return np.nan
            
            if pollutant == 'pm2_5':
                # Truncate to 0.1 µg/m³
                return np.floor(concentration * 10) / 10
            elif pollutant == 'pm10':
                # Truncate to 1 µg/m³
                return np.floor(concentration)
            elif pollutant == 'o3':
                # Truncate to 1 ppb
                return np.floor(concentration)
            elif pollutant == 'co':
                # Truncate to 0.1 ppm
                return np.floor(concentration * 10) / 10
            elif pollutant in ['so2', 'no2']:
                # Truncate to 1 ppb
                return np.floor(concentration)
            else:
                return concentration
        
        def calculate_pollutant_aqi(concentration: float, pollutant: str, averaging_period='1hr') -> float:
            """Calculate AQI for a specific pollutant using EPA breakpoints"""
            if pd.isna(concentration) or concentration < 0:
                return np.nan
            
            # Select appropriate breakpoints
            if pollutant == 'o3':
                if averaging_period == '8hr':
                    breakpoints = aqi_breakpoints['o3_8hr']
                else:
                    breakpoints = aqi_breakpoints['o3_1hr']
            else:
                breakpoints = aqi_breakpoints.get(pollutant, [])
            
            if not breakpoints:
                return np.nan
            
            # Find the appropriate breakpoint range
            for clow, chigh, ilow, ihigh in breakpoints:
                if clow <= concentration <= chigh:
                    # Apply EPA formula: I = (Ihigh - Ilow) / (Chigh - Clow) * (C - Clow) + Ilow
                    aqi = (ihigh - ilow) / (chigh - clow) * (concentration - clow) + ilow
                    return round(aqi)
            
            # If concentration is above the highest breakpoint, cap at 500
            if concentration > breakpoints[-1][1]:
                return 500
            
            # If concentration is below the lowest breakpoint, cap at 0
            if concentration < breakpoints[0][0]:
                return 0
            
            return np.nan
        
        # Calculate AQI for each pollutant with proper averaging and truncation
        aqi_values = {}
        
        # PM2.5 (24-hour average) - apply truncation
        if 'pm2_5' in pollutants:
            pm25_truncated = apply_epa_truncation(pollutants['pm2_5'], 'pm2_5')
            aqi_values['pm2_5_aqi'] = calculate_pollutant_aqi(pm25_truncated, 'pm2_5')
        
        # PM10 (24-hour average) - apply truncation
        if 'pm10' in pollutants:
            pm10_truncated = apply_epa_truncation(pollutants['pm10'], 'pm10')
            aqi_values['pm10_aqi'] = calculate_pollutant_aqi(pm10_truncated, 'pm10')
        
        # Ozone - implement EPA O3 selection rule (EXACTLY as in preprocessing script)
        if 'o3' in pollutants:
            o3_truncated = apply_epa_truncation(pollutants['o3'], 'o3')
            
            # For simplicity, we'll use the current value as both 8h and 1h
            # In reality, we should calculate 8h rolling average
            o3_8h_aqi = calculate_pollutant_aqi(o3_truncated, 'o3', '8hr')
            o3_1h_aqi = calculate_pollutant_aqi(o3_truncated, 'o3', '1hr')
            
            # EPA O3 selection rule: use the higher of 8-hour or 1-hour AQI
            # But 1-hour O3 must be ≥ 125 ppb to use 1-hour table
            o3_1h_eligible = o3_truncated >= 125
            
            # Select the appropriate AQI value
            o3_final_aqi = o3_1h_aqi if (o3_1h_eligible and o3_1h_aqi > o3_8h_aqi) else o3_8h_aqi
            aqi_values['o3_aqi'] = o3_final_aqi
        
        # CO (8-hour average) - apply truncation
        if 'co' in pollutants:
            co_truncated = apply_epa_truncation(pollutants['co'], 'co')
            aqi_values['co_aqi'] = calculate_pollutant_aqi(co_truncated, 'co')
        
        # SO2 (1-hour average) - apply truncation
        if 'so2' in pollutants:
            so2_truncated = apply_epa_truncation(pollutants['so2'], 'so2')
            aqi_values['so2_aqi'] = calculate_pollutant_aqi(so2_truncated, 'so2')
        
        # NO2 (1-hour average) - apply truncation
        if 'no2' in pollutants:
            no2_truncated = apply_epa_truncation(pollutants['no2'], 'no2')
            aqi_values['no2_aqi'] = calculate_pollutant_aqi(no2_truncated, 'no2')
        
        # Calculate overall AQI (maximum of all pollutant AQIs)
        if aqi_values:
            # Convert to list of values for max calculation
            aqi_list = list(aqi_values.values())
            overall_aqi = max(aq for aq in aqi_list if pd.notna(aq))
        else:
            overall_aqi = 0
        
        # Ensure AQI is capped at 500 (EPA standard)
        overall_aqi = min(overall_aqi, 500)
        
        return overall_aqi
    
    def _convert_units_to_epa_standard(self, pollutants: Dict[str, float]) -> Dict[str, float]:
        """Convert pollutant units from µg/m³ to EPA standard units (EXACTLY as in preprocessing script)"""
        # Molecular weights for unit conversion (g/mol) - same as preprocessing script
        molecular_weights = {
            'o3': 48.00,       # Ozone
            'no2': 46.01,      # Nitrogen dioxide
            'so2': 64.07,      # Sulfur dioxide
            'co': 28.01        # Carbon monoxide
        }
        
        # Standard molar volume at 25°C, 1 atm (L/mol) - same as preprocessing script
        molar_volume = 24.45
        
        converted_pollutants = {}
        
        # PM2.5 and PM10 are already in µg/m³, no conversion needed
        if 'pm2_5' in pollutants:
            converted_pollutants['pm2_5'] = pollutants['pm2_5']
        if 'pm10' in pollutants:
            converted_pollutants['pm10'] = pollutants['pm10']
        
        # Convert O3 from µg/m³ to ppb
        if 'o3' in pollutants:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            converted_pollutants['o3'] = (pollutants['o3'] * molar_volume) / molecular_weights['o3']
        
        # Convert NO2 from µg/m³ to ppb
        if 'no2' in pollutants:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            converted_pollutants['no2'] = (pollutants['no2'] * molar_volume) / molecular_weights['no2']
        
        # Convert SO2 from µg/m³ to ppb
        if 'so2' in pollutants:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            converted_pollutants['so2'] = (pollutants['so2'] * molar_volume) / molecular_weights['so2']
        
        # Convert CO from µg/m³ to ppm
        if 'co' in pollutants:
            # µg/m³ to ppm: ppm = (µg/m³ × 24.45) / (1000 × MW)
            converted_pollutants['co'] = (pollutants['co'] * molar_volume) / (1000 * molecular_weights['co'])
        
        return converted_pollutants
    
    def _convert_aqi_category_to_value(self, aqi_category: float) -> float:
        """Convert AQI category (1-6) to actual AQI values (fallback method)"""
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

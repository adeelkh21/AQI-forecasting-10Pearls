# Data access service - read latest AQI/weather/history from CSVs
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.paths import ROOT, FEATURES_CSV, MERGED_CSV
from ..utils.logging import get_logger

logger = get_logger('data_access')


async def get_latest_aqi() -> Optional[Dict[str, Any]]:
    """
    Get latest numeric AQI data from features CSV.
    
    Returns:
        Dict with timestamp and target_aqi_24h, or None if not available
    """
    try:
        if not FEATURES_CSV.exists():
            logger.warning("Features CSV not found")
            return None
        
        # Read the features CSV
        df = pd.read_csv(FEATURES_CSV)
        
        if df.empty:
            logger.warning("Features CSV is empty")
            return None
        
        # Check if required columns exist
        required_cols = ['timestamp', 'target_aqi_24h']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"Missing required columns: {missing_cols}")
            return None
        
        # Get the latest row
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest_row = df.loc[df['timestamp'].idxmax()]
        
        return {
            "timestamp": latest_row['timestamp'].isoformat(),
            "aqi_24h": float(latest_row['target_aqi_24h']) if pd.notna(latest_row['target_aqi_24h']) else None,
            "aqi_48h": float(latest_row.get('target_aqi_48h', None)) if 'target_aqi_48h' in latest_row and pd.notna(latest_row.get('target_aqi_48h')) else None,
            "aqi_72h": float(latest_row.get('target_aqi_72h', None)) if 'target_aqi_72h' in latest_row and pd.notna(latest_row.get('target_aqi_72h')) else None,
            "data_source": "features_csv"
        }
        
    except Exception as e:
        logger.error(f"Failed to get latest AQI: {e}")
        return None


async def get_aqi_history(hours: int = 168) -> List[Dict[str, Any]]:
    """
    Get historical AQI data for plotting.
    
    Args:
        hours: Number of hours to look back (default: 168 = 7 days)
        
    Returns:
        List of dicts with timestamp and AQI values
    """
    try:
        # Try to get data from features CSV first (for historical forecasting data)
        if FEATURES_CSV.exists():
            logger.info("Using features CSV for AQI history")
            try:
                df = pd.read_csv(FEATURES_CSV, usecols=['timestamp', 'target_aqi_24h', 'target_aqi_48h', 'target_aqi_72h'])
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    df = df.dropna(subset=['timestamp'])
                    
                    if not df.empty:
                        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                        df_filtered = df[df['timestamp'] >= cutoff_time]
                        
                        if not df_filtered.empty:
                            # Convert to list of dicts
                            result = []
                            for _, row in df_filtered.iterrows():
                                data_point = _create_aqi_data_point(row)
                                if data_point:
                                    result.append(data_point)
                            
                            logger.info(f"Retrieved {len(result)} AQI data points from features CSV for last {hours} hours")
                            return result
            except Exception as e:
                logger.warning(f"Failed to read features CSV: {e}")
        
        # Fallback to merged data for recent AQI values
        logger.info("Features CSV empty or missing recent data, using merged data as fallback")
        merged_csv = ROOT / "data_repositories" / "historical_data" / "processed" / "merged_data.csv"
        
        if not merged_csv.exists():
            logger.warning("Merged data CSV not found")
            return []
        
        # Read merged data and calculate AQI for recent timestamps
        try:
            df = pd.read_csv(merged_csv)
            if df.empty:
                logger.warning("Merged data CSV is empty")
                return []
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            
            if df.empty:
                logger.warning("No valid timestamps found in merged data")
                return []
            
            # Filter to recent hours
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            df_filtered = df[df['timestamp'] >= cutoff_time]
            
            if df_filtered.empty:
                logger.info(f"No data found in last {hours} hours. Available data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                return []
            
            # Calculate AQI from pollutant data if available
            result = []
            for _, row in df_filtered.iterrows():
                data_point = _create_aqi_data_point_from_merged(row, df.columns)
                if data_point:
                    result.append(data_point)
            
            logger.info(f"Retrieved {len(result)} AQI data points from merged data for last {hours} hours")
            return result
            
        except Exception as e:
            logger.error(f"Failed to read merged CSV: {e}")
            return []
        
    except Exception as e:
        logger.error(f"Failed to get AQI history: {e}")
        return []


async def get_latest_weather() -> Optional[Dict[str, Any]]:
    """
    Get latest weather data from merged dataset.
    
    Returns:
        Dict with latest weather information, or None if not available
    """
    try:
        if not MERGED_CSV.exists():
            logger.warning("Merged CSV not found")
            return None
        
        # Read the merged CSV
        df = pd.read_csv(MERGED_CSV)
        
        if df.empty:
            logger.warning("Merged CSV is empty")
            return None
        
        # Check if timestamp column exists
        if 'timestamp' not in df.columns:
            logger.warning("Timestamp column not found in merged CSV")
            return None
        
        # Get the latest row
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest_row = df.loc[df['timestamp'].idxmax()]
        
        # Extract weather-related columns (common weather fields)
        weather_data = {
            "timestamp": latest_row['timestamp'].isoformat(),
            "data_source": "merged_csv"
        }
        
        # Common weather columns to look for
        weather_columns = [
            'temperature', 'temp', 'humidity', 'hum', 'wind_speed', 'wind_speed_10m',
            'wind_direction', 'wind_dir', 'pressure', 'precipitation', 'rain',
            'solar_radiation', 'solar', 'uv_index', 'uv', 'visibility', 'vis'
        ]
        
        for col in weather_columns:
            if col in latest_row and pd.notna(latest_row[col]):
                try:
                    weather_data[col] = float(latest_row[col])
                except (ValueError, TypeError):
                    weather_data[col] = str(latest_row[col])
        
        # If no weather columns found, return basic info
        if len(weather_data) <= 2:  # Only timestamp and data_source
            logger.info("No weather columns found, returning basic timestamp info")
            return {
                "timestamp": weather_data["timestamp"],
                "data_source": weather_data["data_source"],
                "message": "No weather data columns found"
            }
        
        logger.info(f"Retrieved weather data with {len(weather_data)-2} weather fields")
        return weather_data
        
    except Exception as e:
        logger.error(f"Failed to get latest weather: {e}")
        return None


def get_data_summary() -> Dict[str, Any]:
    """
    Get summary information about available data.
    
    Returns:
        Dict with data availability and statistics
    """
    try:
        summary = {
            "features_csv": {
                "exists": FEATURES_CSV.exists(),
                "row_count": 0,
                "columns": [],
                "last_modified": None
            },
            "merged_csv": {
                "exists": MERGED_CSV.exists(),
                "row_count": 0,
                "columns": [],
                "last_modified": None
            }
        }
        
        # Check features CSV
        if FEATURES_CSV.exists():
            try:
                df = pd.read_csv(FEATURES_CSV)
                summary["features_csv"].update({
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "last_modified": datetime.fromtimestamp(FEATURES_CSV.stat().st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error reading features CSV: {e}")
        
        # Check merged CSV
        if MERGED_CSV.exists():
            try:
                df = pd.read_csv(MERGED_CSV)
                summary["merged_csv"].update({
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "last_modified": datetime.fromtimestamp(MERGED_CSV.stat().st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error reading merged CSV: {e}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        return {"error": str(e)}


def _create_aqi_data_point(row: pd.Series) -> Optional[Dict[str, Any]]:
    """
    Create AQI data point from features CSV row.
    
    Args:
        row: DataFrame row
        
    Returns:
        AQI data point dict or None
    """
    try:
        timestamp = row['timestamp']
        if pd.isna(timestamp):
            return None
        
        aqi_24h = row.get('target_aqi_24h')
        if pd.isna(aqi_24h):
            return None
        
        data_point = {
            "timestamp": timestamp.isoformat(),
            "aqi_24h": float(aqi_24h)
        }
        
        # Add 48h and 72h if available
        for horizon in ['target_aqi_48h', 'target_aqi_72h']:
            if horizon in row and pd.notna(row[horizon]):
                key = horizon.replace('target_', '')
                data_point[key] = float(row[horizon])
        
        return data_point
        
    except Exception as e:
        logger.warning(f"Failed to create AQI data point: {e}")
        return None


def _create_aqi_data_point_from_merged(row: pd.Series, columns: pd.Index) -> Optional[Dict[str, Any]]:
    """
    Create AQI data point from merged CSV row.
    
    Args:
        row: DataFrame row
        columns: Available columns
        
    Returns:
        AQI data point dict or None
    """
    try:
        timestamp = row['timestamp']
        if pd.isna(timestamp):
            return None
        
        # Try to get AQI from existing columns first
        aqi_value = None
        for aqi_col in ['aqi', 'numerical_aqi', 'target_aqi_24h']:
            if aqi_col in columns and pd.notna(row.get(aqi_col)):
                aqi_value = float(row[aqi_col])
                break
        
        # If no AQI column, calculate from PM2.5 (simplified)
        if aqi_value is None and 'pm2_5' in columns and pd.notna(row.get('pm2_5')):
            pm25 = float(row['pm2_5'])
            aqi_value = _calculate_aqi_from_pm25(pm25)
        
        if aqi_value is None:
            return None
        
        return {
            "timestamp": timestamp.isoformat(),
            "aqi_24h": aqi_value
        }
        
    except Exception as e:
        logger.warning(f"Failed to create AQI data point from merged data: {e}")
        return None


def _calculate_aqi_from_pm25(pm25: float) -> Optional[float]:
    """
    Calculate AQI from PM2.5 using EPA breakpoints.
    
    Args:
        pm25: PM2.5 concentration in µg/m³
        
    Returns:
        AQI value or None if calculation fails
    """
    try:
        # EPA PM2.5 breakpoints (µg/m³)
        if pm25 <= 12.0:
            aqi = (50 - 0) / (12.0 - 0) * (pm25 - 0) + 0
        elif pm25 <= 35.4:
            aqi = (100 - 51) / (35.4 - 12.1) * (pm25 - 12.1) + 51
        elif pm25 <= 55.4:
            aqi = (150 - 101) / (55.4 - 35.5) * (pm25 - 35.5) + 101
        elif pm25 <= 150.4:
            aqi = (200 - 151) / (150.4 - 55.5) * (pm25 - 55.5) + 151
        elif pm25 <= 250.4:
            aqi = (300 - 201) / (250.4 - 150.5) * (pm25 - 150.5) + 201
        elif pm25 <= 350.4:
            aqi = (400 - 301) / (350.4 - 250.5) * (pm25 - 250.5) + 301
        else:
            aqi = 500
        
        return round(aqi)
        
    except Exception as e:
        logger.warning(f"Failed to calculate AQI from PM2.5: {e}")
        return None

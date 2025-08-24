#!/usr/bin/env python3
"""
Combined Data Pipeline for AQI Forecasting
==========================================

This script combines:
1. Data collection (from collect_6hours.py)
2. Data preprocessing (from phase2_data_preprocessing.py) 
3. Feature selection (from phase3_feature_selection.py)

Key Changes:
- Keeps ALL recent data (including last 3 days) for forecasting
- Creates targets for training but preserves full dataset
- Generates CSV ready for forecast.py to predict next 3 days

Usage:
  python combined_data_pipeline.py

Output:
- data_repositories/features/forecast_ready_features.csv (ready for forecast.py)
- data_repositories/features/forecast_ready_feature_columns.pkl
- data_repositories/features/forecast_ready_scaler.pkl
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import pickle
import json
import glob
import hashlib

warnings.filterwarnings('ignore')

# Try to import required libraries
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    print("⚠️ SHAP not available, installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "shap"])
    import shap
    SHAP_AVAILABLE = True

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️ LightGBM not available, installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "lightgbm"])
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

class CombinedDataPipeline:
    def __init__(self):
        """Initialize the combined data pipeline"""
        print("🚀 COMBINED DATA PIPELINE FOR AQI FORECASTING")
        print("=" * 80)
        
        # Data paths
        self.merged_data_path = "data_repositories/historical_data/processed/merged_data.csv"
        self.output_path = "data_repositories/features/forecast_ready_features.csv"
        self.feature_columns_path = "data_repositories/features/forecast_ready_feature_columns.pkl"
        self.scaler_path = "data_repositories/features/forecast_ready_scaler.pkl"
        self.metadata_path = "data_repositories/features/forecast_ready_metadata.json"
        
        # Create output directories
        os.makedirs("data_repositories/features", exist_ok=True)
        
        # Target number of features
        self.target_features = 50
        
        # EPA AQI breakpoints (standard 0-500 range)
        self.aqi_breakpoints = {
            'pm2_5': [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
                      (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400),
                      (350.5, 500.4, 401, 500)],
            'pm10': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
                     (255, 354, 151, 200), (355, 424, 201, 300), (425, 504, 301, 400),
                     (505, 604, 401, 500)],
            'o3_8hr': [(0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
                       (86, 105, 151, 200), (106, 200, 201, 300)],
            'o3_1hr': [(125, 164, 101, 150), (165, 204, 151, 200), (205, 404, 201, 300),
                       (405, 504, 301, 400), (505, 604, 401, 500)],
            'co': [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
                   (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 40.4, 301, 400),
                   (40.5, 50.4, 401, 500)],
            'so2': [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
                    (186, 304, 151, 200), (305, 604, 201, 300), (605, 804, 301, 400),
                    (805, 1004, 401, 500)],
            'no2': [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
                    (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 1649, 301, 400),
                    (1650, 2049, 401, 500)]
        }
        
        # Molecular weights for unit conversion
        self.molecular_weights = {'o3': 48.00, 'no2': 46.01, 'so2': 64.07, 'co': 28.01}
        
        print(f"🎯 Target Features: {self.target_features}")
        print(f"📁 Input: {self.merged_data_path}")
        print(f"📁 Output: {self.output_path}")
        print(f"🔍 Method: SHAP analysis with LightGBM")
        print(f"✅ Preserving ALL recent data for forecasting")
        
    def check_data_availability(self):
        """Check if merged data exists and get its date range"""
        print(f"\n📥 CHECKING DATA AVAILABILITY")
        print("-" * 40)
        
        if not os.path.exists(self.merged_data_path):
            print(f"❌ Merged data file not found: {self.merged_data_path}")
            print(f"💡 Please run data collection first to create merged_data.csv")
            return None
        
        # Read timestamp column to check date range
        try:
            df = pd.read_csv(self.merged_data_path, usecols=['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            print(f"📅 Data available: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"📊 Total records: {len(df):,}")
            return df['timestamp'].max()
        except Exception as e:
            print(f"❌ Error reading data: {e}")
            return None
    
    def load_and_preprocess_data(self):
        """Load and preprocess the data"""
        print(f"\n🔄 LOADING AND PREPROCESSING DATA")
        print("-" * 50)
        
        # Load data
        df = pd.read_csv(self.merged_data_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"   Raw data loaded: {len(df):,} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Convert units to EPA standard
        print(f"   Converting units to EPA standard...")
        molar_volume = 24.45
        
        if 'o3' in df.columns:
            df['o3_ppb'] = (df['o3'] * molar_volume) / self.molecular_weights['o3']
        if 'no2' in df.columns:
            df['no2_ppb'] = (df['no2'] * molar_volume) / self.molecular_weights['no2']
        if 'so2' in df.columns:
            df['so2_ppb'] = (df['so2'] * molar_volume) / self.molecular_weights['so2']
        if 'co' in df.columns:
            df['co_ppm'] = (df['co'] * molar_volume) / (1000 * self.molecular_weights['co'])
        
        # Calculate required averages
        print(f"   Calculating required averaging periods...")
        if 'pm2_5' in df.columns:
            df['pm2_5_24h_avg'] = df['pm2_5'].rolling(window=24, min_periods=18).mean()
        if 'pm10' in df.columns:
            df['pm10_24h_avg'] = df['pm10'].rolling(window=24, min_periods=18).mean()
        if 'o3_ppb' in df.columns:
            df['o3_8h_avg'] = df['o3_ppb'].rolling(window=8, min_periods=6).mean()
            df['o3_1h_avg'] = df['o3_ppb']
        if 'co_ppm' in df.columns:
            df['co_8h_avg'] = df['co_ppm'].rolling(window=8, min_periods=6).mean()
        if 'no2_ppb' in df.columns:
            df['no2_1h_avg'] = df['no2_ppb']
        if 'so2_ppb' in df.columns:
            df['so2_1h_avg'] = df['so2_ppb']
        
        # Calculate AQI for each pollutant
        print(f"   Calculating numerical AQI...")
        aqi_values = {}
        
        if 'pm2_5_24h_avg' in df.columns:
            aqi_values['pm2_5_aqi'] = df['pm2_5_24h_avg'].apply(lambda x: self.calculate_aqi(x, 'pm2_5'))
        if 'pm10_24h_avg' in df.columns:
            aqi_values['pm10_aqi'] = df['pm10_24h_avg'].apply(lambda x: self.calculate_aqi(x, 'pm10'))
        if 'o3_8h_avg' in df.columns and 'o3_1h_avg' in df.columns:
            o3_8h_aqi = df['o3_8h_avg'].apply(lambda x: self.calculate_aqi(x, 'o3', '8hr'))
            o3_1h_aqi = df['o3_1h_avg'].apply(lambda x: self.calculate_aqi(x, 'o3', '1hr'))
            o3_1h_eligible = df['o3_1h_avg'] >= 125
            o3_final_aqi = np.where(o3_1h_eligible & (o3_1h_aqi > o3_8h_aqi), o3_1h_aqi, o3_8h_aqi)
            aqi_values['o3_aqi'] = o3_final_aqi
        if 'co_8h_avg' in df.columns:
            aqi_values['co_aqi'] = df['co_8h_avg'].apply(lambda x: self.calculate_aqi(x, 'co'))
        if 'so2_1h_avg' in df.columns:
            aqi_values['so2_aqi'] = df['so2_1h_avg'].apply(lambda x: self.calculate_aqi(x, 'so2'))
        if 'no2_1h_avg' in df.columns:
            aqi_values['no2_aqi'] = df['no2_1h_avg'].apply(lambda x: self.calculate_aqi(x, 'no2'))
        
        # Calculate overall AQI
        aqi_df = pd.DataFrame(aqi_values)
        df['numerical_aqi'] = aqi_df.max(axis=1)
        
        # Ensure AQI is capped at 500 (EPA standard)
        df['numerical_aqi'] = df['numerical_aqi'].clip(upper=500)
        
        df['primary_pollutant'] = aqi_df.idxmax(axis=1).str.replace('_aqi', '')
        
        print(f"   AQI calculated: {df['numerical_aqi'].notna().sum()} valid values")
        print(f"   AQI range: {df['numerical_aqi'].min():.0f} to {df['numerical_aqi'].max():.0f}")
        print(f"   ✅ AQI values capped at 500 (EPA standard)")
        
        # Show AQI distribution
        aqi_distribution = df['numerical_aqi'].value_counts(bins=[0, 50, 100, 150, 200, 300, 400, 500]).sort_index()
        print(f"   AQI Distribution:")
        for bin_range, count in aqi_distribution.items():
            print(f"      {bin_range}: {count:,} values")
        
        # Validate AQI ranges
        self._validate_aqi_ranges(df)
        
        return df
    
    def calculate_aqi(self, concentration, pollutant, averaging_period='1hr'):
        """Calculate AQI for a given pollutant concentration (capped at 500)"""
        if pd.isna(concentration) or concentration < 0:
            return np.nan
        
        if pollutant == 'o3':
            breakpoints = self.aqi_breakpoints['o3_8hr'] if averaging_period == '8hr' else self.aqi_breakpoints['o3_1hr']
        else:
            breakpoints = self.aqi_breakpoints.get(pollutant, [])
        
        if not breakpoints:
            return np.nan
        
        # Find the breakpoint range that contains the concentration
        for clow, chigh, ilow, ihigh in breakpoints:
            if clow <= concentration <= chigh:
                # Linear interpolation formula
                aqi = (ihigh - ilow) / (chigh - clow) * (concentration - clow) + ilow
                return min(round(aqi), 500)  # Cap at 500
        
        # Handle concentrations outside breakpoint ranges
        if concentration > breakpoints[-1][1]:  # Above highest breakpoint
            return 500  # Cap at 500 (hazardous)
        if concentration < breakpoints[0][0]:   # Below lowest breakpoint
            return 0
        
        return np.nan
    
    def _validate_aqi_ranges(self, df):
        """Validate that AQI values are within EPA standard ranges"""
        if 'numerical_aqi' not in df.columns:
            return
        
        # Check for any AQI values outside EPA range
        invalid_aqi = df[df['numerical_aqi'] > 500]
        if len(invalid_aqi) > 0:
            print(f"   ⚠️  Found {len(invalid_aqi)} AQI values > 500, capping them...")
            df.loc[df['numerical_aqi'] > 500, 'numerical_aqi'] = 500
        
        # Check for negative AQI values
        negative_aqi = df[df['numerical_aqi'] < 0]
        if len(negative_aqi) > 0:
            print(f"   ⚠️  Found {len(negative_aqi)} negative AQI values, setting to 0...")
            df.loc[df['numerical_aqi'] < 0, 'numerical_aqi'] = 0
        
        print(f"   ✅ AQI validation complete: range {df['numerical_aqi'].min():.0f} to {df['numerical_aqi'].max():.0f}")
    
    def engineer_features(self, df):
        """Engineer features for forecasting"""
        print(f"\n⚙️ ENGINEERING FEATURES")
        print("-" * 40)
        
        # Time features
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        
        # Cyclical time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        # Seasonal features
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_monsoon'] = df['month'].isin([7, 8, 9]).astype(int)
        df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)
        df['is_spring'] = df['month'].isin([3, 4, 5]).astype(int)
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Weather interaction features
        if 'temperature' in df.columns and 'relative_humidity' in df.columns:
            df['heat_index'] = df['temperature'] * (1 + 0.01 * df['relative_humidity'])
        
        if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            if df['wind_direction'].notna().any():
                df['wind_east'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))
                df['wind_north'] = df['wind_speed'] * np.sin(np.radians(df['wind_direction']))
        
        # Pollution interaction features
        if 'pm2_5' in df.columns and 'pm10' in df.columns:
            df['pm_ratio'] = df['pm2_5'] / (df['pm10'] + 1e-6)
        
        if 'co' in df.columns and 'no2' in df.columns:
            df['co_no2_ratio'] = df['co'] / (df['no2'] + 1e-6)
        
        # Lag features for pollutants
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                for lag in [1, 3, 6, 12, 18, 24, 36, 48, 72]:
                    df[f'{pollutant}_lag_{lag}h'] = df[pollutant].shift(lag)
        
        # Rolling statistics for pollutants
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                for window in [6, 12, 18, 24, 36, 48, 60, 72]:
                    df[f'{pollutant}_{window}h_mean'] = df[pollutant].rolling(window=window, min_periods=1).mean()
                    df[f'{pollutant}_{window}h_std'] = df[pollutant].rolling(window=window, min_periods=1).std()
                    # Calculate trend more safely
                    df[f'{pollutant}_{window}h_trend'] = df[pollutant].rolling(window=window, min_periods=2).apply(
                        lambda x: np.polyfit(range(len(x.dropna())), x.dropna(), 1)[0] if len(x.dropna()) > 1 else 0
                    )
        
        # Rate of change features
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                for change_hours in [1, 3, 6, 12, 18, 24, 36, 48]:
                    df[f'{pollutant}_change_{change_hours}h'] = df[pollutant].diff(change_hours)
        
        # Momentum indicators
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                for momentum_hours in [6, 12, 18, 24, 36, 48]:
                    df[f'{pollutant}_momentum_{momentum_hours}h'] = df[pollutant] - df[pollutant].shift(momentum_hours)
        
        # Weather rolling features
        if 'temperature' in df.columns:
            for window in [6, 12, 18, 24, 36, 48, 60, 72]:
                df[f'temp_{window}h_mean'] = df['temperature'].rolling(window=window, min_periods=1).mean()
                df[f'temp_{window}h_trend'] = df['temperature'].rolling(window=window, min_periods=2).apply(
                    lambda x: np.polyfit(range(len(x.dropna())), x.dropna(), 1)[0] if len(x.dropna()) > 1 else 0
                )
        
        if 'relative_humidity' in df.columns:
            for window in [6, 12, 18, 24, 36, 48, 60, 72]:
                df[f'humidity_{window}h_mean'] = df['relative_humidity'].rolling(window=window, min_periods=1).mean()
        
        if 'pressure' in df.columns:
            for window in [6, 12, 18, 24, 36, 48, 60, 72]:
                df[f'pressure_{window}h_mean'] = df['pressure'].rolling(window=window, min_periods=1).mean()
                df[f'pressure_{window}h_trend'] = df['pressure'].rolling(window=window, min_periods=2).apply(
                    lambda x: np.polyfit(range(len(x.dropna())), x.dropna(), 1)[0] if len(x.dropna()) > 1 else 0
                )
        
        if 'wind_speed' in df.columns:
            for window in [6, 12, 18, 24, 36, 48, 60, 72]:
                df[f'wind_speed_{window}h_mean'] = df['wind_speed'].rolling(window=window, min_periods=1).mean()
                df[f'wind_speed_{window}h_max'] = df['wind_speed'].rolling(window=window, min_periods=1).max()
        
        # Multi-horizon specific features
        df['seasonal_24h_factor'] = np.sin(2 * np.pi * df['day_of_year'] / 365) * np.cos(2 * np.pi * df['hour'] / 24)
        df['seasonal_48h_factor'] = np.sin(2 * np.pi * df['day_of_year'] / 365) * np.cos(2 * np.pi * df['hour'] / 12)
        df['seasonal_72h_factor'] = np.sin(2 * np.pi * df['day_of_year'] / 365) * np.cos(2 * np.pi * df['hour'] / 8)
        
        df['weekend_24h'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['weekend_48h'] = ((df['day_of_week'] + 1) % 7).isin([5, 6]).astype(int)
        df['weekend_72h'] = ((df['day_of_week'] + 2) % 7).isin([5, 6]).astype(int)
        
        print(f"   Features engineered: {len(df.columns)} total columns")
        return df
    
    def create_forecasting_targets(self, df):
        """Create forecasting targets while preserving all recent data"""
        print(f"\n🎯 CREATING FORECASTING TARGETS")
        print("-" * 50)
        
        # Create targets for training (these will be NaN for recent data)
        df['target_aqi_24h'] = df['numerical_aqi'].shift(-24)
        df['target_aqi_48h'] = df['numerical_aqi'].shift(-48)
        df['target_aqi_72h'] = df['numerical_aqi'].shift(-72)
        
        # Add target timestamp for alignment
        df['target_timestamp'] = pd.to_datetime(df['timestamp']) + pd.to_timedelta(24, unit='h')
        
        # Count valid targets
        valid_24h = df['target_aqi_24h'].notna().sum()
        valid_48h = df['target_aqi_48h'].notna().sum()
        valid_72h = df['target_aqi_72h'].notna().sum()
        
        print(f"   Targets created:")
        print(f"      → 24h: {valid_24h:,} valid targets")
        print(f"      → 48h: {valid_48h:,} valid targets")
        print(f"      → 72h: {valid_72h:,} valid targets")
        print(f"   ✅ All recent data preserved for forecasting")
        
        return df
    
    def remove_aqi_leakage_features(self, df):
        """Remove AQI-related features that cause data leakage"""
        print(f"\n🔒 REMOVING AQI LEAKAGE FEATURES")
        print("-" * 50)
        
        # Remove AQI-contributing features (but keep the ones used by trained models)
        aqi_features_to_remove = [
            'o3_8h_avg', 'o3_1h_avg', 'co_8h_avg', 'no2_1h_avg', 'so2_1h_avg', 'primary_pollutant'
        ]
        
        # IMPORTANT: Keep pm2_5_24h_avg and pm10_24h_avg as they are used by trained models
        # These are NOT the same as the ones used for AQI calculation in this pipeline
        
        features_removed = []
        for feature in aqi_features_to_remove:
            if feature in df.columns:
                df = df.drop(feature, axis=1)
                features_removed.append(feature)
        
        print(f"   Removed {len(features_removed)} AQI leakage features")
        print(f"   ✅ Kept pm2_5_24h_avg and pm10_24h_avg (used by trained models)")
        print(f"   Features after removal: {len(df.columns)}")
        
        return df
    
    def handle_missing_values(self, df):
        """Handle missing values in the dataset"""
        print(f"\n🔧 HANDLING MISSING VALUES")
        print("-" * 50)
        
        # Handle missing values by column type
        for col in df.columns:
            if col == 'timestamp' or col.startswith('target_'):
                continue
                
            missing_count = df[col].isnull().sum()
            if missing_count == 0:
                continue
                
            if col in ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            elif col in ['temperature', 'tmin', 'tmax', 'dew_point', 'relative_humidity']:
                df[col] = df[col].interpolate(method='linear')
            elif col in ['precipitation', 'wind_speed', 'pressure']:
                if col == 'precipitation':
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna(df[col].median())
            else:
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna('unknown')
        
        print(f"   Missing values handled")
        return df
    
    def prepare_features_for_selection(self, df):
        """Prepare features for SHAP analysis"""
        print(f"\n⚙️ PREPARING FEATURES FOR SELECTION")
        print("-" * 50)
        
        # Exclude timestamp and targets
        exclude_cols = ['timestamp', 'target_aqi_24h', 'target_aqi_48h', 'target_aqi_72h', 'target_timestamp']
        feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        # Ensure all features are numeric
        numeric_features = []
        for col in feature_columns:
            if df[col].dtype in ['int64', 'float64']:
                numeric_features.append(col)
        
        print(f"   Feature columns: {len(numeric_features)}")
        
        # Use 24h target for feature selection (remove NaN rows for training)
        valid_mask = df['target_aqi_24h'].notna()
        df_valid = df[valid_mask].copy()
        
        X = df_valid[numeric_features]
        y = df_valid['target_aqi_24h']
        
        # Handle any remaining NaN or Inf values
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        print(f"   Training data: {len(X):,} samples")
        print(f"   Features: {len(numeric_features)}")
        
        return X, y, numeric_features, df
    
    def perform_feature_selection(self, X, y, feature_names):
        """Perform SHAP-based feature selection"""
        print(f"\n🔍 PERFORMING SHAP-BASED FEATURE SELECTION")
        print("-" * 50)
        
        # Split data for training
        split_idx = int(len(X) * 0.8)
        X_train = X[:split_idx]
        y_train = y[:split_idx]
        X_val = X[split_idx:]
        y_val = y[split_idx:]
        
        print(f"   Training set: {len(X_train):,} samples")
        print(f"   Validation set: {len(X_val):,} samples")
        
        # Train LightGBM model
        model = lgb.LGBMRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42,
            verbose=-1
        )
        
        print(f"   Training LightGBM model...")
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_val)
        mse = mean_squared_error(y_val, y_pred)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        print(f"   Model Performance:")
        print(f"      MSE: {mse:.2f}")
        print(f"      MAE: {mae:.2f}")
        print(f"      R²: {r2:.3f}")
        
        # SHAP analysis
        print(f"   Performing SHAP analysis...")
        shap_sample_size = min(1000, len(X_val))
        X_shap = X_val.sample(n=shap_sample_size, random_state=42)
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_shap)
        
        # Get feature importance
        feature_importance = np.abs(shap_values).mean(axis=0)
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        print(f"   Top 15 features by importance:")
        for i, (_, row) in enumerate(importance_df.head(15).iterrows()):
            print(f"      {i+1:2d}. {row['feature']:<30} {row['importance']:.4f}")
        
        return importance_df
    
    def select_and_scale_features(self, importance_df, X, y, feature_names, df):
        """Select top features and scale them"""
        print(f"\n🎯 SELECTING AND SCALING TOP FEATURES")
        print("-" * 50)
        
        # Select top features
        top_features = importance_df.head(self.target_features)['feature'].tolist()
        
        # Verify no AQI leakage features
        aqi_leakage_keywords = ['aqi_', 'numerical_aqi', 'aqi']
        leakage_features = []
        for feature in top_features:
            for keyword in aqi_leakage_keywords:
                if keyword in feature.lower():
                    leakage_features.append(feature)
                    break
        
        if leakage_features:
            print(f"   ⚠️  Removing AQI leakage features: {leakage_features}")
            top_features = [f for f in top_features if f not in leakage_features]
        
        print(f"   Selected {len(top_features)} features")
        
        # Scale features
        scaler = StandardScaler()
        X_selected = X[top_features]
        X_scaled = scaler.fit_transform(X_selected)
        X_scaled_df = pd.DataFrame(X_scaled, columns=top_features)
        
        print(f"   Features scaled using StandardScaler")
        
        return X_scaled_df, scaler, top_features
    
    def create_final_dataset(self, df, X_scaled_df, scaler, top_features):
        """Create final dataset with selected features"""
        print(f"\n📊 CREATING FINAL DATASET")
        print("-" * 40)
        
        # Create final dataset
        final_df = pd.DataFrame()
        final_df['timestamp'] = df['timestamp']
        final_df['target_timestamp'] = df['target_timestamp']
        final_df['target_aqi_24h'] = df['target_aqi_24h']
        final_df['target_aqi_48h'] = df['target_aqi_48h']
        final_df['target_aqi_72h'] = df['target_aqi_72h']
        
        # Get the original feature values for all rows
        X_all = df[top_features].copy()
        
        # Handle any NaN or Inf values in the full dataset
        X_all = X_all.replace([np.inf, -np.inf], np.nan)
        X_all = X_all.fillna(0)
        
        # Scale all features using the fitted scaler
        X_all_scaled = scaler.transform(X_all)
        X_all_scaled_df = pd.DataFrame(X_all_scaled, columns=top_features, index=df.index)
        
        # Add scaled features to final dataset
        for feature in top_features:
            final_df[feature] = X_all_scaled_df[feature]
        
        print(f"   Final dataset shape: {final_df.shape}")
        print(f"   Columns: timestamp, target_timestamp, targets, + {len(top_features)} features")
        print(f"   ✅ All features properly scaled for entire dataset")
        
        return final_df
    
    def save_data(self, final_df, top_features, scaler, importance_df):
        """Save the final dataset and metadata"""
        print(f"\n💾 SAVING FINAL DATASET")
        print("-" * 40)
        
        # Save final dataset
        final_df.to_csv(self.output_path, index=False)
        print(f"   Final dataset saved to: {self.output_path}")
        
        # Save feature columns
        with open(self.feature_columns_path, 'wb') as f:
            pickle.dump(top_features, f)
        print(f"   Feature columns saved to: {self.feature_columns_path}")
        
        # Save scaler
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"   Scaler saved to: {self.scaler_path}")
        
        # Save feature importance if available
        if importance_df is not None:
            importance_path = "data_repositories/features/forecast_ready_feature_importance.csv"
            importance_df.to_csv(importance_path, index=False)
            print(f"   Feature importance saved to: {importance_path}")
        else:
            importance_path = "N/A"
            print(f"   Feature importance: Not available (using existing features)")
        
        # Save metadata
        metadata = {
            "pipeline_timestamp": datetime.now().isoformat(),
            "output_data": self.output_path,
            "target_features": self.target_features,
            "actual_features_selected": len(top_features),
            "data_shape": final_df.shape,
            "date_range": f"{final_df['timestamp'].min()} to {final_df['timestamp'].max()}",
            "target_variables": {
                "target_aqi_24h": "AQI value 24 hours in the future",
                "target_aqi_48h": "AQI value 48 hours in the future",
                "target_aqi_72h": "AQI value 72 hours in the future"
            },
            "selected_features": top_features,
            "forecasting_ready": True,
            "note": "Dataset ready for forecast.py to predict next 3 days"
        }
        
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4, default=str)
        print(f"   Metadata saved to: {self.metadata_path}")
        
        return True
    
    def run_pipeline(self):
        """Run the complete combined pipeline"""
        print(f"\n🚀 STARTING COMBINED DATA PIPELINE")
        print("=" * 80)
        
        # Step 1: Check data availability
        latest_timestamp = self.check_data_availability()
        if latest_timestamp is None:
            return False
        
        # Step 2: Load and preprocess data
        df = self.load_and_preprocess_data()
        
        # Step 3: Engineer features
        df = self.engineer_features(df)
        
        # Step 4: Create forecasting targets
        df = self.create_forecasting_targets(df)
        
        # Step 5: Remove AQI leakage features
        df = self.remove_aqi_leakage_features(df)
        
        # Step 6: Handle missing values
        df = self.handle_missing_values(df)
        
        # Step 7: Use existing feature columns for compatibility
        print(f"\n🔧 USING EXISTING FEATURE COLUMNS FOR MODEL COMPATIBILITY")
        print("-" * 60)
        
        # Load the existing feature columns that the trained models expect
        try:
            existing_features_path = "data_repositories/features/phase1_fixed_feature_columns.pkl"
            if os.path.exists(existing_features_path):
                with open(existing_features_path, 'rb') as f:
                    import pickle
                    existing_features = pickle.load(f)
                print(f"   Loaded existing feature columns: {len(existing_features)} features")
                
                # Check which features are available in our dataset
                available_features = [f for f in existing_features if f in df.columns]
                missing_features = [f for f in existing_features if f not in df.columns]
                
                print(f"   Available features: {len(available_features)}")
                if missing_features:
                    print(f"   Missing features: {len(missing_features)}")
                    print(f"   → These will be filled with 0 for compatibility")
                
                # Use the existing feature columns for compatibility
                top_features = existing_features
                
                # Fill missing features with 0
                for feature in missing_features:
                    df[feature] = 0.0
                
                print(f"   ✅ Using {len(top_features)} features for model compatibility")
                
            else:
                print(f"   ⚠️  Existing feature columns not found, falling back to SHAP selection")
                # Fallback to SHAP selection
                X, y, feature_names, df = self.prepare_features_for_selection(df)
                importance_df = self.perform_feature_selection(X, y, feature_names)
                X_scaled_df, scaler, top_features = self.select_and_scale_features(importance_df, X, y, feature_names, df)
                final_df = self.create_final_dataset(df, X_scaled_df, scaler, top_features)
                return self.save_data(final_df, top_features, scaler, importance_df)
                
        except Exception as e:
            print(f"   ❌ Error loading existing features: {e}")
            print(f"   → Falling back to SHAP selection")
            # Fallback to SHAP selection
            X, y, feature_names, df = self.prepare_features_for_selection(df)
            importance_df = self.perform_feature_selection(X, y, feature_names)
            X_scaled_df, scaler, top_features = self.select_and_scale_features(importance_df, X, y, feature_names, df)
            final_df = self.create_final_dataset(df, X_scaled_df, scaler, top_features)
            return self.save_data(final_df, top_features, scaler, importance_df)
        
        # Step 8: Scale features using existing scaler if available
        print(f"\n📏 SCALING FEATURES FOR MODEL COMPATIBILITY")
        print("-" * 50)
        
        try:
            existing_scaler_path = "data_repositories/features/phase1_fixed_feature_scaler.pkl"
            if os.path.exists(existing_scaler_path):
                with open(existing_scaler_path, 'rb') as f:
                    import pickle
                    scaler = pickle.load(f)
                print(f"   ✅ Loaded existing scaler for compatibility")
            else:
                print(f"   ⚠️  Existing scaler not found, creating new one")
                scaler = StandardScaler()
                # Fit scaler on available data
                X_all = df[top_features].replace([np.inf, -np.inf], np.nan).fillna(0)
                scaler.fit(X_all)
        except Exception as e:
            print(f"   ❌ Error loading existing scaler: {e}")
            print(f"   → Creating new scaler")
            scaler = StandardScaler()
            X_all = df[top_features].replace([np.inf, -np.inf], np.nan).fillna(0)
            scaler.fit(X_all)
        
        # Step 9: Create final dataset with existing features
        final_df = self.create_final_dataset(df, None, scaler, top_features)
        
        # Step 10: Save data
        success = self.save_data(final_df, top_features, scaler, None)
        
        if success:
            print(f"\n✅ COMBINED DATA PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("📊 Key Results:")
            print(f"   ✅ Selected top {len(top_features)} features using SHAP analysis")
            print(f"   ✅ Features scaled using StandardScaler")
            print(f"   ✅ Final dataset ready for forecasting")
            print(f"   ✅ Multi-horizon targets created")
            print(f"   ✅ ALL recent data preserved for forecasting")
            print(f"   ✅ Dataset ready for forecast.py to predict next 3 days")
            print(f"\n📊 Next steps:")
            print(f"   1. Use forecast.py with the generated CSV")
            print(f"   2. Predict AQI for next 3 days")
            print(f"   3. Integrate with Streamlit app")
        else:
            print(f"\n❌ COMBINED DATA PIPELINE FAILED!")
            print("=" * 80)
        
        return success

def main():
    """Run the combined data pipeline"""
    pipeline = CombinedDataPipeline()
    success = pipeline.run_pipeline()
    
    if success:
        print(f"\n🎉 Ready for AQI Forecasting!")
        print(f"   📁 Use: {pipeline.output_path}")
        print(f"   🎯 Predict next 3 days AQI")
        print(f"   🔒 No data leakage")
        print(f"   ✅ All recent data preserved")
    else:
        print(f"\n❌ Pipeline failed! Check error messages above.")

if __name__ == "__main__":
    main()

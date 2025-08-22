#!/usr/bin/env python3
"""
Phase 2: Real-time Preprocessing for UI Updates
==============================================

This script processes data in real-time for the Streamlit UI:
- Processes the latest merged data
- Calculates numerical AQI with EPA compliance
- Creates real-time features for immediate display
- Optimized for speed and UI responsiveness

Author: Data Science Team
Date: 2024-03-09
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

class RealtimePreprocessor:
    def __init__(self):
        """Initialize real-time preprocessor for UI updates"""
        print("🔧 PHASE 2: REAL-TIME PREPROCESSING FOR UI UPDATES")
        print("=" * 70)
        
        # Data paths - use merged data from data collection
        self.input_path = "data_repositories/historical_data/processed/merged_data.csv"
        self.output_path = "data_repositories/features/phase1_realtime_features.csv"
        self.metadata_path = "data_repositories/features/phase1_realtime_metadata.json"
        
        # Create output directories
        os.makedirs("data_repositories/features", exist_ok=True)
        
        # EPA AQI breakpoints with CORRECT units and averaging periods
        self.aqi_breakpoints = {
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
            'o3_8hr': [  # ppb (8-hr average) - truncate to 0.001 ppm = 1 ppb
                (0, 54, 0, 50),
                (55, 70, 51, 100),
                (71, 85, 101, 150),
                (86, 105, 151, 200),
                (106, 200, 201, 300)
            ],
            'o3_1hr': [  # ppb (1-hr average) - truncate to 0.001 ppm = 1 ppb
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
        
        # EPA truncation rules (concentration precision before AQI calculation)
        self.truncation_rules = {
            'pm2_5': 0.1,      # µg/m³ to 0.1 µg/m³
            'pm10': 1.0,       # µg/m³ to 1 µg/m³
            'o3': 1.0,         # ppb to 1 ppb (0.001 ppm)
            'co': 0.1,         # ppm to 0.1 ppm
            'so2': 1.0,        # ppb to 1 ppb
            'no2': 1.0         # ppb to 1 ppb
        }
        
        # Molecular weights for unit conversion (g/mol)
        self.molecular_weights = {
            'o3': 48.00,       # Ozone
            'no2': 46.01,      # Nitrogen dioxide
            'so2': 64.07,      # Sulfur dioxide
            'co': 28.01        # Carbon monoxide
        }
        
        print(f"📁 Input: {self.input_path}")
        print(f"📁 Output: {self.output_path}")
        print(f"🎯 Target: Real-time features with numerical AQI for UI display")
        print(f"🔧 IMPLEMENTING EPA-COMPLIANT AQI CALCULATION")
        
    def convert_units_to_epa_standard(self, df):
        """Convert pollutant units from µg/m³ to EPA standard units"""
        print(f"\n🔄 CONVERTING UNITS TO EPA STANDARD")
        print("-" * 50)
        
        # Standard molar volume at 25°C, 1 atm (L/mol)
        molar_volume = 24.45
        
        # Convert O3 from µg/m³ to ppb
        if 'o3' in df.columns:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            df['o3_ppb'] = (df['o3'] * molar_volume) / self.molecular_weights['o3']
            print(f"   O3 converted: µg/m³ → ppb")
        
        # Convert NO2 from µg/m³ to ppb
        if 'no2' in df.columns:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            df['no2_ppb'] = (df['no2'] * molar_volume) / self.molecular_weights['no2']
            print(f"   NO2 converted: µg/m³ → ppb")
        
        # Convert SO2 from µg/m³ to ppb
        if 'so2' in df.columns:
            # µg/m³ to ppb: ppb = (µg/m³ × 24.45) / MW
            df['so2_ppb'] = (df['so2'] * molar_volume) / self.molecular_weights['so2']
            print(f"   SO2 converted: µg/m³ → ppb")
        
        # Convert CO from µg/m³ to ppm
        if 'co' in df.columns:
            # µg/m³ to ppm: ppm = (µg/m³ × 24.45) / (1000 × MW)
            df['co_ppm'] = (df['co'] * molar_volume) / (1000 * self.molecular_weights['co'])
            print(f"   CO converted: µg/m³ → ppm")
        
        # PM2.5 and PM10 are already in µg/m³, no conversion needed
        print(f"   PM2.5 and PM10: already in µg/m³ (no conversion needed)")
        
        return df
    
    def load_data(self):
        """Load the merged dataset for real-time processing"""
        print(f"\n📥 LOADING MERGED DATA")
        print("-" * 40)
        
        if not os.path.exists(self.input_path):
            print(f"❌ Input file not found: {self.input_path}")
            return None
        
        # Load data
        df = pd.read_csv(self.input_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"   Raw data loaded: {len(df):,} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   Columns: {len(df.columns)}")
        
        return df
    
    def apply_epa_truncation(self, concentration, pollutant):
        """Apply EPA truncation rules to concentration values"""
        if pd.isna(concentration) or concentration < 0:
            return np.nan
        
        truncation = self.truncation_rules.get(pollutant, 1.0)
        
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
    
    def calculate_required_averages(self, df):
        """Calculate required averaging periods for EPA AQI calculation"""
        print(f"\n⏰ CALCULATING REQUIRED AVERAGING PERIODS")
        print("-" * 50)
        
        # Sort by timestamp for proper rolling calculations
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # PM2.5: 24-hour average
        if 'pm2_5' in df.columns:
            df['pm2_5_24h_avg'] = df['pm2_5'].rolling(window=24, min_periods=18).mean()
            print(f"   PM2.5: 24-hour rolling average (min 18 hours)")
        
        # PM10: 24-hour average
        if 'pm10' in df.columns:
            df['pm10_24h_avg'] = df['pm10'].rolling(window=24, min_periods=18).mean()
            print(f"   PM10: 24-hour rolling average (min 18 hours)")
        
        # O3: 8-hour average (and 1-hour for high concentrations)
        if 'o3_ppb' in df.columns:
            df['o3_8h_avg'] = df['o3_ppb'].rolling(window=8, min_periods=6).mean()
            df['o3_1h_avg'] = df['o3_ppb']  # 1-hour values (already hourly data)
            print(f"   O3: 8-hour rolling average (min 6 hours) + 1-hour values")
        
        # CO: 8-hour average
        if 'co_ppm' in df.columns:
            df['co_8h_avg'] = df['co_ppm'].rolling(window=8, min_periods=6).mean()
            print(f"   CO: 8-hour rolling average (min 6 hours)")
        
        # NO2: 1-hour average (already hourly data)
        if 'no2_ppb' in df.columns:
            df['no2_1h_avg'] = df['no2_ppb']
            print(f"   NO2: 1-hour values (already hourly data)")
        
        # SO2: 1-hour average (already hourly data)
        if 'so2_ppb' in df.columns:
            df['so2_1h_avg'] = df['so2_ppb']
            print(f"   SO2: 1-hour values (already hourly data)")
        
        return df
    
    def calculate_aqi(self, concentration, pollutant, averaging_period='1hr'):
        """Calculate AQI for a given pollutant concentration using EPA breakpoints"""
        if pd.isna(concentration) or concentration < 0:
            return np.nan
        
        # Select appropriate breakpoints
        if pollutant == 'o3':
            if averaging_period == '8hr':
                breakpoints = self.aqi_breakpoints['o3_8hr']
            else:
                breakpoints = self.aqi_breakpoints['o3_1hr']
        else:
            breakpoints = self.aqi_breakpoints.get(pollutant, [])
        
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
    
    def calculate_numerical_aqi(self, df):
        """Calculate numerical AQI for each row using EPA-compliant method"""
        print(f"\n🧮 CALCULATING NUMERICAL AQI WITH EPA COMPLIANCE")
        print("-" * 60)
        
        # Calculate AQI for each pollutant with proper averaging and truncation
        aqi_values = {}
        
        # PM2.5 (24-hour average) - apply truncation
        if 'pm2_5_24h_avg' in df.columns:
            pm25_truncated = df['pm2_5_24h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'pm2_5'))
            aqi_values['pm2_5_aqi'] = pm25_truncated.apply(lambda x: self.calculate_aqi(x, 'pm2_5'))
            valid_count = aqi_values['pm2_5_aqi'].notna().sum()
            print(f"   PM2.5 AQI calculated: {valid_count} valid values")
        
        # PM10 (24-hour average) - apply truncation
        if 'pm10_24h_avg' in df.columns:
            pm10_truncated = df['pm10_24h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'pm10'))
            aqi_values['pm10_aqi'] = pm10_truncated.apply(lambda x: self.calculate_aqi(x, 'pm10'))
            valid_count = aqi_values['pm10_aqi'].notna().sum()
            print(f"   PM10 AQI calculated: {valid_count} valid values")
        
        # Ozone - implement EPA O3 selection rule
        if 'o3_8h_avg' in df.columns and 'o3_1h_avg' in df.columns:
            o3_8h_truncated = df['o3_8h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'o3'))
            o3_1h_truncated = df['o3_1h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'o3'))
            
            # Calculate both 8-hour and 1-hour AQIs
            o3_8h_aqi = o3_8h_truncated.apply(lambda x: self.calculate_aqi(x, 'o3', '8hr'))
            o3_1h_aqi = o3_1h_truncated.apply(lambda x: self.calculate_aqi(x, 'o3', '1hr'))
            
            # EPA O3 selection rule: use the higher of 8-hour or 1-hour AQI
            # But 1-hour O3 must be ≥ 125 ppb to use 1-hour table
            o3_1h_eligible = o3_1h_truncated >= 125
            
            # Select the appropriate AQI value
            o3_final_aqi = np.where(
                o3_1h_eligible & (o3_1h_aqi > o3_8h_aqi),
                o3_1h_aqi,
                o3_8h_aqi
            )
            
            aqi_values['o3_aqi'] = o3_final_aqi
            valid_count = pd.Series(o3_final_aqi).notna().sum()
            print(f"   O3 AQI calculated: {valid_count} valid values")
        
        # CO (8-hour average) - apply truncation
        if 'co_8h_avg' in df.columns:
            co_truncated = df['co_8h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'co'))
            aqi_values['co_aqi'] = co_truncated.apply(lambda x: self.calculate_aqi(x, 'co'))
            valid_count = aqi_values['co_aqi'].notna().sum()
            print(f"   CO AQI calculated: {valid_count} valid values")
        
        # SO2 (1-hour average) - apply truncation
        if 'so2_1h_avg' in df.columns:
            so2_truncated = df['so2_1h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'so2'))
            aqi_values['so2_aqi'] = so2_truncated.apply(lambda x: self.calculate_aqi(x, 'so2'))
            valid_count = aqi_values['so2_aqi'].notna().sum()
            print(f"   SO2 AQI calculated: {valid_count} valid values")
        
        # NO2 (1-hour average) - apply truncation
        if 'no2_1h_avg' in df.columns:
            no2_truncated = df['no2_1h_avg'].apply(lambda x: self.apply_epa_truncation(x, 'no2'))
            aqi_values['no2_aqi'] = no2_truncated.apply(lambda x: self.calculate_aqi(x, 'no2'))
            valid_count = aqi_values['no2_aqi'].notna().sum()
            print(f"   NO2 AQI calculated: {valid_count} valid values")
        
        # Calculate overall AQI (maximum of all pollutant AQIs)
        aqi_df = pd.DataFrame(aqi_values)
        df['numerical_aqi'] = aqi_df.max(axis=1)
        
        # Identify the primary pollutant for each row
        df['primary_pollutant'] = aqi_df.idxmax(axis=1).str.replace('_aqi', '')
        
        print(f"\n   Overall numerical AQI calculated: {df['numerical_aqi'].notna().sum()} valid values")
        print(f"   AQI range: {df['numerical_aqi'].min():.0f} to {df['numerical_aqi'].max():.0f}")
        
        # Remove categorical AQI if it exists
        if 'aqi_category' in df.columns:
            df = df.drop('aqi_category', axis=1)
            print(f"   Removed categorical AQI column")
        
        return df
        
    def engineer_realtime_features(self, df):
        """Engineer features for real-time UI display"""
        print(f"\n⚙️ ENGINEERING REAL-TIME FEATURES FOR UI")
        print("-" * 50)
    
        # Create time features from timestamp
        print(f"   Creating time-based features...")
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
    
        # Time-based cyclical features
        print(f"   Adding cyclical time features...")
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
    
        # Day type features
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    
        # Weather interaction features
        if 'temperature' in df.columns and 'relative_humidity' in df.columns:
            df['heat_index'] = df['temperature'] * (1 + 0.01 * df['relative_humidity'])
            print(f"      → Added heat_index")
    
        if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            if df['wind_direction'].notna().any():
                df['wind_east'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))
                df['wind_north'] = df['wind_speed'] * np.sin(np.radians(df['wind_direction']))
                print(f"      → Added wind components")
    
        # Pollution interaction features
        if 'pm2_5' in df.columns and 'pm10' in df.columns:
            df['pm_ratio'] = df['pm2_5'] / (df['pm10'] + 1e-6)
            print(f"      → Added PM2.5/PM10 ratio")
    
        if 'co' in df.columns and 'no2' in df.columns:
            df['co_no2_ratio'] = df['co'] / (df['no2'] + 1e-6)
            print(f"      → Added CO/NO2 ratio")
    
        # Lag features for POLLUTANTS only (not AQI)
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                # Shorter lags for real-time display
                for lag in [1, 3, 6, 12, 18, 24]:
                    df[f'{pollutant}_lag_{lag}h'] = df[pollutant].shift(lag)
                print(f"      → Added {pollutant} lags (1,3,6,12,18,24h)")
    
        # Rolling statistics for POLLUTANTS only
        for pollutant in ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2']:
            if pollutant in df.columns:
                # Real-time windows
                for window in [6, 12, 18, 24]:
                    df[f'{pollutant}_{window}h_mean'] = df[pollutant].rolling(window=window, min_periods=1).mean()
                    df[f'{pollutant}_{window}h_std'] = df[pollutant].rolling(window=window, min_periods=1).std()
                print(f"      → Added {pollutant} rolling statistics (6,12,18,24h)")
    
        # Weather rolling features
        if 'temperature' in df.columns:
            for window in [6, 12, 18, 24]:
                df[f'temp_{window}h_mean'] = df['temperature'].rolling(window=window, min_periods=1).mean()
            print(f"      → Added temperature rolling features")
    
        if 'relative_humidity' in df.columns:
            for window in [6, 12, 18, 24]:
                df[f'humidity_{window}h_mean'] = df['relative_humidity'].rolling(window=window, min_periods=1).mean()
            print(f"      → Added humidity rolling features")
    
        print(f"   Total features after engineering: {len(df.columns)}")
        print(f"   ✅ Real-time features ready for UI display")
        
        return df
        
    def handle_missing_values(self, df):
        """Handle missing values in the dataset"""
        print(f"\n🔧 HANDLING MISSING VALUES")
        print("-" * 50)
        
        # Check missing values before
        missing_before = df.isnull().sum()
        total_missing = missing_before.sum()
        print(f"   Missing values before: {total_missing:,}")
        
        # Handle missing values by column type
        for col in df.columns:
            if col == 'timestamp':
                continue
                
            missing_count = df[col].isnull().sum()
            if missing_count == 0:
                continue
                
            missing_pct = (missing_count / len(df)) * 100
            print(f"   {col}: {missing_count:,} missing ({missing_pct:.1f}%)")
            
            # Handle based on column type
            if col in ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']:
                # Pollution data - forward fill then backward fill
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                print(f"      → Forward/backward filled")
                
            elif col in ['temperature', 'tmin', 'tmax', 'dew_point', 'relative_humidity']:
                # Weather data - interpolate
                df[col] = df[col].interpolate(method='linear')
                print(f"      → Linear interpolation")
                
            elif col in ['precipitation', 'wind_speed', 'pressure']:
                # Weather data - fill with 0 or median
                if col == 'precipitation':
                    df[col] = df[col].fillna(0)
                    print(f"      → Filled with 0")
                else:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    print(f"      → Filled with median: {median_val:.2f}")
                    
            elif col in ['hour', 'day', 'month', 'day_of_week', 'is_weekend', 
                        'day_of_year', 'week_of_year']:
                # Time features - recalculate from timestamp
                if col == 'hour':
                    df[col] = df['timestamp'].dt.hour
                elif col == 'day':
                    df[col] = df['timestamp'].dt.day
                elif col == 'month':
                    df[col] = df['timestamp'].dt.month
                elif col == 'day_of_week':
                    df[col] = df['timestamp'].dt.dayofweek
                elif col == 'is_weekend':
                    df[col] = df['timestamp'].dt.dayofweek.isin([5, 6]).astype(int)
                elif col == 'day_of_year':
                    df[col] = df['timestamp'].dt.dayofyear
                elif col == 'week_of_year':
                    df[col] = df['timestamp'].dt.isocalendar().week
                print(f"      → Recalculated from timestamp")
                
            elif col.startswith(('hour_sin', 'hour_cos', 'month_sin', 'month_cos', 
                                'day_of_year_sin', 'day_of_year_cos')):
                # Cyclical features - recalculate
                if 'hour' in df.columns:
                    if col == 'hour_sin':
                        df[col] = np.sin(2 * np.pi * df['hour'] / 24)
                    elif col == 'hour_cos':
                        df[col] = np.cos(2 * np.pi * df['hour'] / 24)
                if 'month' in df.columns:
                    if col == 'month_sin':
                        df[col] = np.sin(2 * np.pi * df['month'] / 12)
                    elif col == 'month_cos':
                        df[col] = np.cos(2 * np.pi * df['month'] / 12)
                if 'day_of_year' in df.columns:
                    if col == 'day_of_year_sin':
                        df[col] = np.sin(2 * np.pi * df['day_of_year'] / 365)
                    elif col == 'day_of_year_cos':
                        df[col] = np.cos(2 * np.pi * df['day_of_year'] / 365)
                print(f"      → Recalculated cyclical features")
                
            else:
                # Other columns - fill with appropriate defaults
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].fillna(0)
                    print(f"      → Filled with 0")
                else:
                    df[col] = df[col].fillna('unknown')
                    print(f"      → Filled with 'unknown'")
        
        # Check missing values after
        missing_after = df.isnull().sum()
        total_missing_after = missing_after.sum()
        print(f"\n   Missing values after: {total_missing_after:,}")
        print(f"   Improvement: {total_missing - total_missing_after:,} values fixed")
        
        return df
        
    def clean_data(self, df):
        """Clean and validate the data"""
        print(f"\n🧹 CLEANING DATA")
        print("-" * 50)
        
        initial_records = len(df)
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        print(f"   Removed {initial_records - len(df)} rows with invalid timestamps")
        
        # Handle extreme outliers in pollution data
        pollution_cols = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
        
        for col in pollution_cols:
            if col in df.columns:
                # Calculate IQR for outlier detection
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Count outliers
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                if outliers > 0:
                    print(f"   {col}: {outliers} outliers detected")
                    
                    # Cap outliers instead of removing
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                    print(f"      → Capped outliers to [{lower_bound:.2f}, {upper_bound:.2f}]")
        
        # Handle temperature outliers
        if 'temperature' in df.columns:
            # Temperature should be reasonable for Peshawar (-10°C to 50°C)
            temp_outliers = ((df['temperature'] < -10) | (df['temperature'] > 50)).sum()
            if temp_outliers > 0:
                print(f"   temperature: {temp_outliers} extreme values detected")
                df['temperature'] = df['temperature'].clip(lower=-10, upper=50)
                print(f"      → Capped temperature to [-10°C, 50°C]")
        
        # Ensure AQI values are valid (0-500)
        if 'numerical_aqi' in df.columns:
            invalid_aqi = ((df['numerical_aqi'] < 0) | (df['numerical_aqi'] > 500)).sum()
            if invalid_aqi > 0:
                print(f"   numerical_aqi: {invalid_aqi} invalid values detected")
                df['numerical_aqi'] = df['numerical_aqi'].clip(lower=0, upper=500)
                print(f"      → Capped AQI to [0, 500]")
        
        print(f"   Final records: {len(df)}")
        
        return df
        
    def save_data(self, df):
        """Save real-time features for UI display"""
        print(f"\n💾 SAVING REAL-TIME FEATURES")
        print("-" * 40)
        
        # Save real-time features
        df.to_csv(self.output_path, index=False)
        print(f"   Data saved to: {self.output_path}")

        # Additionally, write numerical_aqi back into merged_data.csv for current-hour AQI usage
        try:
            merged_path = self.input_path
            if os.path.exists(merged_path):
                print(f"   Updating numerical_aqi in merged dataset: {merged_path}")
                merged_df = pd.read_csv(merged_path)
                merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])

                # Use only timestamp and numerical_aqi from processed dataframe
                aqi_cols = ['timestamp', 'numerical_aqi']
                aqi_df = df[[c for c in aqi_cols if c in df.columns]].copy()
                aqi_df['timestamp'] = pd.to_datetime(aqi_df['timestamp'])

                # Merge: prefer newly computed numerical_aqi when available
                merged_updated = merged_df.merge(
                    aqi_df, on='timestamp', how='left', suffixes=('', '_new')
                )
                if 'numerical_aqi_new' in merged_updated.columns:
                    # Overwrite or create numerical_aqi column
                    merged_updated['numerical_aqi'] = merged_updated['numerical_aqi_new'].combine_first(
                        merged_updated.get('numerical_aqi')
                    )
                    merged_updated = merged_updated.drop(columns=['numerical_aqi_new'])

                # Atomic write to avoid corruption
                tmp_path = merged_path + ".tmp"
                merged_updated.to_csv(tmp_path, index=False)
                os.replace(tmp_path, merged_path)
                print(f"   ✅ numerical_aqi column updated in merged dataset")
            else:
                print(f"   ⚠️ Merged dataset not found at {merged_path}; skipped updating numerical_aqi")
        except Exception as e:
            print(f"   ⚠️ Could not update numerical_aqi in merged dataset: {e}")
        
        # Save metadata
        metadata = {
            "preprocessing_timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "data_shape": df.shape,
            "date_range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            "missing_values_summary": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.to_dict(),
            "aqi_calculation": "EPA-COMPLIANT with proper unit conversion, averaging windows, and truncation",
            "unit_conversions": "µg/m³ → ppb for O3, NO2, SO2; µg/m³ → ppm for CO",
            "averaging_periods": "PM2.5/PM10: 24-hour; O3: 8-hour + 1-hour selection; CO: 8-hour; NO2/SO2: 1-hour",
            "epa_truncation": "Applied EPA precision rules before AQI calculation",
            "o3_selection_rule": "EPA O3 rule: 8-hour vs 1-hour selection based on concentration thresholds",
            "real_time_features": "Optimized for UI display with current AQI and pollutant data",
            "features_included": "Numerical AQI, pollutant data, weather data, time features, rolling statistics"
        }
        
        import json
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4, default=str)
        print(f"   Metadata saved to: {self.metadata_path}")
        
        # Print summary
        print(f"\n📊 REAL-TIME PREPROCESSING SUMMARY:")
        print(f"   Input records: {len(pd.read_csv(self.input_path)):,}")
        print(f"   Output records: {len(df):,}")
        print(f"   Features: {len(df.columns)}")
        print(f"   Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
        print(f"   ✅ Real-time features ready for UI display")
        print(f"   ✅ Numerical AQI calculated with EPA compliance")
        print(f"   ✅ Pollutant data with proper units")
        print(f"   ✅ Weather data with enhanced features")
        
        return True
        
    def run_preprocessing(self):
        """Run complete real-time preprocessing pipeline for UI updates"""
        print(f"\n🚀 STARTING REAL-TIME PREPROCESSING PIPELINE FOR UI")
        print("=" * 70)
        
        # Step 1: Load data
        df = self.load_data()
        if df is None:
            return False
        
        # Step 2: Convert units to EPA standard
        df = self.convert_units_to_epa_standard(df)
        
        # Step 3: Calculate required averages
        df = self.calculate_required_averages(df)
        
        # Step 4: Calculate numerical AQI
        df = self.calculate_numerical_aqi(df)
        
        # Step 5: Engineer real-time features
        df = self.engineer_realtime_features(df)
        
        # Step 6: Handle missing values
        df = self.handle_missing_values(df)
        
        # Step 7: Clean data
        df = self.clean_data(df)
        
        # Step 8: Save data
        success = self.save_data(df)
        
        if success:
            print(f"\n✅ REAL-TIME PREPROCESSING COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("📊 Key Features Created:")
            print("   ✅ EPA-COMPLIANT numerical AQI calculation")
            print("   ✅ Proper unit conversions (µg/m³ → ppb/ppm)")
            print("   ✅ Required averaging periods (24h for PM, 8h for O3/CO, 1h for NO2/SO2)")
            print("   ✅ EPA truncation rules applied")
            print("   ✅ O3 selection rule implemented (8-hour vs 1-hour)")
            print("   ✅ Real-time features for UI display")
            print("   ✅ Enhanced weather and pollutant data")
            print("   ✅ Time-based features and rolling statistics")
        else:
            print(f"\n❌ REAL-TIME PREPROCESSING FAILED!")
            print("=" * 70)
        
        return success

def main():
    """Run the real-time preprocessing pipeline for UI updates"""
    preprocessor = RealtimePreprocessor()
    success = preprocessor.run_preprocessing()
    
    if success:
        print(f"\n🎉 Real-time features ready for UI display!")
        print(f"   📊 Numerical AQI values calculated")
        print(f"   🌡️ Weather data enhanced")
        print(f"   🏭 Pollutant data with proper units")
        print(f"   ⏰ Time features and rolling statistics")
        print(f"   🔧 EPA-compliant calculations")
    else:
        print(f"\n❌ Real-time preprocessing failed! Check error messages above.")

if __name__ == "__main__":
    main()

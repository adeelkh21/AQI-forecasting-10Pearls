#!/usr/bin/env python3
"""
Smart Data Collection Script
============================

This script automatically detects the last timestamp in the merged CSV file
and collects new data from that point forward. This ensures continuous
data collection without gaps or overlaps.

Author: Data Science Team
Date: 2025-08-21
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append('.')

# Import the renamed DataCollector class
from phase1_data_collection import DataCollector

def get_last_timestamp_from_merged_data():
    """Get the last timestamp from the merged CSV file"""
    merged_file_path = "data_repositories/historical_data/processed/merged_data.csv"
    
    if not os.path.exists(merged_file_path):
        print(f"⚠️ Merged data file not found: {merged_file_path}")
        print("   Will collect data for the past 6 hours as fallback")
        return None
    
    try:
        # Read only the timestamp column to be efficient
        df = pd.read_csv(merged_file_path, usecols=['timestamp'])
        if df.empty:
            print("⚠️ Merged data file is empty")
            return None
        
        # Convert to datetime and get the latest timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        last_timestamp = df['timestamp'].max()
        
        print(f"📅 Last timestamp in merged data: {last_timestamp}")
        return last_timestamp
        
    except Exception as e:
        print(f"⚠️ Error reading merged data file: {e}")
        print("   Will collect data for the past 6 hours as fallback")
        return None

def main():
    """Main function to collect new data from last timestamp"""
    print("🔄 Starting smart data collection...")
    print("📅 Current time:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    
    # Get the last timestamp from existing data
    last_timestamp = get_last_timestamp_from_merged_data()
    
    if last_timestamp is not None:
        # Start collection from the hour AFTER the last timestamp
        start_time = (last_timestamp + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        # Cap the end time to the start of the current UTC hour
        now_utc_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        # Limit to a maximum of 6 hours after start_time
        proposed_end = start_time + timedelta(hours=6)
        end_time = proposed_end if proposed_end <= now_utc_hour else now_utc_hour
        
        # Ensure we have a valid time range (start < end)
        if end_time <= start_time:
            print(f"ℹ️ Data is already up to date (last timestamp: {last_timestamp})")
            print("   No new 6-hour window available yet")
            return 0
        
        print(f"🕐 Collection window: {start_time} to {end_time} (max 6h)")
        duration_hours = (end_time - start_time).total_seconds() / 3600
        print(f"⏰ Duration: {duration_hours:.1f} hours")
        
        # Create collector with specific time window
        collector = DataCollector(start_date=start_time, end_date=end_time, mode='hourly')
        
    else:
        # Fallback: collect 6 hours of data ending at current UTC hour
        print("⏰ Fallback: Collecting data for past 6 hours ending now (UTC hour)...")
        end_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=6)
        
        print(f"🕐 Collection window: {start_time} to {end_time}")
        print(f"⏰ Duration: 6 hours")
        
        # Create collector with fallback time window
        collector = DataCollector(start_date=start_time, end_date=end_time, mode='hourly')
    
    try:
        # Run the pipeline
        success = collector.run_pipeline()
        
        if success:
            print("✅ Data collection completed successfully")
            return 0
        else:
            print("❌ Data collection failed")
            # Try fallback if smart collection failed
            if last_timestamp is not None:
                print("🔄 Attempting fallback: fixed 6-hour window ending now (UTC hour)...")
                end_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                start_time = end_time - timedelta(hours=6)
                
                print(f"🕐 Fallback collection window: {start_time} to {end_time}")
                print(f"⏰ Duration: 6 hours")
                
                fallback_collector = DataCollector(start_date=start_time, end_date=end_time, mode='hourly')
                fallback_success = fallback_collector.run_pipeline()
                
                if fallback_success:
                    print("✅ Fallback data collection completed successfully")
                    return 0
                else:
                    print("❌ Both smart collection and fallback failed")
                    return 1
            else:
                return 1
            
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

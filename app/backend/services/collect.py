# Data collection service - wraps phase1 collection + merge logic
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..utils.paths import PHASE1_SCRIPT, MERGED_CSV, ROOT
from ..utils.runner import run_script
from ..utils.logging import get_logger

logger = get_logger('collect')


async def collect_data(hours_backfill: int = 24) -> Dict[str, Any]:
    """
    Collect new data and merge with existing dataset.
    
    Args:
        hours_backfill: Number of hours to backfill
        
    Returns:
        Dict with rows_collected, rows_added, last_timestamp
    """
    try:
        logger.info(f"Starting data collection with {hours_backfill} hours backfill")
        
        # Step 1: Run phase1 data collection
        logger.info("Running phase1 data collection...")
        result = run_script(PHASE1_SCRIPT, timeout=1800)  # 30 min timeout
        
        if not result.success:
            logger.error(f"Phase1 collection failed: {result.stderr}")
            raise RuntimeError(f"Data collection failed: {result.stderr}")
        
        logger.info("Phase1 collection completed successfully")
        
        # Step 2: Merge new data with existing
        merge_result = await _merge_new_data()
        
        return {
            "rows_collected": merge_result.get("rows_collected", 0),
            "rows_added": merge_result.get("rows_added", 0),
            "last_timestamp": merge_result.get("last_timestamp"),
            "collection_success": True,
            "merge_success": True
        }
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        return {
            "rows_collected": 0,
            "rows_added": 0,
            "last_timestamp": None,
            "collection_success": False,
            "merge_success": False,
            "error": str(e)
        }


async def _merge_new_data() -> Dict[str, Any]:
    """
    Merge newly collected data with existing merged_data.csv.
    
    Returns:
        Dict with merge results
    """
    try:
        # Check if merged CSV exists
        if not MERGED_CSV.exists():
            logger.info("No existing merged data found, creating new file")
            # Look for newly collected data files in the correct locations
            new_data_files = _find_new_data_files()
            if new_data_files:
                # Use the most recent CSV as base
                latest_csv = max(new_data_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"Using {latest_csv} as base for merged data")
                
                # Validate the base CSV before using it
                df = _validate_and_clean_csv(latest_csv)
                if df is None:
                    raise RuntimeError(f"Base CSV {latest_csv} failed validation")
                
                df.to_csv(MERGED_CSV, index=False)
                return {
                    "rows_collected": len(df),
                    "rows_added": len(df),
                    "last_timestamp": _get_last_timestamp(df)
                }
            else:
                return {"rows_collected": 0, "rows_added": 0, "last_timestamp": None}
        
        # Read existing merged data with validation
        logger.info("Reading existing merged data...")
        existing_df = _validate_and_clean_csv(MERGED_CSV)
        if existing_df is None:
            raise RuntimeError("Existing merged data failed validation")
        
        existing_count = len(existing_df)
        
        # Get last timestamp from existing data
        last_timestamp = _get_last_timestamp(existing_df)
        logger.info(f"Last timestamp in existing data: {last_timestamp}")
        
        # Look for new data files in the correct locations
        new_data_files = _find_new_data_files()
        
        if not new_data_files:
            logger.info("No new data files found")
            return {
                "rows_collected": 0,
                "rows_added": 0,
                "last_timestamp": last_timestamp
            }
        
        # Read and merge new data with validation
        new_rows = []
        validation_errors = []
        
        for csv_file in new_data_files:
            try:
                logger.info(f"Processing new data file: {csv_file.name}")
                
                # Validate the new CSV file
                new_df = _validate_and_clean_csv(csv_file)
                if new_df is None:
                    validation_errors.append(f"File {csv_file.name} failed validation")
                    continue
                
                # Filter rows newer than last timestamp if timestamp column exists
                if 'timestamp' in new_df.columns and last_timestamp:
                    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'])
                    new_df = new_df[new_df['timestamp'] > pd.to_datetime(last_timestamp)]
                
                if not new_df.empty:
                    new_rows.append(new_df)
                    logger.info(f"Added {len(new_df)} new rows from {csv_file.name}")
                else:
                    logger.info(f"No new rows from {csv_file.name} (all timestamps <= last timestamp)")
                
            except Exception as e:
                error_msg = f"Failed to process {csv_file.name}: {e}"
                logger.warning(error_msg)
                validation_errors.append(error_msg)
                continue
        
        if validation_errors:
            logger.warning(f"Validation errors encountered: {validation_errors}")
        
        if not new_rows:
            logger.info("No new rows to add")
            return {
                "rows_collected": 0,
                "rows_added": 0,
                "last_timestamp": last_timestamp,
                "validation_errors": validation_errors
            }
        
        # Combine all new data
        combined_new = pd.concat(new_rows, ignore_index=True)
        total_new_rows = len(combined_new)
        
        # Validate combined new data
        combined_new = _validate_merged_dataframe(combined_new)
        if combined_new is None:
            raise RuntimeError("Combined new data failed validation")
        
        # Merge with existing data
        merged_df = pd.concat([existing_df, combined_new], ignore_index=True)
        
        # Apply final validation and cleaning
        merged_df = _validate_merged_dataframe(merged_df)
        if merged_df is None:
            raise RuntimeError("Final merged data failed validation")
        
        # Remove duplicates based on timestamp if available
        if 'timestamp' in merged_df.columns:
            initial_count = len(merged_df)
            merged_df = merged_df.drop_duplicates(subset=['timestamp'], keep='last')
            merged_df = merged_df.sort_values('timestamp')
            duplicates_removed = initial_count - len(merged_df)
            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate timestamps")
        
        # Atomic write: write to temp file first, then replace
        temp_file = MERGED_CSV.with_suffix('.tmp')
        try:
            logger.info(f"Saving merged data: {len(merged_df)} total rows")
            merged_df.to_csv(temp_file, index=False)
            
            # Verify the temp file was written correctly
            if temp_file.exists() and temp_file.stat().st_size > 0:
                # Replace the original file
                temp_file.replace(MERGED_CSV)
                logger.info("Merged data saved successfully with atomic write")
            else:
                raise RuntimeError("Temporary file validation failed")
                
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise RuntimeError(f"Failed to save merged data: {e}")
        
        rows_added = len(merged_df) - existing_count
        
        return {
            "rows_collected": total_new_rows,
            "rows_added": rows_added,
            "last_timestamp": _get_last_timestamp(merged_df),
            "validation_errors": validation_errors,
            "duplicates_removed": duplicates_removed if 'timestamp' in merged_df.columns else 0
        }
        
    except Exception as e:
        logger.error(f"Data merging failed: {e}")
        raise RuntimeError(f"Data merging failed: {e}")


def _get_last_timestamp(df: pd.DataFrame) -> str:
    """Extract the last timestamp from a dataframe."""
    if 'timestamp' not in df.columns:
        return None
    
    try:
        # Convert to datetime and get max
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        last_ts = df['timestamp'].max()
        return last_ts.isoformat() if pd.notna(last_ts) else None
    except Exception:
        return None


def _find_new_data_files() -> List[Path]:
    """
    Find newly collected data files in the correct locations.
    
    Returns:
        List of Path objects for new data files
    """
    new_files = []
    
    # Look in the correct Phase1 output locations
    search_locations = [
        ROOT / "data_repositories" / "historical_data" / "processed",  # Main output
        ROOT / "data_repositories" / "historical_data" / "raw",        # Raw data
        ROOT,  # Root directory as fallback
    ]
    
    for location in search_locations:
        if not location.exists():
            continue
            
        logger.info(f"Searching for new data files in: {location}")
        
        # Look for CSV files that were modified recently (within last 2 hours)
        current_time = datetime.now()
        for csv_file in location.glob("*.csv"):
            if csv_file.name == "merged_data.csv":
                continue  # Skip the merged file itself
                
            try:
                file_age = current_time - datetime.fromtimestamp(csv_file.stat().st_mtime)
                if file_age < timedelta(hours=2):  # Increased from 1 hour to 2 hours
                    new_files.append(csv_file)
                    logger.info(f"Found new data file: {csv_file} (age: {file_age.total_seconds()/3600:.1f}h)")
            except Exception as e:
                logger.warning(f"Error checking file age for {csv_file}: {e}")
    
    logger.info(f"Found {len(new_files)} new data files: {[f.name for f in new_files]}")
    return new_files


def _validate_and_clean_csv(csv_file: Path) -> Optional[pd.DataFrame]:
    """
    Validate and clean a CSV file before processing.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Cleaned DataFrame or None if validation fails
    """
    try:
        if not csv_file.exists():
            logger.warning(f"CSV file does not exist: {csv_file}")
            return None
        
        # Check file size
        file_size = csv_file.stat().st_size
        if file_size == 0:
            logger.warning(f"CSV file is empty: {csv_file}")
            return None
        
        # Read CSV with error handling
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_file}: {e}")
            return None
        
        if df.empty:
            logger.warning(f"CSV file contains no data: {csv_file}")
            return None
        
        # Validate required columns
        required_columns = ['timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns in {csv_file}: {missing_columns}")
            return None
        
        # Validate timestamp column
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            invalid_timestamps = df['timestamp'].isna().sum()
            if invalid_timestamps > 0:
                logger.warning(f"Found {invalid_timestamps} invalid timestamps in {csv_file}")
                df = df.dropna(subset=['timestamp'])
                
            if df.empty:
                logger.error(f"No valid timestamps found in {csv_file}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to parse timestamps in {csv_file}: {e}")
            return None
        
        # Check for reasonable date range (not too old or future)
        min_date = df['timestamp'].min()
        max_date = df['timestamp'].max()
        current_time = pd.Timestamp.now()
        
        if max_date > current_time + pd.Timedelta(days=1):
            logger.warning(f"Future timestamps detected in {csv_file}: {max_date}")
        
        if min_date < current_time - pd.Timedelta(days=365):
            logger.warning(f"Very old timestamps detected in {csv_file}: {min_date}")
        
        # Validate data types for numeric columns
        numeric_columns = ['pm2_5', 'pm10', 'o3', 'co', 'no2', 'so2', 'temperature', 'humidity', 'pressure']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Check for extreme outliers
                    if df[col].notna().any():
                        q1 = df[col].quantile(0.01)
                        q99 = df[col].quantile(0.99)
                        outliers = ((df[col] < q1) | (df[col] > q99)).sum()
                        if outliers > 0:
                            logger.info(f"Found {outliers} outliers in {col} column")
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to numeric: {e}")
        
        logger.info(f"CSV validation passed for {csv_file}: {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logger.error(f"CSV validation failed for {csv_file}: {e}")
        return None


def _validate_merged_dataframe(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Validate and clean a merged DataFrame.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Cleaned DataFrame or None if validation fails
    """
    try:
        if df is None or df.empty:
            logger.error("DataFrame is None or empty")
            return None
        
        # Ensure timestamp column exists and is sorted
        if 'timestamp' not in df.columns:
            logger.error("Timestamp column missing from merged DataFrame")
            return None
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove any remaining invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            logger.error("No valid timestamps after cleaning")
            return None
        
        # Check for timestamp gaps (optional warning)
        time_diffs = df['timestamp'].diff().dt.total_seconds() / 3600  # hours
        large_gaps = (time_diffs > 2).sum()  # gaps larger than 2 hours
        if large_gaps > 0:
            logger.info(f"Found {large_gaps} large time gaps (>2 hours) in merged data")
        
        # Ensure no duplicate timestamps
        duplicates = df['timestamp'].duplicated().sum()
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate timestamps, removing...")
            df = df.drop_duplicates(subset=['timestamp'], keep='last')
        
        logger.info(f"DataFrame validation passed: {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logger.error(f"DataFrame validation failed: {e}")
        return None

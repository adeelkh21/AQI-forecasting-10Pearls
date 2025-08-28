#!/usr/bin/env python3
"""
EDA Demo Script
Demonstrates the EDA functionality without Streamlit
"""
import sys
import os
import pandas as pd

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_eda():
    """Demonstrate EDA functionality"""
    print("🔍 AQI EDA Analysis Demo")
    print("=" * 50)
    
    try:
        from eda_page import AQIEdaAnalyzer
        
        # Create analyzer
        analyzer = AQIEdaAnalyzer()
        print(f"✅ Analyzer created with data path: {analyzer.data_path}")
        
        # Load data
        if analyzer.load_data():
            print(f"✅ Data loaded successfully! Shape: {analyzer.aqi_df.shape}")
            
            # Show basic info
            print(f"\n📊 Dataset Overview:")
            print(f"   • Shape: {analyzer.aqi_df.shape}")
            print(f"   • Columns: {len(analyzer.aqi_df.columns)}")
            print(f"   • Date Range: {analyzer.aqi_df['timestamp'].min()} to {analyzer.aqi_df['timestamp'].max()}")
            
            # Show AQI distribution
            if 'aqi_category' in analyzer.aqi_df.columns:
                aqi_counts = analyzer.aqi_df['aqi_category'].value_counts().sort_index()
                print(f"\n📈 AQI Category Distribution:")
                for category, count in aqi_counts.items():
                    print(f"   • Category {category}: {count} occurrences")
            
            # Show numerical AQI stats
            if 'numerical_aqi' in analyzer.aqi_df.columns:
                aqi_stats = analyzer.aqi_df['numerical_aqi'].describe()
                print(f"\n📊 Numerical AQI Statistics:")
                print(f"   • Mean: {aqi_stats['mean']:.2f}")
                print(f"   • Median: {aqi_stats['50%']:.2f}")
                print(f"   • Std: {aqi_stats['std']:.2f}")
                print(f"   • Min: {aqi_stats['min']:.2f}")
                print(f"   • Max: {aqi_stats['max']:.2f}")
            
            # Show available features
            print(f"\n🔧 Available Features:")
            feature_cols = [col for col in analyzer.aqi_df.columns if col not in ['timestamp', 'date', 'day_label']]
            for i, col in enumerate(feature_cols[:10]):  # Show first 10
                print(f"   • {col}")
            if len(feature_cols) > 10:
                print(f"   • ... and {len(feature_cols) - 10} more features")
            
            print(f"\n✅ EDA Demo completed successfully!")
            print(f"💡 To see full interactive analysis, run: streamlit run eda_page.py")
            
        else:
            print("❌ Failed to load data")
            
    except ImportError as e:
        print(f"❌ Error importing EDA module: {e}")
        print("💡 Please ensure all dependencies are installed:")
        print("   pip install -r requirements_eda.txt")
    except Exception as e:
        print(f"❌ Error in EDA demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_eda()

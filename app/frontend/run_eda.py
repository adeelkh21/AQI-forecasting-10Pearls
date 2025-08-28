#!/usr/bin/env python3
"""
Standalone EDA Page Runner
Run this script to test the EDA functionality independently
"""
import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the EDA page"""
    st.set_page_config(
        page_title="AQI EDA Analysis",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    try:
        from eda_page import main as eda_main
        eda_main()
    except ImportError as e:
        st.error(f"❌ Error importing EDA module: {e}")
        st.info("Please ensure all dependencies are installed:")
        st.code("pip install -r requirements_eda.txt")
    except Exception as e:
        st.error(f"❌ Error running EDA: {e}")
        st.info("Please check the console for more details")

if __name__ == "__main__":
    main()

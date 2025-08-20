"""
Basic tests for the AQI Forecasting System
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import pandas as pd
        import numpy as np
        import streamlit as st
        import plotly.graph_objects as go
        import requests
        assert True, "All required modules imported successfully"
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {e}")

def test_python_version():
    """Test that we're using Python 3.8+"""
    version = sys.version_info
    assert version.major == 3, f"Expected Python 3, got {version.major}"
    assert version.minor >= 8, f"Expected Python 3.8+, got {version.major}.{version.minor}"

def test_file_structure():
    """Test that essential files exist"""
    essential_files = [
        "streamlit_app_clean.py",
        "enhanced_aqi_forecasting_real.py",
        "phase1_data_collection.py",
        "requirements.txt",
        "README.md"
    ]
    
    for file in essential_files:
        assert os.path.exists(file), f"Essential file {file} not found"

def test_requirements_file():
    """Test that requirements.txt contains essential packages"""
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            
        essential_packages = [
            "streamlit",
            "pandas",
            "numpy",
            "plotly",
            "scikit-learn",
            "tensorflow"
        ]
        
        for package in essential_packages:
            assert package in content, f"Package {package} not found in requirements.txt"
            
    except FileNotFoundError:
        pytest.fail("requirements.txt file not found")

def test_streamlit_app_file():
    """Test that the main Streamlit app file exists and is readable"""
    try:
        with open("streamlit_app_clean.py", "r") as f:
            content = f.read()
            assert len(content) > 0, "Streamlit app file is empty"
            assert "streamlit" in content.lower(), "Streamlit app file doesn't contain streamlit imports"
    except FileNotFoundError:
        pytest.fail("streamlit_app_clean.py file not found")

if __name__ == "__main__":
    # Run basic tests
    test_imports()
    test_python_version()
    test_file_structure()
    test_requirements_file()
    test_streamlit_app_file()
    print("✅ All basic tests passed!")

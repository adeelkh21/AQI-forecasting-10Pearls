"""
Configuration file for the Streamlit frontend
"""
import os
from typing import Dict, Any

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Streamlit Configuration
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")

# UI Configuration
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))  # seconds
AUTO_REFRESH_DEFAULT = os.getenv("AUTO_REFRESH_DEFAULT", "true").lower() == "true"

# Theme Configuration
THEME_CONFIG = {
    "primary_color": "#3b82f6",
    "secondary_color": "#f59e0b", 
    "success_color": "#10b981",
    "warning_color": "#f59e0b",
    "error_color": "#ef4444",
    "background_color": "#0e1117",
    "surface_color": "#1f2937",
    "border_color": "#374151",
    "text_color": "#f9fafb",
    "text_secondary": "#d1d5db",
    "accent_color": "#fbbf24"
}

# Chart Configuration
CHART_CONFIG = {
    "height": 400,
    "template": "plotly_dark",
    "font_family": "Arial, sans-serif",
    "font_size": 14,
    "margin": {"l": 50, "r": 50, "t": 50, "b": 50}
}

# AQI Configuration
AQI_CONFIG = {
    "ranges": {
        "Good": {"min": 0, "max": 50, "color": "#00e400"},
        "Moderate": {"min": 51, "max": 100, "color": "#ffff00"},
        "Unhealthy for Sensitive Groups": {"min": 101, "max": 150, "color": "#ff7e00"},
        "Unhealthy": {"min": 151, "max": 200, "color": "#ff0000"},
        "Very Unhealthy": {"min": 201, "max": 300, "color": "#8f3f97"},
        "Hazardous": {"min": 301, "max": 500, "color": "#7e0023"}
    },
    "max_value": 500,
    "default_value": 100
}

# Pollutant Configuration
POLLUTANT_CONFIG = {
    "PM2.5": {"unit": "μg/m³", "color": "#3b82f6"},
    "PM10": {"unit": "μg/m³", "color": "#10b981"},
    "NO2": {"unit": "ppb", "color": "#f59e0b"},
    "SO2": {"unit": "ppb", "color": "#ef4444"},
    "CO": {"unit": "ppm", "color": "#8b5cf6"},
    "O3": {"unit": "ppb", "color": "#06b6d4"}
}

# Weather Configuration
WEATHER_CONFIG = {
    "temperature": {"unit": "°C", "range": [-50, 50], "color": "#3b82f6"},
    "humidity": {"unit": "%", "range": [0, 100], "color": "#10b981"},
    "pressure": {"unit": "hPa", "range": [800, 1200], "color": "#f59e0b"},
    "wind_speed": {"unit": "m/s", "range": [0, 50], "color": "#ef4444"},
    "wind_direction": {"unit": "°", "range": [0, 360], "color": "#8b5cf6"}
}

# Forecast Configuration
FORECAST_CONFIG = {
    "default_horizon": 72,  # hours
    "chart_height": 500,
    "trend_line_color": "#f59e0b",
    "model_markers": {
        "catboost": {"symbol": "diamond", "size": 12, "color": "#3b82f6"},
        "tcn_48h": {"symbol": "square", "size": 12, "color": "#10b981"},
        "tcn_72h": {"symbol": "circle", "size": 12, "color": "#f59e0b"}
    }
}

# Layout Configuration
LAYOUT_CONFIG = {
    "page_title": "AQI Forecasting System",
    "page_icon": "🌤️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        'Get Help': 'https://github.com/your-repo/aqi-forecasting',
        'Report a bug': "https://github.com/your-repo/aqi-forecasting/issues",
        'About': "# AQI Forecasting System\nReal-time air quality monitoring and prediction"
    }
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary"""
    return {
        "api": {
            "host": API_HOST,
            "port": API_PORT,
            "base_url": API_BASE_URL
        },
        "streamlit": {
            "server_port": STREAMLIT_SERVER_PORT,
            "server_address": STREAMLIT_SERVER_ADDRESS
        },
        "ui": {
            "refresh_interval": REFRESH_INTERVAL,
            "auto_refresh_default": AUTO_REFRESH_DEFAULT
        },
        "theme": THEME_CONFIG,
        "charts": CHART_CONFIG,
        "aqi": AQI_CONFIG,
        "pollutants": POLLUTANT_CONFIG,
        "weather": WEATHER_CONFIG,
        "forecast": FORECAST_CONFIG,
        "layout": LAYOUT_CONFIG
    }

def get_api_url(endpoint: str) -> str:
    """Get full API URL for an endpoint"""
    return f"{API_BASE_URL}{endpoint}"

def get_theme_color(color_name: str) -> str:
    """Get theme color by name"""
    return THEME_CONFIG.get(color_name, THEME_CONFIG["primary_color"])

def get_aqi_category(aqi_value: float) -> str:
    """Get AQI category based on value"""
    for category, config in AQI_CONFIG["ranges"].items():
        if config["min"] <= aqi_value <= config["max"]:
            return category
    return "Unknown"

def get_aqi_color(aqi_value: float) -> str:
    """Get AQI color based on value"""
    category = get_aqi_category(aqi_value)
    return AQI_CONFIG["ranges"].get(category, {}).get("color", "#00e400")

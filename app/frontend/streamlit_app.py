"""
AQI Forecasting System - Streamlit Frontend
A sophisticated, real-time interface for monitoring and controlling AQI forecasting operations
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
import warnings
from plotly.subplots import make_subplots
import requests
import time
import json
from datetime import datetime, timedelta
import asyncio
import threading
from typing import Dict, Any, Optional, List
import numpy as np

# Page configuration
st.set_page_config(
    page_title="AQI Forecasting System",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/aqi-forecasting',
        'Report a bug': "https://github.com/your-repo/aqi-forecasting/issues",
        'About': "# AQI Forecasting System\nReal-time air quality monitoring and prediction"
    }
)

# Custom CSS for dark theme and sophisticated styling
st.markdown("""
<style>
    /* Dark theme customization */
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    .stApp {
        background-color: #0e1117;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #374151;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        color: #fbbf24;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .main-header p {
        color: #d1d5db;
        text-align: center;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Status indicators */
    .status-healthy {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    .status-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* Data table styling */
    .dataframe {
        background-color: #1f2937;
        color: #f9fafb;
        border: 1px solid #374151;
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #111827;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #3b82f6;
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #34d399;
    }
    
    /* Error message styling */
    .error-message {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #f87171;
    }
    
    /* Navigation styling */
    .nav-button {
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
        color: #f9fafb;
        border: 1px solid #4b5563;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    .nav-button.active {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-color: #60a5fa;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
REFRESH_INTERVAL = 30  # seconds

class AQIForecastingApp:
    """Main application class for AQI Forecasting System"""
    
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Configure session with extended timeouts and retry strategy
        retry_strategy = requests.adapters.Retry(
            total=5,  # Increased retries
            backoff_factor=2,  # Increased backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def check_api_health(self) -> bool:
        """Check if the FastAPI backend is healthy"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=30)
            return response.status_code == 200
        except Exception as e:
            st.error(f"❌ Backend connection error: {str(e)}")
            return False
    
    def ensure_connection(self) -> bool:
        """Ensure backend connection is stable before operations"""
        max_retries = 3
        for attempt in range(max_retries):
            if self.check_api_health():
                return True
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get current AQI and weather data"""
        try:
            response = self.session.get(f"{self.api_base_url}/api/v1/data/current", timeout=60)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_latest_forecast(self) -> Optional[Dict[str, Any]]:
        """Get the latest forecast data"""
        try:
            response = self.session.get(f"{self.api_base_url}/api/v1/forecasts/latest", timeout=60)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """Get system status information"""
        try:
            response = self.session.get(f"{self.api_base_url}/api/v1/system/status", timeout=60)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def trigger_data_collection(self) -> Optional[Dict[str, Any]]:
        """Trigger data collection job"""
        try:
            # Show progress indicator
            with st.spinner("🔄 Collecting past 1 hour of data... This may take 30-60 seconds"):
                response = self.session.post(f"{self.api_base_url}/api/v1/jobs/quick/collect", timeout=300)  # 5 minutes
                if response.status_code == 200:
                    st.success("✅ Data collection completed successfully!")
                    return response.json()
                else:
                    st.error(f"❌ Data collection failed with status: {response.status_code}")
                    return None
        except Exception as e:
            st.error(f"❌ Data collection error: {str(e)}")
            return None
    
    def trigger_data_processing(self) -> Optional[Dict[str, Any]]:
        """Trigger data processing job"""
        try:
            # Show progress indicator
            with st.spinner("🔄 Starting data processing... This may take 2-3 minutes"):
                response = self.session.post(f"{self.api_base_url}/api/v1/jobs/quick/process", timeout=600)  # 10 minutes
                if response.status_code == 200:
                    st.success("✅ Data processing completed successfully!")
                    return response.json()
                else:
                    st.error(f"❌ Data processing failed with status: {response.status_code}")
                    return None
        except Exception as e:
            st.error(f"❌ Data processing error: {str(e)}")
            return None
    
    def trigger_forecasting(self) -> Optional[Dict[str, Any]]:
        """Trigger forecasting job"""
        try:
            response = self.session.post(f"{self.api_base_url}/api/v1/jobs/quick/forecast", timeout=600)  # 10 minutes
            return response.json()
        except:
            return None

def create_aqi_gauge(value: float, category: str) -> go.Figure:
    """Create a beautiful AQI gauge chart"""
    # Color mapping based on AQI category
    color_map = {
        "Good": "#00e400",
        "Moderate": "#ffff00", 
        "Unhealthy for Sensitive Groups": "#ff7e00",
        "Unhealthy": "#ff0000",
        "Very Unhealthy": "#8f3f97",
        "Hazardous": "#7e0023"
    }
    
    color = color_map.get(category, "#00e400")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Current AQI", 'font': {'size': 24, 'color': '#f9fafb'}},
        delta={'reference': 100, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 500], 'tickwidth': 1, 'tickcolor': "#374151"},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "#1f2937",
            'borderwidth': 2,
            'bordercolor': "#374151",
            'steps': [
                {'range': [0, 50], 'color': '#00e400'},
                {'range': [51, 100], 'color': '#ffff00'},
                {'range': [101, 150], 'color': '#ff7e00'},
                {'range': [151, 200], 'color': '#ff0000'},
                {'range': [201, 300], 'color': '#8f3f97'},
                {'range': [301, 500], 'color': '#7e0023'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 300
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f9fafb"},
        height=400
    )
    
    return fig



def create_forecast_chart(forecast_data: Dict[str, Any]) -> go.Figure:
    """Create a forecast visualization chart"""
    if not forecast_data or 'forecasts' not in forecast_data:
        return go.Figure()
    
    forecasts = forecast_data['forecasts']
    if not forecasts:
        return go.Figure()
    
    # Extract data for plotting
    hours_ahead = [f['hours_ahead'] for f in forecasts]
    values = [f['forecast_value'] for f in forecasts]
    models = [f['model_used'] for f in forecasts]
    
    # Create the main forecast line
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours_ahead,
        y=values,
        mode='lines+markers',
        name='AQI Forecast',
        line=dict(color='#3b82f6', width=4),
        marker=dict(size=8, color='#3b82f6'),
        hovertemplate='<b>Hour %{x}</b><br>AQI: %{y:.1f}<extra></extra>'
    ))
    
    # Add trend line
    if len(hours_ahead) > 1:
        z = np.polyfit(hours_ahead, values, 1)
        p = np.poly1d(z)
        trend_line = p(hours_ahead)
        
        fig.add_trace(go.Scatter(
            x=hours_ahead,
            y=trend_line,
            mode='lines',
            name='Trend Line',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            hovertemplate='<b>Trend</b><br>AQI: %{y:.1f}<extra></extra>'
        ))
    
    # Add model transition markers
    unique_models = list(set(models))
    for model in unique_models:
        model_indices = [i for i, m in enumerate(models) if m == model]
        if model_indices:
            fig.add_trace(go.Scatter(
                x=[hours_ahead[i] for i in model_indices],
                y=[values[i] for i in model_indices],
                mode='markers',
                name=f'{model.upper()} Model',
                marker=dict(size=12, symbol='diamond'),
                hovertemplate=f'<b>{model.upper()}</b><br>Hour %{{x}}<br>AQI: %{{y:.1f}}<extra></extra>'
            ))
    
    fig.update_layout(
        title="72-Hour AQI Forecast with Trend Analysis",
        title_font={'size': 20, 'color': '#f9fafb'},
        xaxis_title="Hours Ahead",
        yaxis_title="Predicted AQI",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f9fafb"},
        xaxis={'gridcolor': '#374151'},
        yaxis={'gridcolor': '#374151'},
        height=500,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.8)',
            bordercolor='#374151',
            borderwidth=1
        )
    )
    
    return fig

def create_aqi_timeline_chart(timeline_data, current_data):
    """Create a complete AQI timeline chart using Plotly"""
    try:
        timeline = timeline_data.get('timeline', [])
        if not timeline:
            print("❌ No timeline data available")
            return go.Figure()
        
        print(f"📊 Creating timeline chart with {len(timeline)} data points")
        
        # Extract data and convert timestamps to datetime
        timestamps = []
        aqi_values = []
        categories = []
        
        for point in timeline:
            try:
                # Parse timestamp and convert to datetime
                timestamp_str = point['timestamp']
                if isinstance(timestamp_str, str):
                    # Handle different timestamp formats
                    if 'T' in timestamp_str:
                        dt = pd.to_datetime(timestamp_str)
                    else:
                        dt = pd.to_datetime(timestamp_str, format='%Y-%m-%d %H:%M:%S')
                else:
                    dt = pd.to_datetime(timestamp_str)
                
                timestamps.append(dt)
                aqi_values.append(float(point['aqi_value']))
                categories.append(point['aqi_category'])
                
            except Exception as e:
                print(f"⚠️ Error processing point: {point}, Error: {e}")
                continue
        
        if not timestamps:
            print("❌ No valid timestamps found")
            return go.Figure()
        
        print(f"✅ Processed {len(timestamps)} valid data points")
        print(f"📅 Date range: {min(timestamps)} to {max(timestamps)}")
        print(f"📊 AQI range: {min(aqi_values):.1f} to {max(aqi_values):.1f}")
        
        # Get current AQI for highlighting
        current_aqi = current_data.get('aqi_value', 0)
        current_timestamp = current_data.get('timestamp', '')
        
        # Create figure
        fig = go.Figure()
        
        # Add historical AQI line - use actual datetime objects
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=aqi_values,
            mode='lines',
            name='Historical AQI',
            line=dict(color='#10b981', width=2),
            hovertemplate='<b>Date:</b> %{x}<br><b>AQI:</b> %{y:.1f}<br><b>Category:</b> %{text}<extra></extra>',
            text=categories
        ))
        
        # Highlight current AQI point if we have current data
        if current_aqi > 0:
            # Find the most recent timestamp for current AQI
            if timestamps:
                current_dt = max(timestamps)  # Use most recent timestamp
                fig.add_trace(go.Scatter(
                    x=[current_dt],
                    y=[current_aqi],
                    mode='markers',
                    name='Current AQI',
                    marker=dict(
                        size=15,
                        color='#ef4444',
                        symbol='diamond',
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate=f'<b>Current AQI:</b> {current_aqi:.1f}<br><b>Time:</b> %{{x}}<extra></extra>'
                ))
        
        # Add AQI category bands
        add_aqi_category_bands(fig)
        
        # Update layout with better formatting
        fig.update_layout(
            title="📊 Complete AQI Timeline - Historical Data & Current Status",
            xaxis_title="Time (UTC)",
            yaxis_title="AQI Value",
            hovermode='x unified',
            showlegend=True,
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f3f4f6', size=12),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                showgrid=True,
                rangeslider=dict(visible=True),
                tickformat='%Y-%m-%d',
                tickangle=45
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                showgrid=True,
                range=[0, max(aqi_values) + 50] if aqi_values else [0, 500],
                title="AQI Value"
            ),
            legend=dict(
                bgcolor='rgba(0,0,0,0.8)',
                bordercolor='#374151',
                borderwidth=1
            )
        )
        
        print("✅ Timeline chart created successfully")
        return fig
        
    except Exception as e:
        print(f"❌ Error creating timeline chart: {e}")
        import traceback
        traceback.print_exc()
        # Return empty figure on error
        return go.Figure()

def add_aqi_category_bands(fig):
    """Add AQI category background bands to a plotly figure"""
    # AQI category breakpoints and colors
    aqi_bands = [
        (0, 50, 'Good', '#10b981', 0.1),
        (51, 100, 'Moderate', '#f59e0b', 0.1),
        (101, 150, 'Unhealthy for Sensitive Groups', '#f97316', 0.1),
        (151, 200, 'Unhealthy', '#ef4444', 0.1),
        (201, 300, 'Very Unhealthy', '#8b5cf6', 0.1),
        (301, 500, 'Hazardous', '#7c2d12', 0.1)
    ]
    
    for min_val, max_val, label, color, opacity in aqi_bands:
        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=min_val,
            y1=max_val,
            xref="paper",
            yref="y",
            fillcolor=color,
            opacity=opacity,
            layer="below",
            line_width=0
        )
        
        # Add text labels for each band
        fig.add_annotation(
            x=0.02,
            y=(min_val + max_val) / 2,
            xref="paper",
            yref="y",
            text=label,
            showarrow=False,
            font=dict(size=10, color=color),
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor=color,
            borderwidth=1
        )

def create_weather_chart(weather: Dict[str, float]) -> go.Figure:
    """Create a weather conditions chart"""
    if not weather:
        return go.Figure()
    
    # Create subplots for different weather parameters
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[],  # Remove subplot titles to avoid duplication
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]]
    )
    
    weather_items = list(weather.items())
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
    
    for i, (param, value) in enumerate(weather_items[:4]):
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        # Create clean, clear titles for each weather parameter
        if param == 'temperature':
            title_text = f"Temperature (°C)"
            gauge_range = [-20, 50]
        elif param == 'humidity':
            title_text = f"Humidity (%)"
            gauge_range = [0, 100]
        elif param == 'pressure':
            title_text = f"Pressure (hPa)"
            gauge_range = [800, 1200]
        elif param == 'wind_speed':
            title_text = f"Wind Speed (m/s)"
            gauge_range = [0, 30]
        else:
            title_text = param.replace('_', ' ').title()
            gauge_range = [0, 100]
        
        # Add gauge for temperature and humidity, number for others
        if param in ['temperature', 'humidity']:
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title_text, 'font': {'size': 14, 'color': '#f9fafb'}},
                gauge={
                    'axis': {'range': gauge_range, 'tickwidth': 1, 'tickcolor': "#374151"},
                    'bar': {'color': colors[i]},
                    'bgcolor': "#1f2937",
                    'borderwidth': 2,
                    'bordercolor': "#374151",
                    'steps': [
                        {'range': [gauge_range[0], gauge_range[1]], 'color': colors[i]}
                    ]
                },
                domain={'row': row, 'column': col}
            ), row=row, col=col)
        else:
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=value,
                title={'text': title_text, 'font': {'size': 14, 'color': '#f9fafb'}},
                delta={'reference': gauge_range[1]/2, 'font': {'size': 12}},
                domain={'row': row, 'column': col}
            ), row=row, col=col)
    
    # Update layout with better spacing and clear title
    fig.update_layout(
        title={
            'text': "Current Weather Conditions",
            'font': {'size': 20, 'color': '#f9fafb'},
            'x': 0.5,
            'xanchor': 'center'
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f9fafb"},
        height=500,
        margin=dict(t=80, l=20, r=20, b=20),
        showlegend=False
    )
    
    # Update subplot layout for better spacing
    fig.update_xaxes(showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, showticklabels=False)
    
    return fig


def save_timeline_artifacts(fig, timeline_data):
    """Save AQI timeline chart image and export numerical AQI CSVs into EDA folder.

    - Saves chart to EDA/aqi_timeline.png (or HTML fallback)
    - Saves numerical AQI vs timestamp to EDA/latest_numerical_aqi.csv
    - Merges numerical AQI into processed merged_data.csv and saves to EDA/merged_with_numerical_aqi.csv
    """
    try:
        # Write artifacts to single folder dataEDA (no versioning)
        os.makedirs('dataEDA', exist_ok=True)

        # Save figure as PNG (fallback to HTML if kaleido not available)
        chart_png = os.path.join('dataEDA', 'aqi_timeline.png')
        chart_html = os.path.join('dataEDA', 'aqi_timeline.html')
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                fig.write_image(chart_png, scale=2)
        except Exception:
            fig.write_html(chart_html, include_plotlyjs='cdn')

        # Build numerical AQI timeline CSV from API timeline payload
        timeline = timeline_data.get('timeline', []) if isinstance(timeline_data, dict) else []
        rows = []
        for point in timeline:
            ts = point.get('timestamp') or point.get('time')
            val = point.get('aqi_value')
            if ts is not None and val is not None:
                rows.append({'timestamp': ts, 'numerical_aqi': float(val)})
        if rows:
            df_num = pd.DataFrame(rows)
            # Normalize timestamp
            df_num['timestamp'] = pd.to_datetime(df_num['timestamp'])
            df_num = df_num.sort_values('timestamp').drop_duplicates(subset=['timestamp'], keep='last')
            num_path = os.path.join('dataEDA', 'latest_numerical_aqi.csv')
            df_num.to_csv(num_path, index=False)

            # Merge with processed merged_data.csv to include all features + numerical_aqi
            merged_src = os.path.join('data_repositories', 'historical_data', 'processed', 'merged_data.csv')
            if os.path.exists(merged_src):
                df_merged = pd.read_csv(merged_src)
                if 'timestamp' in df_merged.columns:
                    df_merged['timestamp'] = pd.to_datetime(df_merged['timestamp'])
                    out = df_merged.merge(df_num, on='timestamp', how='left')
                    out_path = os.path.join('dataEDA', 'merged_with_numerical_aqi.csv')
                    out.to_csv(out_path, index=False)
    except Exception as _e:
        # Non-fatal in UI; artifacts are best-effort
        pass

def main():
    """Main application function"""
    # Page navigation
    st.sidebar.markdown("## 🧭 Navigation")
    
    # Navigation buttons
    if st.sidebar.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
    
    if st.sidebar.button("🔍 EDA Analysis", key="nav_eda", use_container_width=True):
        st.session_state.current_page = "eda"
    
    st.sidebar.markdown("---")
    
    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Show EDA page if selected
    if st.session_state.current_page == "eda":
        # Import and run EDA page
        try:
            from eda_page import main as eda_main
            eda_main()
            return
        except ImportError:
            st.error("❌ EDA page module not found. Please ensure eda_page.py is in the same directory.")
            st.session_state.current_page = "dashboard"
    
    # Main dashboard page
    st.markdown("""
    <div class="main-header">
        <h1>🌤️ AQI Forecasting System</h1>
        <p>Real-time Air Quality Monitoring & Prediction Platform</p>
        <p style="font-size: 0.9rem; color: #9ca3af; margin-top: 0.5rem;">🕒 All timestamps are displayed in UTC (Coordinated Universal Time)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize app
    app = AQIForecastingApp()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Control Panel")
        st.markdown("---")
        
        # Smart API Status with auto-reconnection
        st.markdown("### 🔌 Connection Status")
        api_healthy = app.check_api_health()
        
        if api_healthy:
            st.success("✅ Backend Connected")
            st.info("All systems operational")
        else:
            st.error("❌ Backend Disconnected")
            st.warning("Attempting to reconnect...")
            
            # Try to reconnect
            if st.button("🔄 Reconnect", key="reconnect_btn"):
                if app.ensure_connection():
                    st.success("✅ Reconnected successfully!")
                    st.rerun()
                else:
                    st.error("❌ Reconnection failed")
                    st.info("Please check if the backend is running")
            
            # Show troubleshooting tips
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                **Backend Connection Issues:**
                1. Ensure FastAPI backend is running on port 8000
                2. Check if there are any error messages in the backend terminal
                3. Try refreshing the page
                4. Restart the backend if necessary
                """)
            
            # Don't return immediately, allow reconnection attempts
            if not app.ensure_connection():
                st.stop()
        
        st.markdown("---")
        
        # Action Buttons
        st.markdown("### 📊 Data Operations")
        
        if st.button("🔄 Collect Data (1 Hour)", use_container_width=True):
            with st.spinner("Triggering data collection..."):
                result = app.trigger_data_collection()
                if result and result.get('success'):
                    st.success("✅ Data collection job started! (Collecting past 1 hour)")
                else:
                    st.error("❌ Failed to start data collection")
        
        if st.button("⚙️ Process Data", use_container_width=True):
            # Check connection first
            if not app.ensure_connection():
                st.error("❌ Cannot connect to backend")
                return
                
            # Create a progress container
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
            # Simulate progress for long-running operation
            for i in range(101):
                time.sleep(0.05)  # Small delay to show progress
                progress_bar.progress(i)
                if i < 20:
                    status_text.text("🔄 Initializing data processing...")
                elif i < 40:
                    status_text.text("📊 Loading and validating data...")
                elif i < 60:
                    status_text.text("🔧 Feature engineering in progress...")
                elif i < 80:
                    status_text.text("⚙️ Applying transformations...")
                elif i < 100:
                    status_text.text("💾 Saving processed data...")
                else:
                    status_text.text("✅ Finalizing...")
            
            # Trigger the actual job
            with status_container:
                result = app.trigger_data_processing()
                if result and result.get('success'):
                    st.success("✅ Data processing completed successfully!")
                else:
                    st.error("❌ Data processing failed")
            
            # Clear progress indicators
            progress_container.empty()
            status_container.empty()
        
        if st.button("🔮 Generate Forecast", use_container_width=True):
            with st.spinner("Generating forecast..."):
                result = app.trigger_forecasting()
                if result and result.get('success'):
                    st.success("✅ Forecasting job started!")
                else:
                    st.error("❌ Failed to start forecasting")
        
        st.markdown("---")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, help="Automatically refresh data every 30 seconds")
        
        # Manual refresh
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # System Info
        st.markdown("### ℹ️ System Info")
        system_status = app.get_system_status()
        if system_status and system_status.get('success'):
            data = system_status.get('data', {})
            overall_status = data.get('overall_status', 'unknown')
            
            if overall_status == 'healthy':
                st.markdown('<span class="status-healthy">🟢 System Healthy</span>', unsafe_allow_html=True)
            elif overall_status == 'warning':
                st.markdown('<span class="status-warning">🟡 System Warning</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-error">🔴 System Degraded</span>', unsafe_allow_html=True)
        
        # Data Status
        st.markdown("### 📊 Data Status")
        st.info("🕒 **Note:** All timestamps are displayed in UTC time")
        current_data = app.get_current_data()
        if current_data and current_data.get('success'):
            st.success("✅ Data Available")
            timestamp = current_data.get('timestamp', 'Unknown')
            if timestamp != 'Unknown':
                st.info(f"Last Update: {timestamp} UTC")
            else:
                st.info(f"Last Update: {timestamp}")
        else:
            st.warning("⚠️ No Data Available")
            st.info("Click 'Collect Data (1 Hour)' to start")
    
    # Main content area
    
    # Connection Health Banner
    if not api_healthy:
        st.error("""
        🚨 **Backend Connection Lost**
        
        The system is experiencing connection issues with the backend. 
        Some features may not work properly. Please check the sidebar for reconnection options.
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📊 Current AQI Status")
        
        # Get current data
        current_data = app.get_current_data()
        
        if current_data and current_data.get('success'):
            data = current_data
            aqi_value = data.get('aqi_value', 0)
            aqi_category = data.get('aqi_category', 'Unknown')
            pollutants = data.get('pollutants', {})
            weather = data.get('weather', {})
            timestamp = data.get('timestamp', 'Unknown')
            
            # AQI Gauge
            aqi_gauge = create_aqi_gauge(aqi_value, aqi_category)
            st.plotly_chart(aqi_gauge, use_container_width=True)
            
            # Status cards
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📈 AQI Value</h3>
                    <h2 style="color: #fbbf24; font-size: 2rem;">{aqi_value:.1f}</h2>
                    <p style="color: #d1d5db;">{aqi_category}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🕒 Last Updated (UTC)</h3>
                    <p style="color: #d1d5db; font-size: 1.1rem;">{timestamp} UTC</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_c:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🌡️ Weather</h3>
                    <p style="color: #d1d5db; font-size: 1.1rem;">{len(weather)} parameters</p>
                </div>
                """, unsafe_allow_html=True)
            
        else:
            st.error("❌ Unable to retrieve current data")
            st.info("**To get started with AQI data:**")
            st.info("1. **Click '🔄 Collect Data'** in the sidebar")
            st.info("2. **Wait for collection to complete** (check job status)")
            st.info("3. **Click '🔄 Refresh Now'** to see the data")
            st.info("4. **Data will appear here automatically**")
            st.info("")
            st.info("**Make sure:**")
            st.info("• FastAPI backend is running on port 8000")
            st.info("• Data collection scripts are accessible")
            st.info("• Required data files exist in the system")
    
    with col2:
        st.markdown("## 🌡️ Weather Conditions")
        
        if current_data and current_data.get('success'):
            weather = current_data.get('weather', {})
            if weather:
                # Display weather data in a cleaner format
                st.markdown("### Current Weather Data")
                
                # Create a simple display of key weather parameters
                weather_cols = st.columns(2)
                for i, (param, value) in enumerate(weather.items()):
                    col_idx = i % 2
                    with weather_cols[col_idx]:
                        if param == 'temperature':
                            st.metric("🌡️ Temperature", f"{value:.1f}°C")
                        elif param == 'humidity':
                            st.metric("💧 Humidity", f"{value:.1f}%")
                        elif param == 'pressure':
                            st.metric("🌪️ Pressure", f"{value:.1f} hPa")
                        elif param == 'wind_speed':
                            st.metric("💨 Wind Speed", f"{value:.1f} m/s")
                        else:
                            st.metric(f"📊 {param.replace('_', ' ').title()}", f"{value:.1f}")
                
                # Display pollutant data instead of weather chart
                st.markdown("### Current Pollutant Levels")
                
                if current_data and current_data.get('success'):
                    data = current_data
                    pollutants = data.get('pollutants', {})
                    
                    if pollutants and len(pollutants) > 0:
                        # Create pollutant metrics in a clean format
                        pollutant_cols = st.columns(2)
                        for i, (pollutant, value) in enumerate(pollutants.items()):
                            col_idx = i % 2
                            with pollutant_cols[col_idx]:
                                # Add appropriate emojis for each pollutant
                                if 'PM2.5' in pollutant or 'pm2_5' in pollutant.lower():
                                    st.metric("🟢 PM2.5", f"{value:.1f} μg/m³")
                                elif 'PM10' in pollutant or 'pm10' in pollutant.lower():
                                    st.metric("🟡 PM10", f"{value:.1f} μg/m³")
                                elif 'NO2' in pollutant or 'no2' in pollutant.lower():
                                    st.metric("🔴 NO₂", f"{value:.1f} ppb")
                                elif 'SO2' in pollutant or 'so2' in pollutant.lower():
                                    st.metric("🟣 SO₂", f"{value:.1f} ppb")
                                elif 'CO' in pollutant or 'co' in pollutant.lower():
                                    st.metric("🟠 CO", f"{value:.1f} ppm")
                                elif 'O3' in pollutant or 'o3' in pollutant.lower():
                                    st.metric("🔵 O₃", f"{value:.1f} ppb")
                                else:
                                    st.metric(f"📊 {pollutant}", f"{value:.1f}")
                    else:
                        st.info("📊 No pollutant data available yet")
                        st.info("**To get pollutant data:**")
                        st.info("1. Click '🔄 Collect Data' button")
                        st.info("2. Wait for data collection to complete")
                        st.info("3. Click '🔄 Refresh Now' button")
            

    
    # AQI Timeline Chart Section - Main Dashboard
    st.markdown("---")
    st.markdown("## 📊 Complete AQI Timeline")
    st.markdown("**View the complete air quality history and current trends**")
    
    # Get AQI timeline data
    try:
        timeline_response = requests.get(f"{API_BASE_URL}/api/v1/data/aqi-timeline", timeout=30)
        if timeline_response.status_code == 200:
            timeline_data = timeline_response.json()
            
            if timeline_data.get('success') and timeline_data.get('timeline'):
                # Create AQI timeline chart
                timeline_chart = create_aqi_timeline_chart(timeline_data, current_data)
                st.plotly_chart(timeline_chart, use_container_width=True)
                # Save artifacts to EDA folder (image + CSV exports)
                try:
                    save_timeline_artifacts(timeline_chart, timeline_data)
                except Exception:
                    pass
                
                # Display timeline statistics
                col1, col2, col3, col4 = st.columns(4)
                stats = timeline_data.get('aqi_statistics', {})
                
                with col1:
                    st.metric("📊 Historical Min", f"{stats.get('min', 0):.0f}")
                with col2:
                    st.metric("📊 Historical Max", f"{stats.get('max', 0):.0f}")
                with col3:
                    st.metric("📊 Historical Mean", f"{stats.get('mean', 0):.1f}")
                with col4:
                    st.metric("📊 Historical Median", f"{stats.get('median', 0):.0f}")
                
                # Context information
                st.info(f"💡 **Context**: Current AQI {aqi_value:.1f} ({aqi_category}) is "
                       f"**{'below' if aqi_value < stats.get('mean', 0) else 'above'}** the historical average "
                       f"of {stats.get('mean', 0):.1f}. This represents {len(timeline_data.get('timeline', [])):,} data points "
                       f"from {timeline_data.get('date_range', {}).get('start', 'Unknown')} to "
                       f"{timeline_data.get('date_range', {}).get('end', 'Unknown')}.")
                
            else:
                st.warning("⚠️ No timeline data available")
                
        else:
            st.error(f"❌ Failed to load AQI timeline: {timeline_response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error loading AQI timeline: {str(e)}")
        st.info("💡 This feature requires the backend to be running and accessible.")
    
    st.markdown("---")
    
    # Forecast section
    st.markdown("## 🔮 AQI Forecast")
    
    # Get latest forecast
    forecast_data = app.get_latest_forecast()
    
    if forecast_data and forecast_data.get('success'):
        # The backend returns the forecast data directly, not nested under 'data'
        forecasts = forecast_data.get('forecasts', [])
        
        if forecasts:
            # Forecast chart
            forecast_chart = create_forecast_chart(forecast_data)
            st.plotly_chart(forecast_chart, use_container_width=True)
            
            # Forecast summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                horizon = forecast_data.get('forecast_horizon', 0)
                st.metric("Forecast Horizon", f"{horizon} hours")
            
            with col2:
                total_forecasts = len(forecasts)
                st.metric("Total Predictions", total_forecasts)
            
            with col3:
                models_used = forecast_data.get('metadata', {}).get('models_used', [])
                st.metric("Models Used", len(models_used))
            
            # Forecast table
            st.markdown("### 📋 Forecast Details")
            st.info("📅 All timestamps in the table below are displayed in UTC")
            forecast_df = pd.DataFrame(forecasts)
            st.dataframe(forecast_df, use_container_width=True)
            
        else:
            st.info("No forecast data available. Please generate a new forecast.")
    else:
        st.info("Forecast data will appear here when available. Click 'Generate Forecast' to create predictions.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #1f2937 0%, #111827 100%); border-radius: 15px; border: 1px solid #374151; margin-top: 3rem;">
        <h3 style="color: #fbbf24; margin-bottom: 1rem;">👨‍💻 Project Developer</h3>
        <h4 style="color: #60a5fa; margin-bottom: 0.5rem;">Muhammad Adeel</h4>
        <p style="color: #d1d5db; margin-bottom: 1rem;">Student of Data Science at GIK Institute</p>
        <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;">
            <a href="https://www.linkedin.com/in/muhammadadeel21/" target="_blank" style="text-decoration: none; color: #60a5fa; padding: 0.5rem 1rem; border: 1px solid #60a5fa; border-radius: 8px; transition: all 0.3s ease;">
                🔗 LinkedIn
            </a>
            <a href="https://github.com/adeelkh21" target="_blank" style="text-decoration: none; color: #60a5fa; padding: 0.5rem 1rem; border: 1px solid #60a5fa; border-radius: 8px; transition: all 0.3s ease;">
                🐙 GitHub
            </a>
        </div>
        <p style="color: #9ca3af; font-size: 0.9rem; margin-top: 1.5rem; margin-bottom: 0;">
            Built with ❤️ using Python, Streamlit, and Machine Learning
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.rerun()

if __name__ == "__main__":
    main()

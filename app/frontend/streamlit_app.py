import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
from typing import Dict, Any, List, Optional

# Page configuration
st.set_page_config(
    page_title="AQI Forecasting Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for elegant styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    .metric-card {
        background: white;
        padding: 1.8rem;
        border-radius: 16px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        border-left: 5px solid #667eea;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .status-online { background-color: #00ff88; }
    .status-offline { background-color: #ff4757; }
    .status-warning { background-color: #ffa502; }
    
    .action-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .data-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .chart-container {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        margin: 1.5rem 0;
        border: 1px solid #f1f3f4;
    }
    
    .sidebar-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .sidebar-section:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .info-box::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        animation: shine 3s infinite;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffa502, #ff6348);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(255, 165, 2, 0.3);
    }
    
    .success-box {
        background: linear-gradient(135deg, #00ff88, #00d4aa);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2c3e50;
        margin: 0.5rem 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .timestamp {
        font-size: 0.85rem;
        color: #95a5a6;
        font-style: italic;
        margin-top: 1rem;
        padding: 0.5rem;
        background: rgba(149, 165, 166, 0.1);
        border-radius: 6px;
        text-align: center;
    }
    
    .section-header {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 2rem 0 1rem 0;
        border-left: 4px solid #667eea;
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f3f4;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE = "http://127.0.0.1:8000"
REFRESH_INTERVAL = 30  # seconds
REQUEST_DELAY = 0.5  # seconds between API calls

# Initialize session state
if 'last_api_call' not in st.session_state:
    st.session_state.last_api_call = 0
if 'backend_status' not in st.session_state:
    st.session_state.backend_status = "unknown"
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"

def get_aqi_category(aqi_value: float) -> tuple:
    """Get AQI category and color based on value."""
    if aqi_value <= 50:
        return "Good", "#00ff88", "🟢"
    elif aqi_value <= 100:
        return "Moderate", "#ffff00", "🟡"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups", "#ff8800", "🟠"
    elif aqi_value <= 200:
        return "Unhealthy", "#ff0000", "🔴"
    elif aqi_value <= 300:
        return "Very Unhealthy", "#8800ff", "🟣"
    else:
        return "Hazardous", "#800000", "⚫"

def fetch_api_data(endpoint: str, params: dict = None, method: str = "GET") -> Optional[Dict[str, Any]]:
    """Fetch data from API with rate limiting and error handling."""
    current_time = time.time()
    if current_time - st.session_state.last_api_call < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY)
    
    try:
        url = f"{API_BASE}{endpoint}"
        if params and method == "GET":
            url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=params if params else {}, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
            
        st.session_state.last_api_call = time.time()
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend Connection Failed - Is the server running?")
        st.session_state.backend_status = "offline"
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ Request Timeout - Backend may be slow")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected Error: {str(e)}")
        return None

def get_backend_health_status() -> str:
    """Check backend health status."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            health_score = data.get('health_score', 0)
            if health_score >= 75:
                return "healthy"
            elif health_score >= 50:
                return "degraded"
            else:
                return "unhealthy"
        else:
            return "unhealthy"
    except:
        return "offline"

def display_metric_card(title: str, value: Any, unit: str = "", icon: str = "", color: str = "#667eea"):
    """Display a metric card with consistent styling."""
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <span style="font-size: 0.9rem; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px;">{title}</span>
        </div>
        <div class="metric-value" style="color: {color};">{value}</div>
        {f'<div class="metric-label">{unit}</div>' if unit else ''}
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌤️ AQI Forecasting Dashboard</h1>
        <p style="margin: 0; opacity: 0.9;">Real-time Air Quality Index Monitoring & Prediction System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>🔧 System Control</h2>
            <p style="color: #7f8c8d; font-size: 0.9rem;">Manage your AQI forecasting system</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Backend Status
        backend_status = get_backend_health_status()
        st.session_state.backend_status = backend_status
        
        status_color = {
            "healthy": "🟢",
            "degraded": "🟡", 
            "unhealthy": "🔴",
            "offline": "⚫"
        }.get(backend_status, "⚪")
        
        status_bg = {
            "healthy": "rgba(0, 255, 136, 0.1)",
            "degraded": "rgba(255, 165, 2, 0.1)",
            "unhealthy": "rgba(255, 71, 87, 0.1)",
            "offline": "rgba(0, 0, 0, 0.1)"
        }.get(backend_status, "rgba(149, 165, 166, 0.1)")
        
        st.markdown(f"""
        <div class="sidebar-section" style="background: {status_bg}; border-left: 4px solid {'#00ff88' if backend_status == 'healthy' else '#ffa502' if backend_status == 'degraded' else '#ff4757' if backend_status == 'unhealthy' else '#95a5a6'};">
            <h4 style="margin: 0 0 0.5rem 0;">Backend Status</h4>
            <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">{status_color} {backend_status.title()}</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #7f8c8d;">
                Last checked: {datetime.now().strftime('%H:%M:%S')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons
        st.markdown("### 📊 Data Operations")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Collect", use_container_width=True, help="Collect new air quality data"):
                st.info("Starting data collection...")
                result = fetch_api_data("/collect")
                if result and result.get("success"):
                    st.success(f"✅ Collected {result.get('rows_collected', 0)} new data points")
                else:
                    st.error("❌ Data collection failed")
        
        with col2:
            if st.button("🔮 Forecast", use_container_width=True, help="Run AQI forecast for next 72 hours"):
                st.info("Starting AQI forecast...")
                result = fetch_api_data("/forecast", method="POST")
                if result and result.get("success"):
                    st.success("✅ Forecast completed successfully")
                else:
                    st.error("❌ Forecast failed")
        
        # Pipeline Button
        if st.button("🚀 Full Pipeline", use_container_width=True, help="Run complete data collection and preprocessing pipeline"):
            st.info("Starting complete pipeline...")
            result = fetch_api_data("/pipeline/collect-and-prep", method="POST")
            if result:
                st.success(f"✅ Pipeline started - Job ID: {result.get('job_id', 'Unknown')}")
            else:
                st.error("❌ Pipeline failed to start")
        
        # Settings Section
        st.markdown("### ⚙️ Settings")
        
        with st.expander("🔄 Auto-refresh Settings", expanded=False):
            auto_refresh = st.checkbox("Enable auto-refresh", value=True, help="Automatically refresh data at specified intervals")
            refresh_interval = st.slider("Refresh interval (seconds)", 10, 60, 30, help="How often to refresh the dashboard")
            
            if auto_refresh:
                st.success(f"🔄 Auto-refresh enabled every {refresh_interval} seconds")
            else:
                st.info("⏸️ Auto-refresh disabled")
        
        # System Information
        with st.expander("ℹ️ System Information", expanded=False):
            st.write(f"**API Base:** {API_BASE}")
            st.write(f"**Last API Call:** {datetime.fromtimestamp(st.session_state.last_api_call).strftime('%H:%M:%S') if st.session_state.last_api_call > 0 else 'Never'}")
            st.write(f"**Backend Status:** {backend_status}")
            st.write(f"**Session ID:** {st.session_state.session_id}")
            
            # Add refresh button
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
        
        # Debug Information
        with st.expander("🔍 Debug Information", expanded=False):
            st.write(f"**API Base:** {API_BASE}")
            st.write(f"**Last API Call:** {datetime.fromtimestamp(st.session_state.last_api_call).strftime('%H:%M:%S') if st.session_state.last_api_call > 0 else 'Never'}")
            st.write(f"**Backend Status:** {backend_status}")
            st.write(f"**Request Delay:** {REQUEST_DELAY}s")
            st.write(f"**Refresh Interval:** {REFRESH_INTERVAL}s")
            
            # Test connection button
            if st.button("🧪 Test Connection", use_container_width=True):
                health_data = fetch_api_data("/health")
                if health_data:
                    st.success("✅ Backend connection successful")
                    st.json(health_data)
                else:
                    st.error("❌ Backend connection failed")
        
        # Footer in sidebar
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #7f8c8d; font-size: 0.8rem; padding: 1rem;">
            <p>🌤️ AQI Forecasting</p>
            <p>v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    col1, col2, col3 = st.columns(3)
    
    # Current AQI
    with col1:
        st.markdown("### 🌡️ Current AQI")
        aqi_data = fetch_api_data("/aqi/latest")
        if aqi_data:
            aqi_value = aqi_data.get('aqi_24h', 0)
            category, color, icon = get_aqi_category(aqi_value)
            
            display_metric_card(
                "AQI 24h",
                f"{icon} {aqi_value}",
                category,
                "🌡️",
                color
            )
            
            if aqi_data.get('timestamp'):
                st.markdown(f"""
                <div class="timestamp">
                    📅 {datetime.fromisoformat(aqi_data['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">⚠️ Unable to fetch AQI data</div>', unsafe_allow_html=True)
    
    # Current Weather
    with col2:
        st.markdown("### 🌤️ Current Weather")
        weather_data = fetch_api_data("/weather/latest")
        if weather_data:
            temp = weather_data.get('temperature', 'N/A')
            humidity = weather_data.get('humidity', 'N/A')
            wind_speed = weather_data.get('wind_speed', 'N/A')
            
            display_metric_card("Temperature", f"{temp}°C", "Celsius", "🌡️")
            display_metric_card("Humidity", f"{humidity}%", "Relative", "💧")
            display_metric_card("Wind Speed", f"{wind_speed} m/s", "Meters/Second", "💨")
            
            if weather_data.get('timestamp'):
                st.markdown(f"""
                <div class="timestamp">
                    📅 {datetime.fromisoformat(weather_data['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">⚠️ Unable to fetch weather data</div>', unsafe_allow_html=True)
    
    # System Health
    with col3:
        st.markdown("### 🏥 System Health")
        health_data = fetch_api_data("/health")
        if health_data:
            health_score = health_data.get('health_score', 0)
            status = health_data.get('status', 'unknown')
            
            # Health color based on score
            if health_score >= 75:
                health_color = "#00ff88"
                health_icon = "🟢"
            elif health_score >= 50:
                health_color = "#ffa502"
                health_icon = "🟡"
            else:
                health_color = "#ff4757"
                health_icon = "🔴"
            
            display_metric_card("Health Score", f"{health_icon} {health_score}%", status, "🏥", health_color)
            
            # Critical files status
            critical_files = health_data.get('critical_files', {})
            if critical_files:
                st.markdown("**Critical Files:**")
                for file_name, exists in critical_files.items():
                    status_icon = "✅" if exists else "❌"
                    st.write(f"{status_icon} {file_name.replace('_', ' ').title()}")
        else:
            st.markdown('<div class="warning-box">⚠️ Unable to fetch health data</div>', unsafe_allow_html=True)
    
    # AQI History Chart
    st.markdown('<div class="section-header">📈 AQI Historical Trends</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        chart_container = st.container()
        
        with chart_container:
            aqi_history = fetch_api_data("/aqi/history", {"hours": 72})
            
            if aqi_history and aqi_history.get('data'):
                data = aqi_history['data']
                
                if data:
                    # Prepare data for plotting
                    timestamps = []
                    aqi_values = []
                    
                    for point in data:
                        try:
                            timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                            aqi = point.get('aqi_24h', 0)
                            if aqi is not None:
                                timestamps.append(timestamp)
                                aqi_values.append(aqi)
                        except:
                            continue
                    
                    if timestamps and aqi_values:
                        # Create Plotly chart
                        fig = go.Figure()
                        
                        # Add AQI line
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=aqi_values,
                            mode='lines+markers',
                            name='AQI 24h',
                            line=dict(color='#667eea', width=3),
                            marker=dict(size=6, color='#667eea'),
                            fill='tonexty',
                            fillcolor='rgba(102, 126, 234, 0.1)'
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title="AQI Trends (Last 72 Hours)",
                            xaxis_title="Time",
                            yaxis_title="AQI Value",
                            hovermode='x unified',
                            template='plotly_white',
                            height=450,
                            showlegend=True,
                            margin=dict(l=50, r=50, t=50, b=50),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(size=12)
                        )
                        
                        # Add AQI category lines
                        fig.add_hline(y=50, line_dash="dash", line_color="green", annotation_text="Good", line_width=2)
                        fig.add_hline(y=100, line_dash="dash", line_color="yellow", annotation_text="Moderate", line_width=2)
                        fig.add_hline(y=150, line_dash="dash", line_color="orange", annotation_text="Unhealthy", line_width=2)
                        fig.add_hline(y=200, line_dash="dash", line_color="red", annotation_text="Very Unhealthy", line_width=2)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Data summary
                        st.markdown(f"""
                        <div class="data-section">
                            <h4>📊 Data Summary</h4>
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <div class="stat-value">{len(data)}</div>
                                    <div class="stat-label">Data Points</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">{timestamps[0].strftime('%m/%d')}</div>
                                    <div class="stat-label">Start Date</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">{timestamps[-1].strftime('%m/%d')}</div>
                                    <div class="stat-label">End Date</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">{aqi_values[-1] if aqi_values else 'N/A'}</div>
                                    <div class="stat-label">Current AQI</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-box">⚠️ No valid AQI data points found</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="info-box">ℹ️ No AQI history data available for the last 72 hours. Try collecting new data first.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-box">⚠️ Unable to fetch AQI history data - check backend connection</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        if aqi_history and aqi_history.get('data'):
            data = aqi_history['data']
            if data:
                # Calculate statistics
                aqi_values = [point.get('aqi_24h', 0) for point in data if point.get('aqi_24h') is not None]
                
                if aqi_values:
                    avg_aqi = sum(aqi_values) / len(aqi_values)
                    min_aqi = min(aqi_values)
                    max_aqi = max(aqi_values)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value">{avg_aqi:.1f}</div>
                        <div class="stat-label">Average AQI</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value">{min_aqi:.1f}</div>
                        <div class="stat-label">Min AQI</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value">{max_aqi:.1f}</div>
                        <div class="stat-label">Max AQI</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AQI distribution
                    st.markdown("**AQI Distribution:**")
                    good_count = sum(1 for aqi in aqi_values if aqi <= 50)
                    moderate_count = sum(1 for aqi in aqi_values if 51 <= aqi <= 100)
                    unhealthy_count = sum(1 for aqi in aqi_values if aqi > 100)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value" style="color: #00ff88;">{good_count}</div>
                        <div class="stat-label">🟢 Good</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value" style="color: #ffa502;">{moderate_count}</div>
                        <div class="stat-label">🟡 Moderate</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="stat-item">
                        <div class="stat-value" style="color: #ff4757;">{unhealthy_count}</div>
                        <div class="stat-label">🔴 Unhealthy</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Recent Activity Section
    st.markdown('<div class="section-header">📋 Recent Activity</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Latest Jobs")
        # This would show recent job statuses if implemented
        st.markdown('<div class="info-box">🚀 Job monitoring feature coming soon...</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📈 Latest Forecasts")
        # This would show recent forecasts if implemented
        st.markdown('<div class="info-box">🔮 Forecast history feature coming soon...</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; margin-top: 2rem;">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">🌤️ AQI Forecasting Dashboard</h3>
        <p style="margin: 0.5rem 0; font-size: 1rem;">Real-time air quality monitoring and prediction system</p>
        <p style="margin: 0.5rem 0; font-size: 0.9rem;">Built with Streamlit & FastAPI</p>
        <div style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 10px; display: inline-block;">
            <p style="margin: 0; font-size: 0.8rem; color: #95a5a6;">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()



# 🌤️ AQI Forecasting System - Streamlit Frontend

A sophisticated, real-time Streamlit interface for monitoring and controlling AQI forecasting operations.

## ✨ Features

### 🎨 **Sophisticated Dark Theme**
- **Modern Design**: Clean, professional interface with dark theme
- **Responsive Layout**: Wide layout optimized for data visualization
- **Interactive Elements**: Hover effects, smooth transitions, and visual feedback
- **Custom Styling**: Professional CSS with gradients and shadows

### 📊 **Real-Time Data Display**
- **Current AQI Status**: Beautiful gauge chart with color-coded categories
- **Weather Conditions**: Multi-parameter weather display with gauges
- **Pollutant Levels**: Interactive bar charts for all air pollutants
- **System Status**: Real-time monitoring of backend services

### 🔮 **Forecast Visualization**
- **72-Hour Forecasts**: Complete prediction timeline with trend analysis
- **Model Transitions**: Visual indicators for different forecasting models
- **Trend Lines**: Regression analysis with mathematical trend lines
- **Interactive Charts**: Plotly-based charts with hover information

### 🎛️ **Control Panel**
- **Data Collection**: One-click data collection trigger
- **Data Processing**: Automated data preprocessing pipeline
- **Forecast Generation**: Instant AQI prediction generation
- **System Monitoring**: Real-time health checks and status updates

### ⚡ **Real-Time Features**
- **Auto-refresh**: Configurable automatic data updates
- **Live Monitoring**: Continuous backend health monitoring
- **Instant Feedback**: Real-time job status and execution feedback
- **Error Handling**: Comprehensive error handling and user notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FastAPI backend running on port 8000
- Required Python packages (see requirements.txt)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure FastAPI backend is running
# (Start from app/backend/main.py)
```

### Launch the Frontend
```bash
# Method 1: Using the launch script (recommended)
python app/frontend/run_streamlit.py

# Method 2: Direct Streamlit command
streamlit run app/frontend/streamlit_app.py

# Method 3: With custom configuration
python app/frontend/run_streamlit.py --port 8501 --host 127.0.0.1 --debug
```

### Launch Options
- `--port`: Custom port (default: 8501)
- `--host`: Custom host (default: 127.0.0.1)
- `--debug`: Enable debug mode
- `--help`: Show all options

## 🏗️ Architecture

### File Structure
```
app/frontend/
├── streamlit_app.py      # Main Streamlit application
├── config.py            # Configuration and theme settings
├── run_streamlit.py     # Launch script
└── README.md           # This documentation
```

### Core Components

#### 1. **AQIForecastingApp Class**
- **API Integration**: HTTP client for FastAPI backend
- **Data Management**: Centralized data fetching and caching
- **Error Handling**: Comprehensive error handling and user feedback
- **Job Management**: Background job triggering and monitoring

#### 2. **Chart Generation Functions**
- **create_aqi_gauge()**: Interactive AQI gauge with color coding
- **create_pollutant_chart()**: Bar charts for pollutant levels
- **create_forecast_chart()**: Time-series forecast visualization
- **create_weather_chart()**: Multi-parameter weather display

#### 3. **Configuration System**
- **Theme Management**: Centralized color schemes and styling
- **API Configuration**: Backend connection settings
- **Chart Settings**: Visualization parameters and defaults
- **Environment Variables**: Configurable via .env file

## 🎨 Theme Configuration

### Color Scheme
```python
THEME_CONFIG = {
    "primary_color": "#3b82f6",      # Blue
    "secondary_color": "#f59e0b",    # Orange
    "success_color": "#10b981",      # Green
    "warning_color": "#f59e0b",      # Orange
    "error_color": "#ef4444",        # Red
    "background_color": "#0e1117",   # Dark background
    "surface_color": "#1f2937",      # Card background
    "border_color": "#374151",       # Border color
    "text_color": "#f9fafb",        # Primary text
    "text_secondary": "#d1d5db",    # Secondary text
    "accent_color": "#fbbf24"       # Accent/highlight
}
```

### AQI Color Mapping
- **Good (0-50)**: Green (#00e400)
- **Moderate (51-100)**: Yellow (#ffff00)
- **Unhealthy for Sensitive Groups (101-150)**: Orange (#ff7e00)
- **Unhealthy (151-200)**: Red (#ff0000)
- **Very Unhealthy (201-300)**: Purple (#8f3f97)
- **Hazardous (301-500)**: Maroon (#7e0023)

## 📱 User Interface

### Main Dashboard
1. **Header Section**: System title and description
2. **Control Sidebar**: Action buttons and system status
3. **AQI Gauge**: Large, interactive AQI display
4. **Status Cards**: Key metrics and information
5. **Weather Panel**: Current weather conditions
6. **Pollutant Chart**: Air pollutant levels
7. **Forecast Section**: 72-hour predictions with trend analysis

### Control Panel Features
- **API Status Indicator**: Real-time backend connection status
- **Action Buttons**: Data collection, processing, and forecasting
- **Auto-refresh Toggle**: Automatic data updates
- **System Health**: Overall system status and warnings
- **Manual Refresh**: Instant data refresh option

## 🔌 API Integration

### Endpoints Used
- `GET /health` - Backend health check
- `GET /api/v1/data/current` - Current AQI and weather data
- `GET /api/v1/forecasts/latest` - Latest forecast data
- `GET /api/v1/system/status` - System status information
- `POST /api/v1/jobs/quick/collect` - Trigger data collection
- `POST /api/v1/jobs/quick/process` - Trigger data processing
- `POST /api/v1/jobs/quick/forecast` - Trigger forecasting

### Data Flow
1. **User Interaction** → Frontend triggers API calls
2. **API Processing** → FastAPI backend executes operations
3. **Data Retrieval** → Frontend fetches updated information
4. **Visualization** → Charts and displays are updated
5. **User Feedback** → Success/error messages displayed

## 🛠️ Customization

### Environment Variables
```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=127.0.0.1

# UI Configuration
REFRESH_INTERVAL=30
AUTO_REFRESH_DEFAULT=true
```

### Theme Customization
Modify `app/frontend/config.py` to customize:
- Color schemes
- Chart configurations
- Layout settings
- AQI ranges and colors
- Pollutant and weather parameters

### Adding New Charts
1. Create chart function in `streamlit_app.py`
2. Add configuration in `config.py`
3. Integrate into main dashboard
4. Update documentation

## 🚨 Troubleshooting

### Common Issues

#### 1. **API Connection Failed**
```
❌ API Disconnected
Please ensure the FastAPI backend is running
```
**Solution**: Start the FastAPI backend from `app/backend/main.py`

#### 2. **No Data Available**
```
❌ Unable to retrieve current data
Please check if data collection is running
```
**Solution**: 
1. Click "🔄 Collect Data" button
2. Wait for data collection to complete
3. Click "🔄 Refresh Now"

#### 3. **Forecast Not Available**
```
No forecast data available. Please generate a new forecast.
```
**Solution**: Click "🔮 Generate Forecast" button

#### 4. **Port Already in Use**
```
Error: Port 8501 is already in use
```
**Solution**: Use different port with `--port` flag

### Debug Mode
Enable debug mode for detailed logging:
```bash
python app/frontend/run_streamlit.py --debug
```

## 📊 Performance Features

### Caching
- **Data Caching**: Reduces API calls for better performance
- **Chart Caching**: Prevents unnecessary chart regeneration
- **Session State**: Maintains user preferences across sessions

### Optimization
- **Lazy Loading**: Charts load only when needed
- **Efficient Updates**: Minimal re-rendering of components
- **Background Processing**: Non-blocking API calls

### Monitoring
- **Real-time Status**: Live backend health monitoring
- **Performance Metrics**: System resource utilization
- **Error Tracking**: Comprehensive error logging and display

## 🔮 Future Enhancements

### Planned Features
- **WebSocket Support**: Real-time data streaming
- **Mobile Optimization**: Responsive design for mobile devices
- **Advanced Analytics**: Statistical analysis and insights
- **Export Functionality**: Data export in various formats
- **User Authentication**: Multi-user support with roles
- **Notification System**: Alerts for critical AQI levels

### Integration Possibilities
- **IoT Devices**: Direct sensor data integration
- **External APIs**: Weather service integration
- **Machine Learning**: Advanced prediction models
- **Cloud Deployment**: Scalable cloud infrastructure

## 📚 API Documentation

For detailed API documentation, visit:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include error handling
- Write unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check this README and API docs
- **Community**: Join our discussion forum
- **Email**: Contact the development team

---

**🌤️ AQI Forecasting System** - Making air quality monitoring accessible and intelligent.

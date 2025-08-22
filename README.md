# 🌤️ AQI Forecasting System

**Real-Time Air Quality Index Forecasting System with Modern Web Architecture**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## 🎯 Project Overview

This project is a **comprehensive, production-ready Air Quality Index (AQI) forecasting system** that provides real-time air quality predictions with a modern web architecture. The system combines advanced machine learning techniques with real-time data collection, featuring a robust FastAPI backend and an elegant Streamlit frontend.

### ✨ Key Features

- 🔄 **Real-time Data Collection** - Automated hourly weather and pollution data gathering
- 🧠 **Advanced ML Models** - Ensemble forecasting with CatBoost, TCN, and traditional models
- 🚀 **Modern Backend** - FastAPI with comprehensive API endpoints and job orchestration
- 🎨 **Elegant Frontend** - Professional Streamlit dashboard with sophisticated UI/UX
- 🔧 **Production Ready** - Robust error handling, validation, and monitoring
- 📊 **Interactive Visualizations** - Real-time charts and data exploration tools
- 🎯 **High Accuracy** - Advanced forecasting through ensemble methods

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Data Pipeline  │    │  ML Models &    │
│                 │    │                 │    │  Forecasting    │
│ • OpenWeather   │───▶│ • Collection    │───▶│ • CatBoost      │
│ • Historical    │    │ • Processing    │    │ • TCN           │
│   Data         │    │ • Validation    │    │ • Ensemble      │
└─────────────────┘    │ • Feature Eng.  │    │ • Traditional   │
                       └─────────────────┘    └─────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  FastAPI Backend│
                      │                 │
                      │ • REST API      │
                      │ • Job Management│
                      │ • Data Services │
                      └─────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │Streamlit Frontend│
                      │                 │
                      │ • Real-time UI  │
                      │ • Interactive   │
                      │ • Professional  │
                      └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- 8GB RAM minimum
- Stable internet connection
- API keys for OpenWeatherMap

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/adeelkh21/aqi-forecasting-10Pearls.git
   cd aqi-forecasting-10Pearls
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Unix/MacOS:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in project root
   OPENWEATHER_API_KEY=your_api_key_here
   API_HOST=127.0.0.1
   API_PORT=8000
   STREAMLIT_API_BASE=http://localhost:9000
   LOG_LEVEL=INFO
   ```

5. **Run the application**
   ```bash
   # Terminal 1: Start FastAPI backend
   python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000 --reload
   
   # Terminal 2: Start Streamlit frontend
   streamlit run app/frontend/streamlit_app.py --server.port 9000 --server.address 127.0.0.1
   ```

6. **Access the application**
   - **Backend API**: http://127.0.0.1:8000
   - **Frontend Dashboard**: http://127.0.0.1:9000
   - **API Documentation**: http://127.0.0.1:8000/docs

---

## 🏛️ System Architecture Details

### Backend (FastAPI)

The system features a robust FastAPI backend with the following components:

- **Main Application** (`app/backend/main.py`): Core API endpoints and request handling
- **Services Layer**: Modular services for data collection, preprocessing, and forecasting
- **Job Management**: Background task orchestration and monitoring
- **Data Access**: Centralized data retrieval and validation
- **Error Handling**: Comprehensive error handling and logging

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health and status |
| `/collect` | POST | Trigger data collection |
| `/preprocess` | POST | Run data preprocessing |
| `/forecast` | POST | Generate AQI forecasts |
| `/aqi/latest` | GET | Latest AQI data |
| `/aqi/history` | GET | Historical AQI data |
| `/weather/latest` | GET | Latest weather data |
| `/jobs/{job_id}` | GET | Job status and progress |

### Frontend (Streamlit)

The Streamlit frontend provides a sophisticated, professional user interface:

- **Real-time Dashboard**: Live AQI and weather data display
- **Interactive Charts**: Plotly-based visualizations with AQI trends
- **System Control**: Data collection and forecasting controls
- **Status Monitoring**: Backend health and system status
- **Responsive Design**: Professional UI with modern styling

---

## 📊 Data Collection & Processing

### Data Sources

- **Weather Data**: OpenWeatherMap API (temperature, humidity, wind, pressure)
- **Pollution Data**: OpenWeatherMap API (PM2.5, PM10, NO2, O3, SO2, CO, NH3)
- **Historical Data**: Validated environmental datasets

### Data Pipeline

1. **Phase 1**: Data collection and merging (`phase1_data_collection.py`)
2. **Phase 2**: Data preprocessing and feature engineering (`phase2_data_preprocessing.py`)
3. **Phase 3**: Feature selection and validation (`phase3_feature_selection.py`)
4. **Phase 4**: Model training and development (`phase4_model_training.py`)
5. **Phase 5**: Model evaluation and validation (`phase5_model_evaluation.py`)
6. **Phase 6**: Hyperparameter optimization (`phase6_hyperparam_optimization.py`)
7. **Phase 8-11**: Advanced model optimization and fine-tuning
8. **Forecasting**: Model execution and prediction generation (`forecast.py`)

### Automation & CI/CD

- **Daily Runner**: Automated daily data collection (`daily_runner.py`)
- **6-Hour Collection**: Frequent data updates (`collect_6hours.py`)
- **Historical Backfill**: 150-day data reconstruction (`phase1_backfill_150_days.py`)
- **GitHub Actions**: Automated workflows for data collection and deployment

---

## 🤖 Machine Learning Models

### Current Model Stack

- **CatBoost**: Gradient boosting for structured data with advanced optimization
- **TCN (Temporal Convolutional Networks)**: Deep learning for time series forecasting
- **Ensemble Methods**: Combining multiple model outputs for improved accuracy
- **Traditional Models**: Statistical and classical ML approaches
- **Advanced Optimization**: Multi-phase hyperparameter tuning and fine-tuning

### ML Pipeline Capabilities

- **Comprehensive Training**: 11-phase ML development pipeline
- **Hyperparameter Optimization**: Advanced tuning for all models
- **Per-Horizon Optimization**: Specialized tuning for 24h, 48h, and 72h forecasts
- **Model Validation**: Extensive evaluation and testing procedures
- **Production Deployment**: Optimized models ready for real-time forecasting

### Forecasting Capabilities

- **72-Hour Predictions**: Hourly AQI forecasts for next 3 days
- **Real-Time Updates**: Continuous model performance monitoring
- **Uncertainty Quantification**: Confidence intervals and error estimates
- **Multi-Horizon**: 24h, 48h, and 72h forecasting

---

## 🌐 Web Application Features

### Dashboard Capabilities

- **Real-Time Monitoring**: Live AQI and weather data
- **Historical Trends**: Interactive 72-hour AQI charts
- **System Health**: Backend status and performance metrics
- **Data Operations**: One-click data collection and forecasting
- **Professional UI**: Sophisticated design with smooth animations

### User Experience

- **Responsive Layout**: Works on desktop and mobile devices
- **Auto-refresh**: Configurable data update intervals
- **Error Handling**: User-friendly error messages and status updates
- **Performance Monitoring**: Real-time system health indicators

---

## 📁 Project Structure

```
aqi-forecasting-10Pearls/
├── 📊 app/                          # Main application directory
│   ├── 🚀 backend/                  # FastAPI backend
│   │   ├── main.py                 # Main API application
│   │   ├── jobs.py                 # Job management
│   │   ├── services/               # Business logic services
│   │   │   ├── collect.py         # Data collection
│   │   │   ├── preprocess.py      # Data preprocessing
│   │   │   ├── forecast.py        # Forecasting engine
│   │   │   └── data_access.py     # Data access layer
│   │   ├── models/                 # Data models and schemas
│   │   └── utils/                  # Utility functions
│   └── 🎨 frontend/                # Streamlit frontend
│       └── streamlit_app.py       # Main dashboard
├── 📈 data_repositories/            # Data storage
│   ├── historical_data/            # Historical datasets
│   ├── features/                   # Engineered features
│   └── forecasts/                  # Forecast outputs
├── 🤖 saved_models/                # Trained ML models
├── 🔧 ML Pipeline Scripts          # Core ML processing
│   ├── phase1_data_collection.py   # Data collection
│   ├── phase2_data_preprocessing.py # Data preprocessing
│   ├── phase3_feature_selection.py # Feature selection
│   ├── phase4_model_training.py    # Model training
│   ├── phase5_model_evaluation.py  # Model evaluation
│   ├── phase6_hyperparam_optimization.py # Hyperparameter tuning
│   ├── phase8_tcn_optimization.py  # TCN model optimization
│   ├── phase9_advanced_tcn_optimization.py # Advanced TCN tuning
│   ├── phase10_best_model_fine_tuning.py # Final model tuning
│   ├── phase11_per_horizon_finetune.py # Per-horizon optimization
│   └── forecast.py                 # Forecasting engine
├── 🚀 Automation Scripts            # System automation
│   ├── daily_runner.py             # Daily data collection runner
│   ├── collect_6hours.py           # 6-hour collection script
│   └── phase1_backfill_150_days.py # Historical data backfill
├── 📋 requirements.txt              # Python dependencies
├── 📋 requirements-ci.txt           # CI/CD dependencies
├── 🌍 .env                         # Environment configuration
├── 📖 README.md                     # Project documentation
├── 📖 GITHUB_ACTIONS_SETUP.md      # CI/CD setup guide
├── 🎯 pathway                       # Development pathway
└── 🧪 tests/                        # Test suite and validation
```

---

## 🛠️ Technical Specifications

### System Requirements

- **Python Version**: 3.9+
- **Memory**: 8GB RAM minimum
- **Storage**: 10GB for data and models
- **Network**: Stable internet connection

### Key Dependencies

```
fastapi>=0.100.0        # Modern web framework
uvicorn>=0.23.0         # ASGI server
streamlit>=1.28.0       # Web application framework
pandas>=1.5.0           # Data manipulation
numpy>=1.21.0           # Numerical computing
scikit-learn>=1.1.0     # Machine learning
catboost>=1.2.0         # Gradient boosting
tensorflow>=2.10.0      # Deep learning
plotly>=5.15.0          # Interactive visualizations
requests>=2.28.0        # HTTP requests
python-dotenv>=1.0.0    # Environment management
```

### Performance Metrics

- **API Response Time**: <500ms for most endpoints
- **Data Collection**: 5-10 minutes per cycle
- **Forecasting**: 2-5 seconds for 72-hour prediction
- **Web App Response**: <2 seconds

---

## 🔧 Development & Deployment

### Local Development

1. **Backend Development**
   ```bash
   cd app/backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Frontend Development**
   ```bash
   cd app/frontend
   streamlit run streamlit_app.py --server.port 9000
   ```

3. **ML Pipeline Testing**
   ```bash
   # Test individual phases
   python phase1_data_collection.py
   python phase2_data_preprocessing.py
   python phase3_feature_selection.py
   
   # Run complete forecasting
   python forecast.py
   ```

4. **Automation Scripts**
   ```bash
   # Daily data collection
   python daily_runner.py
   
   # 6-hour collection
   python collect_6hours.py
   ```

### Production Deployment

- **Backend**: Deploy FastAPI with uvicorn or gunicorn
- **Frontend**: Deploy Streamlit to Streamlit Cloud or similar
- **Environment**: Use production-grade environment variables
- **Monitoring**: Implement logging and health checks

---

## 🚧 Current Status & Roadmap

### ✅ Completed Features

- **Modern Architecture**: FastAPI backend + Streamlit frontend
- **Data Pipeline**: Complete 11-phase ML development pipeline
- **ML Models**: CatBoost and TCN with advanced optimization
- **Professional UI**: Sophisticated dashboard design with modern styling
- **API System**: Comprehensive REST API endpoints with job management
- **Job Management**: Background task orchestration and monitoring
- **Error Handling**: Robust error handling, validation, and logging
- **Automation**: Daily data collection and 6-hour update scripts
- **Testing**: Comprehensive test suite and validation procedures
- **CI/CD**: GitHub Actions workflows for automated operations

### 🚧 In Progress

- **Model Optimization**: Fine-tuning and hyperparameter optimization
- **Performance Monitoring**: Advanced metrics and alerting
- **Data Validation**: Enhanced data quality checks

### 🔮 Future Enhancements

- **Mobile Application**: Native mobile app development
- **Public API**: Open API services for external users
- **Real-time Alerts**: Push notifications for air quality changes
- **Multi-city Support**: Expand to multiple locations
- **Advanced Analytics**: Machine learning insights and recommendations

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Muhammad Adeel** - Lead Developer

- **LinkedIn**: [muhammadadeel21](https://www.linkedin.com/in/muhammadadeel21)
- **GitHub**: [adeelkh21](https://github.com/adeelkh21)
- **Email**: adeel210103@gmail.com

---

## 🙏 Acknowledgments

- **OpenWeatherMap** for weather and pollution data APIs
- **FastAPI** for the modern web framework
- **Streamlit** for the web application framework
- **Open Source Community** for various libraries and tools

---

## 📞 Support

If you have questions or need support:

- 📧 **Email**: adeel210103@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/adeelkh21/aqi-forecasting-10Pearls/issues)
- 📖 **Documentation**: This README and inline code documentation

---

## ⭐ Star the Project

If this project helped you, please give it a ⭐ star on GitHub!

---

**Last Updated**: August 22, 2025  
**Version**: 3.0.0  
**Status**: Production Ready with Modern Architecture 🚀

---

## 🔍 Quick Navigation

- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [API Endpoints](#api-endpoints)
- [Project Structure](#-project-structure)
- [Development Setup](#-development--deployment)
- [Current Status](#-current-status--roadmap)

















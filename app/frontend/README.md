# 🔍 AQI Forecasting System - Frontend

A comprehensive Streamlit-based frontend for the AQI (Air Quality Index) forecasting system with integrated Exploratory Data Analysis (EDA) capabilities.

## 🚀 Features

### **Main Dashboard**
- Real-time AQI monitoring and visualization
- Historical data analysis and trends
- Forecasting model management
- System status and health monitoring

### **🔍 EDA Analysis (NEW!)**
- **9 Comprehensive Analysis Tabs:**
  1. 📊 **Overview** - Dataset structure & AQI distributions
  2. 📈 **Temporal Patterns** - Time series trends & patterns
  3. 🔗 **Correlations** - Feature relationships & multicollinearity
  4. 🌫️ **Pollutants** - Distribution plots & statistics
  5. 🌸 **Seasonal** - Monthly patterns & weekend analysis
  6. 📈 **Time Series** - Seasonal decomposition & trends
  7. 🔄 **Autocorrelation** - Lag analysis with proper visualizations
  8. 📊 **Spikes & Volatility** - Extreme events & stability analysis
  9. ⚙️ **Features** - Engineering, scaling, selection, export

- **Interactive Visualizations:** All charts use Plotly for zoom, pan, and hover interactions
- **Smart Data Loading:** Automatic path detection for data files
- **Feature Engineering:** Automated scaling, selection, and export capabilities
- **Professional Insights:** Comprehensive analysis with actionable recommendations

## 🛠️ Installation

### **Prerequisites**
- Python 3.8+
- Streamlit
- Required packages (see `requirements.txt`)

### **Setup**
```bash
# Navigate to frontend directory
cd app/frontend

# Install dependencies
pip install -r requirements.txt

# Install EDA-specific dependencies
pip install -r requirements_eda.txt
```

## 🚀 Usage

### **Launch Main Application**
```bash
streamlit run streamlit_app.py
```

### **Launch EDA Only (Standalone)**
```bash
streamlit run run_eda.py
```

### **Test EDA Functionality**
```bash
python demo_eda.py
```

## 📁 File Structure

```
app/frontend/
├── streamlit_app.py          # Main Streamlit application
├── eda_page.py              # EDA analysis module
├── app_config.py            # Application configuration
├── requirements.txt          # Main dependencies
├── requirements_eda.txt      # EDA-specific dependencies
├── run_eda.py               # Standalone EDA runner
├── demo_eda.py              # EDA functionality test
├── README.md                # This file
├── EDA_README.md            # Detailed EDA documentation
├── INTEGRATION_SUMMARY.md   # EDA integration details
├── PATH_FIX_SUMMARY.md      # Data path resolution details
├── ERROR_FIX_SUMMARY.md     # String formatting error fixes
└── PLOTLY_FIX_SUMMARY.md    # Plotly range object fixes
```

## 🔧 Recent Fixes & Improvements

### **✅ Data Path Resolution**
- **Smart Path Detection:** Automatically finds data files using multiple possible paths
- **Absolute & Relative Paths:** Works from any directory location
- **Automatic Fallback:** Uses absolute path if relative paths fail

### **✅ Plotly Range Object Errors Fixed**
- **Autocorrelation Analysis:** Proper x-axis with lag values
- **Cross-Correlation Analysis:** Correct bar chart x-axis
- **Type Safety:** Converts Python `range` objects to lists for Plotly compatibility

### **✅ String Formatting Issues Resolved**
- **Footer Rendering:** Fixed datetime formatting in EDA page
- **Error-Free Display:** No more KeyError exceptions

### **✅ Circular Import Resolution**
- **Config Module:** Renamed `config.py` to `app_config.py` to avoid Streamlit conflicts
- **Clean Imports:** Seamless module loading without import errors

## 📊 Data Requirements

### **Required Data File**
- **Location:** `dataEDA/merged_with_numerical_aqi.csv`
- **Format:** CSV with columns including:
  - `timestamp`: DateTime column
  - `numerical_aqi`: Target variable
  - `aqi_category`: Categorical AQI levels
  - Various pollutant columns (pm2_5, pm10, co, no2, o3, etc.)
  - Meteorological data (temperature, humidity, wind, etc.)

### **Data Structure**
- **Expected Shape:** ~4000+ rows × 30+ columns
- **Time Coverage:** Hourly data over extended period
- **Missing Values:** Handled automatically with imputation

## 🎯 Navigation

### **Main App Navigation**
- **Sidebar Navigation:** Switch between Dashboard and EDA Analysis
- **Session State:** Remembers current page selection
- **Seamless Integration:** No page reloads when switching

### **EDA Tab Navigation**
- **9 Organized Tabs:** Logical grouping of analysis types
- **Progressive Analysis:** Start with overview, dive into specifics
- **Interactive Elements:** Expandable sections and collapsible content

## 🔍 EDA Analysis Capabilities

### **Statistical Analysis**
- **Descriptive Statistics:** Mean, median, std, min/max for all features
- **Missing Value Analysis:** Comprehensive data quality assessment
- **Distribution Analysis:** Histograms, box plots, and statistical summaries

### **Time Series Analysis**
- **Seasonal Decomposition:** Trend, seasonal, and residual components
- **Autocorrelation:** Lag analysis for temporal dependencies
- **Cross-Correlation:** Feature lag relationships with AQI

### **Feature Engineering**
- **Automatic Scaling:** MinMax normalization for all features
- **Feature Selection:** F-regression based importance ranking
- **Data Export:** Save processed data for modeling

### **Visualization Features**
- **Interactive Charts:** Zoom, pan, hover, and selection capabilities
- **Responsive Design:** Adapts to different screen sizes
- **Professional Styling:** Consistent color schemes and layouts

## 🚨 Troubleshooting

### **Common Issues & Solutions**

#### **Data File Not Found**
```bash
# Check if data exists
ls -la ../../dataEDA/

# Verify path in eda_page.py
# The system automatically detects correct paths
```

#### **Import Errors**
```bash
# Ensure all dependencies installed
pip install -r requirements_eda.txt

# Check for circular imports
# config.py should be renamed to app_config.py
```

#### **Plotly Errors**
```bash
# All range object errors have been fixed
# If you see new errors, check data types being passed to Plotly
```

### **Debug Mode**
```bash
# Test EDA functionality without Streamlit
python demo_eda.py

# Test main app integration
python -c "import streamlit_app; print('✅ Integration successful')"
```

## 🔮 Future Enhancements

### **Planned Features**
- **Real-time Data Updates:** Live data streaming integration
- **Advanced Analytics:** Machine learning model performance analysis
- **Export Capabilities:** PDF reports and data exports
- **Custom Dashboards:** User-configurable analysis views

### **Performance Improvements**
- **Caching:** Streamlit caching for faster analysis
- **Lazy Loading:** Load heavy visualizations on demand
- **Optimized Charts:** Reduced memory usage for large datasets

## 📚 Documentation

### **Additional Resources**
- **`EDA_README.md`:** Comprehensive EDA module documentation
- **`INTEGRATION_SUMMARY.md`:** Technical integration details
- **`PATH_FIX_SUMMARY.md`:** Data path resolution guide
- **`ERROR_FIX_SUMMARY.md`:** String formatting fixes
- **`PLOTLY_FIX_SUMMARY.md`:** Plotly compatibility fixes

### **API Documentation**
- **Backend Integration:** FastAPI endpoints for data and forecasts
- **Data Services:** Real-time data fetching and processing
- **Job Management:** Background task execution and monitoring

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-analysis`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### **Testing Guidelines**
- Test EDA functionality: `python demo_eda.py`
- Test main app integration: `python -c "import streamlit_app"`
- Test Streamlit launch: `streamlit run streamlit_app.py`

## 📄 License

This project is part of the AQI Forecasting System developed by 10Pearls.

## 🆘 Support

### **Getting Help**
- **Documentation:** Check all README files in the frontend directory
- **Error Logs:** Look for specific error messages in the documentation
- **Testing:** Use demo scripts to isolate issues

### **Current Status**
- **✅ EDA Integration:** Fully operational
- **✅ All Fixes Applied:** No known errors
- **✅ Ready for Production:** Robust and reliable system

---

**Last Updated:** December 2024  
**Status:** ✅ **FULLY OPERATIONAL**  
**Version:** 2.0 (with EDA Integration)

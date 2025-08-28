# 🔍 Exploratory Data Analysis (EDA) for AQI Forecasting System

## Overview

The EDA module provides comprehensive analysis of air quality data, including interactive visualizations, statistical insights, and feature engineering capabilities. This module integrates seamlessly with the main AQI Forecasting System Streamlit application.

## Features

### 📊 Data Overview
- **Dataset Structure**: Shape, columns, date range, memory usage
- **Data Types**: Column information and non-null counts
- **Missing Values**: Analysis of data completeness
- **Sample Data**: First few rows preview

### 📈 AQI Distribution Analysis
- **Category Distribution**: Bar charts and pie charts for AQI categories
- **Frequency Analysis**: Most and least common AQI levels
- **Data Imbalance**: Insights for modeling considerations

### ⏰ Temporal Patterns
- **Time Series Trends**: AQI changes over time (categorical and numerical)
- **Hourly Patterns**: Diurnal variations in air quality
- **Weekly Patterns**: Day-of-week analysis
- **Seasonal Trends**: Monthly and seasonal variations

### 🔗 Correlation Analysis
- **Feature Correlations**: Heatmap of all numerical features
- **Top Correlations**: Ranking of most important features for AQI prediction
- **Multicollinearity**: Identification of highly correlated features

### 🌫️ Pollutant Analysis
- **Distribution Plots**: Histograms for all major pollutants
- **Statistical Summary**: Descriptive statistics for each pollutant
- **Outlier Detection**: Identification of extreme values

### 🌸 Seasonal Analysis
- **Monthly Patterns**: Box plots showing AQI distribution by month
- **Weekend vs Weekday**: Comparison of air quality on different day types
- **Seasonal Statistics**: Aggregated monthly data

### 📈 Time Series Components
- **Seasonal Decomposition**: Trend, seasonal, and residual components
- **Long-term Patterns**: Identification of recurring cycles
- **Data Structure**: Understanding of time series characteristics

### 🔄 Autocorrelation Analysis
- **Lag Analysis**: Correlation between current and past AQI values
- **Confidence Intervals**: Statistical significance of correlations
- **Feature Engineering**: Optimal lag selection for models

### 🔗 Cross-Correlation
- **Feature Lags**: How past pollutant values predict current AQI
- **Optimal Timing**: Best time lags for each feature
- **Predictive Power**: Assessment of feature importance over time

### 📊 Spikes & Volatility
- **AQI Spikes**: Analysis of extreme pollution events
- **Spike Patterns**: Frequency and timing of high AQI periods
- **Volatility Analysis**: 24-hour rolling standard deviation
- **Stability Assessment**: Air quality predictability

### ⚙️ Feature Engineering
- **Data Scaling**: MinMax normalization for all features
- **Feature Selection**: F-regression based feature importance
- **Modeling Preparation**: Clean, scaled dataset ready for ML
- **Feature Scores**: Ranking of predictive power

### 📋 Summary Report
- **Comprehensive Statistics**: All key metrics in one place
- **Key Insights**: Main findings from the analysis
- **Modeling Recommendations**: Best practices for forecasting
- **Data Quality Assessment**: Overall dataset health

## Usage

### Integration with Main App
The EDA module is automatically integrated into the main Streamlit application. Users can access it through the sidebar navigation:

1. **Dashboard**: Main AQI forecasting interface
2. **EDA Analysis**: Comprehensive data analysis interface

### Standalone Usage
To run the EDA page independently:

```bash
cd app/frontend
streamlit run run_eda.py
```

### Data Requirements
The EDA module expects data in the following location:
- **Path**: `dataEDA/merged_with_numerical_aqi.csv`
- **Format**: CSV with timestamp and numerical_aqi columns
- **Size**: Typically 1-10 MB depending on data volume

## Installation

### Dependencies
Install required packages:

```bash
pip install -r requirements_eda.txt
```

### Key Libraries
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Static plotting
- **seaborn**: Statistical visualization
- **plotly**: Interactive plotting
- **scikit-learn**: Machine learning utilities
- **statsmodels**: Time series analysis
- **streamlit**: Web application framework

## Data Flow

### 1. Data Loading
- Reads from `dataEDA/merged_with_numerical_aqi.csv`
- Parses timestamps and handles data types
- Validates data integrity

### 2. Analysis Pipeline
- **Overview**: Basic statistics and data quality
- **Distribution**: AQI category analysis
- **Temporal**: Time-based patterns
- **Correlations**: Feature relationships
- **Pollutants**: Individual pollutant analysis
- **Seasonal**: Time-based variations
- **Time Series**: Advanced temporal analysis
- **Autocorrelation**: Lag analysis
- **Spikes**: Extreme event analysis
- **Features**: Engineering and selection

### 3. Output Generation
- **Interactive Charts**: Plotly visualizations
- **Statistical Tables**: Pandas DataFrames
- **Insights**: Text-based analysis summaries
- **Processed Data**: Scaled and selected features

## Technical Details

### Architecture
- **Class-based Design**: `AQIEdaAnalyzer` class for modularity
- **Streamlit Integration**: Native Streamlit components
- **Error Handling**: Graceful degradation for missing data
- **Performance**: Efficient data processing for large datasets

### Visualization Engine
- **Plotly**: Primary visualization library for interactivity
- **Responsive Design**: Adapts to different screen sizes
- **Dark Theme**: Consistent with main application
- **Export Capability**: Charts can be downloaded as images

### Data Processing
- **Missing Value Handling**: Forward fill and backfill strategies
- **Feature Scaling**: MinMax normalization (0-1 range)
- **Feature Selection**: Statistical significance testing
- **Time Series**: Proper temporal data handling

## Customization

### Adding New Analyses
1. Create new method in `AQIEdaAnalyzer` class
2. Add corresponding tab in main function
3. Integrate with existing data pipeline

### Modifying Visualizations
- Update Plotly figure configurations
- Modify color schemes and layouts
- Add new chart types as needed

### Data Sources
- Change `data_path` in `__init__` method
- Support additional file formats
- Implement data validation rules

## Troubleshooting

### Common Issues

#### Data Not Found
```
❌ Data file not found: dataEDA/merged_with_numerical_aqi.csv
```
**Solution**: Ensure data collection has been completed and files are in the correct location.

#### Import Errors
```
❌ EDA page module not found
```
**Solution**: Check that `eda_page.py` is in the same directory as the main app.

#### Memory Issues
```
MemoryError: Unable to allocate array
```
**Solution**: Reduce dataset size or implement data sampling for large datasets.

#### Visualization Errors
```
Error in time series analysis
```
**Solution**: Check data quality and ensure sufficient temporal coverage.

### Performance Optimization
- **Large Datasets**: Implement data sampling for initial analysis
- **Real-time Updates**: Cache analysis results
- **Memory Management**: Process data in chunks if needed

## Future Enhancements

### Planned Features
- **Real-time Analysis**: Live data streaming analysis
- **Advanced Statistics**: More sophisticated statistical tests
- **Export Functionality**: PDF reports and data exports
- **Custom Dashboards**: User-configurable analysis views
- **Machine Learning Integration**: Automated model recommendations

### Scalability Improvements
- **Database Integration**: Direct database connections
- **Caching**: Redis-based result caching
- **Async Processing**: Background analysis tasks
- **Distributed Computing**: Multi-node analysis capabilities

## Contributing

### Development Guidelines
1. **Code Style**: Follow PEP 8 standards
2. **Documentation**: Add docstrings for all methods
3. **Testing**: Include unit tests for new features
4. **Error Handling**: Implement comprehensive error handling
5. **Performance**: Optimize for large datasets

### Testing
```bash
# Run basic functionality test
python -c "from eda_page import AQIEdaAnalyzer; print('Import successful')"

# Test data loading
python -c "from eda_page import AQIEdaAnalyzer; a = AQIEdaAnalyzer(); print('Analyzer created')"
```

## Support

### Documentation
- **Code Comments**: Inline documentation
- **Method Docstrings**: Function descriptions
- **README**: This comprehensive guide
- **Examples**: Sample usage patterns

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and support
- **Contributions**: Pull requests and improvements

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: AQI Forecasting System Team

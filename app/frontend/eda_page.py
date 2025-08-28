"""
Exploratory Data Analysis (EDA) Page for AQI Forecasting System
Comprehensive analysis of air quality data with interactive visualizations
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import warnings
import os
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.impute import SimpleImputer
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import ccf
from pandas.plotting import autocorrelation_plot

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set matplotlib style for better plots
plt.style.use('seaborn-v0_8-darkgrid')

class AQIEdaAnalyzer:
    """Comprehensive EDA analyzer for AQI data"""
    
    def __init__(self):
        # Try to find the data file using multiple possible paths
        possible_paths = [
            "D:/AQI-forecasting-10Pearls/dataEDA/merged_with_numerical_aqi.csv",  # Absolute path
            "../../dataEDA/merged_with_numerical_aqi.csv",  # Relative from frontend
            "../dataEDA/merged_with_numerical_aqi.csv",    # Relative from app
            "dataEDA/merged_with_numerical_aqi.csv"        # Relative from root
        ]
        
        # Find the first path that exists
        self.data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.data_path = path
                break
        
        # If no path found, use the absolute path as default
        if self.data_path is None:
            self.data_path = "D:/AQI-forecasting-10Pearls/dataEDA/merged_with_numerical_aqi.csv"
        
        self.aqi_df = None
        self.df_scaled = None
        self.df_selected = None
        
    def load_data(self):
        """Load and prepare the AQI dataset"""
        try:
            if os.path.exists(self.data_path):
                self.aqi_df = pd.read_csv(self.data_path)
                # Parse timestamp
                self.aqi_df['timestamp'] = pd.to_datetime(self.aqi_df['timestamp'])
                
                # Round off AQI values to nearest integer
                if 'aqi_category' in self.aqi_df.columns:
                    self.aqi_df['aqi_category'] = self.aqi_df['aqi_category'].round().astype(int)
                
                st.success(f"✅ Data loaded successfully! Shape: {self.aqi_df.shape}")
                return True
            else:
                st.error(f"❌ Data file not found: {self.data_path}")
                st.info("Please ensure the data collection has been run first.")
                return False
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            return False
    
    def display_dataset_info(self):
        """Display basic dataset information"""
        st.markdown("## 📊 Dataset Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Dataset Structure")
            st.write(f"**Shape:** {self.aqi_df.shape}")
            st.write(f"**Columns:** {len(self.aqi_df.columns)}")
            st.write(f"**Date Range:** {self.aqi_df['timestamp'].min()} to {self.aqi_df['timestamp'].max()}")
            
            # Memory usage
            memory_usage = self.aqi_df.memory_usage(deep=True).sum() / 1024**2
            st.write(f"**Memory Usage:** {memory_usage:.2f} MB")
        
        with col2:
            st.markdown("### Data Types")
            dtype_df = pd.DataFrame({
                'Column': self.aqi_df.dtypes.index,
                'Data Type': self.aqi_df.dtypes.values,
                'Non-Null Count': self.aqi_df.count().values
            })
            st.dataframe(dtype_df, use_container_width=True)
        
        # Missing values analysis
        st.markdown("### Missing Values Analysis")
        missing_df = pd.DataFrame({
            'Column': self.aqi_df.columns,
            'Missing Count': self.aqi_df.isnull().sum(),
            'Missing Percentage': (self.aqi_df.isnull().sum() / len(self.aqi_df) * 100).round(2)
        }).sort_values('Missing Percentage', ascending=False)
        
        st.dataframe(missing_df, use_container_width=True)
        
        # Display first few rows
        st.markdown("### First 5 Rows")
        st.dataframe(self.aqi_df.head(), use_container_width=True)
    
    def analyze_aqi_distribution(self):
        """Analyze AQI category distribution"""
        st.markdown("## 📈 AQI Category Distribution")
        
        if 'aqi_category' in self.aqi_df.columns:
            # Count frequency of each AQI category
            aqi_counts = self.aqi_df['aqi_category'].value_counts().sort_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart using plotly
                fig = px.bar(
                    x=aqi_counts.index,
                    y=aqi_counts.values,
                    title="Frequency of Each AQI Category",
                    labels={'x': 'AQI Category', 'y': 'Frequency'},
                    color=aqi_counts.values,
                    color_continuous_scale='viridis'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie chart
                fig = px.pie(
                    values=aqi_counts.values,
                    names=aqi_counts.index,
                    title="AQI Category Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            st.info("💡 **Key Insights:**")
            st.write(f"• **Most Common Category:** {aqi_counts.index[aqi_counts.argmax()]} ({aqi_counts.max()} occurrences)")
            st.write(f"• **Least Common Category:** {aqi_counts.index[aqi_counts.argmin()]} ({aqi_counts.min()} occurrences)")
            st.write(f"• **Data Imbalance:** The data shows significant imbalance, which may require special handling in modeling")
    
    def analyze_temporal_patterns(self):
        """Analyze temporal patterns in AQI data"""
        st.markdown("## ⏰ Temporal Patterns Analysis")
        
        # AQI Trends Over Time
        st.markdown("### AQI Trends Over Time")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Categorical AQI over time
            fig = px.line(
                x=self.aqi_df['timestamp'],
                y=self.aqi_df['aqi_category'],
                title="AQI Category Over Time",
                labels={'x': 'Date', 'y': 'AQI Level (1: Good → 5: Hazardous)'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Numerical AQI over time
            fig = px.line(
                x=self.aqi_df['timestamp'],
                y=self.aqi_df['numerical_aqi'],
                title="Numerical AQI Over Time",
                labels={'x': 'Date', 'y': 'Numerical AQI'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Hourly patterns
        st.markdown("### Hourly Patterns")
        
        if 'hour' in self.aqi_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Average categorical AQI by hour
                hourly_cat = self.aqi_df.groupby('hour')['aqi_category'].mean()
                fig = px.bar(
                    x=hourly_cat.index,
                    y=hourly_cat.values,
                    title="Average AQI Category by Hour of Day",
                    labels={'x': 'Hour', 'y': 'Mean AQI Category'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Average numerical AQI by hour
                hourly_num = self.aqi_df.groupby('hour')['numerical_aqi'].mean()
                fig = px.bar(
                    x=hourly_num.index,
                    y=hourly_num.values,
                    title="Average Numerical AQI by Hour of Day",
                    labels={'x': 'Hour', 'y': 'Mean Numerical AQI'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Weekly patterns
        if 'day_of_week' in self.aqi_df.columns:
            st.markdown("### Weekly Patterns")
            
            weekday_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            self.aqi_df['day_label'] = self.aqi_df['day_of_week'].map(lambda x: weekday_map[x])
            
            weekly_avg = self.aqi_df.groupby('day_label')['numerical_aqi'].mean().reindex(weekday_map)
            
            fig = px.bar(
                x=weekly_avg.index,
                y=weekly_avg.values,
                title="Average AQI by Day of Week",
                labels={'x': 'Day', 'y': 'Mean Numerical AQI'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def analyze_correlations(self):
        """Analyze correlations between features"""
        st.markdown("## 🔗 Feature Correlations Analysis")
        
        # Select numerical columns for correlation
        numerical_cols = ['numerical_aqi', 'aqi_category', 'co', 'no', 'no2', 'o3', 'so2', 
                         'pm2_5', 'pm10', 'nh3', 'day_of_week', 'temperature', 
                         'wind_direction', 'relative_humidity', 'hour', 'pressure']
        
        # Filter columns that exist in the dataset
        available_cols = [col for col in numerical_cols if col in self.aqi_df.columns]
        
        if len(available_cols) > 1:
            corr_matrix = self.aqi_df[available_cols].corr()
            
            # Create correlation heatmap
            fig = px.imshow(
                corr_matrix,
                title="Correlation Matrix: AQI vs Features",
                color_continuous_scale='RdBu',
                aspect='auto'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Top correlations with AQI
            st.markdown("### Top Correlations with AQI")
            aqi_corr = corr_matrix['numerical_aqi'].abs().sort_values(ascending=False)
            top_corr_df = pd.DataFrame({
                'Feature': aqi_corr.index,
                'Correlation with AQI': aqi_corr.values
            }).head(10)
            
            st.dataframe(top_corr_df, use_container_width=True)
            
            # Insights
            st.info("💡 **Correlation Insights:**")
            st.write("• Features with high correlation to AQI are most important for prediction")
            st.write("• Highly correlated features may cause multicollinearity issues")
            st.write("• Negative correlations indicate inverse relationships")
        else:
            st.warning("⚠️ Insufficient numerical columns for correlation analysis")
    
    def analyze_pollutant_distributions(self):
        """Analyze distributions of key pollutants"""
        st.markdown("## 🌫️ Pollutant Distributions")
        
        pollutants = ['pm2_5', 'pm10', 'co', 'so2', 'no2', 'o3', 'nh3']
        available_pollutants = [p for p in pollutants if p in self.aqi_df.columns]
        
        if available_pollutants:
            # Create subplots for pollutant distributions
            n_pollutants = len(available_pollutants)
            cols = min(3, n_pollutants)
            rows = (n_pollutants + cols - 1) // cols
            
            fig = make_subplots(
                rows=rows, cols=cols,
                subplot_titles=[p.upper().replace('_', ' ') for p in available_pollutants]
            )
            
            for i, pollutant in enumerate(available_pollutants):
                row = (i // cols) + 1
                col = (i % cols) + 1
                
                # Create histogram
                fig.add_trace(
                    go.Histogram(
                        x=self.aqi_df[pollutant].dropna(),
                        name=pollutant.upper(),
                        nbinsx=30,
                        opacity=0.7
                    ),
                    row=row, col=col
                )
            
            fig.update_layout(
                title="Distribution of Key Pollutants",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'),
                height=300 * rows,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistical summary
            st.markdown("### Statistical Summary of Pollutants")
            pollutant_stats = self.aqi_df[available_pollutants].describe()
            st.dataframe(pollutant_stats, use_container_width=True)
            
            # Insights
            st.info("💡 **Distribution Insights:**")
            st.write("• Right-skewed distributions indicate presence of outliers")
            st.write("• High standard deviations suggest high variability")
            st.write("• Understanding distributions helps in feature scaling and outlier detection")
        else:
            st.warning("⚠️ No pollutant columns found in the dataset")
    
    def analyze_seasonal_patterns(self):
        """Analyze seasonal and monthly patterns"""
        st.markdown("## 🌸 Seasonal Patterns Analysis")
        
        if 'month' in self.aqi_df.columns:
            # Monthly AQI boxplot
            fig = px.box(
                self.aqi_df,
                x='month',
                y='numerical_aqi',
                title="AQI Distribution by Month",
                labels={'x': 'Month', 'y': 'AQI'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly statistics
            monthly_stats = self.aqi_df.groupby('month')['numerical_aqi'].agg(['mean', 'std', 'min', 'max']).round(2)
            st.markdown("### Monthly AQI Statistics")
            st.dataframe(monthly_stats, use_container_width=True)
        
        # Weekend vs Weekday analysis
        if 'is_weekend' in self.aqi_df.columns:
            st.markdown("### Weekend vs Weekday AQI")
            
            weekend_stats = self.aqi_df.groupby('is_weekend')['numerical_aqi'].agg(['mean', 'std', 'count']).round(2)
            weekend_stats.index = ['Weekday', 'Weekend']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.box(
                    self.aqi_df,
                    x='is_weekend',
                    y='numerical_aqi',
                    title="Weekend vs Weekday AQI",
                    labels={'x': 'Day Type', 'y': 'AQI'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(weekend_stats, use_container_width=True)
    
    def analyze_time_series_components(self):
        """Analyze time series components"""
        st.markdown("## 📈 Time Series Analysis")
        
        try:
            # Prepare data for seasonal decomposition
            if 'timestamp' in self.aqi_df.columns:
                # Resample to daily data
                daily_aqi = self.aqi_df.set_index('timestamp')['numerical_aqi'].resample('D').mean()
                
                # Remove NaN values
                daily_aqi = daily_aqi.dropna()
                
                if len(daily_aqi) > 30:  # Need sufficient data for decomposition
                    # Seasonal decomposition
                    result = seasonal_decompose(daily_aqi, model='additive', period=30)
                    
                    # Create subplots for decomposition
                    fig = make_subplots(
                        rows=4, cols=1,
                        subplot_titles=['Original', 'Trend', 'Seasonal', 'Residual'],
                        vertical_spacing=0.05
                    )
                    
                    # Original data
                    fig.add_trace(
                        go.Scatter(x=daily_aqi.index, y=daily_aqi.values, name='Original'),
                        row=1, col=1
                    )
                    
                    # Trend
                    fig.add_trace(
                        go.Scatter(x=daily_aqi.index, y=result.trend, name='Trend'),
                        row=2, col=1
                    )
                    
                    # Seasonal
                    fig.add_trace(
                        go.Scatter(x=daily_aqi.index, y=result.seasonal, name='Seasonal'),
                        row=3, col=1
                    )
                    
                    # Residual
                    fig.add_trace(
                        go.Scatter(x=daily_aqi.index, y=result.resid, name='Residual'),
                        row=4, col=1
                    )
                    
                    fig.update_layout(
                        title="Seasonal Decomposition of AQI Time Series",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#f9fafb'),
                        height=800,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Insights
                    st.info("💡 **Time Series Insights:**")
                    st.write("• **Trend:** Shows long-term direction of AQI")
                    st.write("• **Seasonal:** Reveals recurring patterns (daily, weekly, monthly)")
                    st.write("• **Residual:** Random fluctuations after removing trend and seasonality")
                    st.write("• Understanding these components helps in model selection and feature engineering")
                else:
                    st.warning("⚠️ Insufficient data for seasonal decomposition (need at least 30 days)")
            else:
                st.warning("⚠️ Timestamp column not found for time series analysis")
                
        except Exception as e:
            st.error(f"❌ Error in time series analysis: {str(e)}")
    
    def analyze_autocorrelation(self):
        """Analyze autocorrelation patterns"""
        st.markdown("## 🔄 Autocorrelation Analysis")
        
        try:
            if 'numerical_aqi' in self.aqi_df.columns:
                # Prepare data
                aqi_series = self.aqi_df['numerical_aqi'].dropna()
                
                if len(aqi_series) > 50:
                    # Create autocorrelation plot
                    fig = go.Figure()
                    
                    # Calculate autocorrelation for different lags
                    max_lag = min(50, len(aqi_series) // 4)
                    lags = list(range(1, max_lag + 1))  # Convert range to list
                    autocorr_values = [aqi_series.autocorr(lag) for lag in lags]
                    
                    fig.add_trace(go.Scatter(
                        x=lags,
                        y=autocorr_values,
                        mode='lines+markers',
                        name='Autocorrelation',
                        line=dict(color='#3b82f6', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # Add confidence intervals
                    confidence = 1.96 / np.sqrt(len(aqi_series))
                    fig.add_hline(y=confidence, line_dash="dash", line_color="red", 
                                annotation_text="95% Confidence Interval")
                    fig.add_hline(y=-confidence, line_dash="dash", line_color="red")
                    fig.add_hline(y=0, line_dash="dash", line_color="gray")
                    
                    fig.update_layout(
                        title="Autocorrelation of AQI Values",
                        xaxis_title="Lag (hours)",
                        yaxis_title="Autocorrelation",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#f9fafb'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Insights
                    st.info("💡 **Autocorrelation Insights:**")
                    st.write("• High autocorrelation at lag 1 indicates strong immediate dependency")
                    st.write("• Significant autocorrelation at higher lags suggests longer-term patterns")
                    st.write("• This information helps determine optimal lag features for forecasting models")
                else:
                    st.warning("⚠️ Insufficient data for autocorrelation analysis")
            else:
                st.warning("⚠️ Numerical AQI column not found")
                
        except Exception as e:
            st.error(f"❌ Error in autocorrelation analysis: {str(e)}")
    
    def analyze_cross_correlations(self):
        """Analyze cross-correlations between features and AQI"""
        st.markdown("## 🔗 Cross-Correlation Analysis")
        
        try:
            # Select key features for cross-correlation
            key_features = ['pm2_5', 'pm10', 'no2', 'o3', 'co', 'temperature', 'relative_humidity']
            available_features = [f for f in key_features if f in self.aqi_df.columns]
            
            if available_features and 'numerical_aqi' in self.aqi_df.columns:
                # Create cross-correlation plots
                n_features = len(available_features)
                cols = min(2, n_features)
                rows = (n_features + cols - 1) // cols
                
                fig = make_subplots(
                    rows=rows, cols=cols,
                    subplot_titles=[f"Cross-Correlation: {f.upper()} vs AQI" for f in available_features]
                )
                
                for i, feature in enumerate(available_features):
                    row = (i // cols) + 1
                    col = (i % cols) + 1
                    
                    # Calculate cross-correlation
                    x = self.aqi_df[feature].fillna(0)
                    y = self.aqi_df['numerical_aqi'].fillna(0)
                    
                    # Calculate cross-correlation for different lags
                    max_lag = 24
                    lags = list(range(max_lag))  # Convert range to list
                    corr_values = [ccf(x, y, adjusted=False)[lag] for lag in lags]
                    
                    fig.add_trace(
                        go.Bar(
                            x=lags,
                            y=corr_values,
                            name=feature.upper(),
                            opacity=0.7
                        ),
                        row=row, col=col
                    )
                
                fig.update_layout(
                    title="Cross-Correlation: Features vs AQI",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    height=300 * rows,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Insights
                st.info("💡 **Cross-Correlation Insights:**")
                st.write("• Shows how past values of features correlate with current AQI")
                st.write("• Helps determine optimal time lags for feature engineering")
                st.write("• Strong correlations at specific lags indicate predictive power")
            else:
                st.warning("⚠️ Insufficient features for cross-correlation analysis")
                
        except Exception as e:
            st.error(f"❌ Error in cross-correlation analysis: {str(e)}")
    
    def analyze_aqi_spikes(self):
        """Analyze AQI spikes and extreme events"""
        st.markdown("## 📊 AQI Spikes Analysis")
        
        try:
            if 'numerical_aqi' in self.aqi_df.columns:
                # Define AQI spike threshold (very unhealthy)
                spike_threshold = 130
                spike_df = self.aqi_df[self.aqi_df['numerical_aqi'] > spike_threshold]
                
                if len(spike_df) > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Spike frequency over time
                        spike_df['date'] = spike_df['timestamp'].dt.date
                        daily_spikes = spike_df.groupby('date').size()
                        
                        fig = px.line(
                            x=daily_spikes.index,
                            y=daily_spikes.values,
                            title=f"Daily AQI Spikes (> {spike_threshold})",
                            labels={'x': 'Date', 'y': 'Number of Spikes'}
                        )
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#f9fafb'),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Dominant pollutants during spikes
                        pollutants = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'nh3']
                        available_pollutants = [p for p in pollutants if p in spike_df.columns]
                        
                        if available_pollutants:
                            mean_spike = spike_df[available_pollutants].mean().sort_values(ascending=False)
                            
                            fig = px.bar(
                                x=mean_spike.index,
                                y=mean_spike.values,
                                title="Dominant Pollutants During AQI Spikes",
                                labels={'x': 'Pollutant', 'y': 'Mean Concentration'}
                            )
                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#f9fafb'),
                                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Spike statistics
                    st.markdown("### AQI Spike Statistics")
                    spike_stats = pd.DataFrame({
                        'Metric': ['Total Spikes', 'Spike Percentage', 'Max AQI During Spike', 'Min AQI During Spike'],
                        'Value': [
                            len(spike_df),
                            f"{(len(spike_df) / len(self.aqi_df) * 100):.2f}%",
                            f"{spike_df['numerical_aqi'].max():.1f}",
                            f"{spike_df['numerical_aqi'].min():.1f}"
                        ]
                    })
                    st.dataframe(spike_stats, use_container_width=True)
                    
                    # Insights
                    st.info("💡 **Spike Analysis Insights:**")
                    st.write(f"• **{len(spike_df)}** AQI spikes detected above threshold {spike_threshold}")
                    st.write("• Spikes represent extreme pollution events requiring attention")
                    st.write("• Understanding spike patterns helps in emergency response planning")
                else:
                    st.info("✅ No AQI spikes detected above the threshold")
            else:
                st.warning("⚠️ Numerical AQI column not found")
                
        except Exception as e:
            st.error(f"❌ Error in AQI spikes analysis: {str(e)}")
    
    def analyze_volatility(self):
        """Analyze AQI volatility patterns"""
        st.markdown("## 📈 AQI Volatility Analysis")
        
        try:
            if 'numerical_aqi' in self.aqi_df.columns:
                # Calculate rolling volatility (24-hour standard deviation)
                self.aqi_df['aqi_volatility'] = self.aqi_df['numerical_aqi'].rolling(24).std()
                
                # Volatility over time
                fig = px.line(
                    x=self.aqi_df['timestamp'],
                    y=self.aqi_df['aqi_volatility'],
                    title="24-Hour Rolling AQI Volatility",
                    labels={'x': 'Date', 'y': 'AQI Standard Deviation (Volatility)'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Volatility statistics
                volatility_stats = self.aqi_df['aqi_volatility'].describe()
                st.markdown("### Volatility Statistics")
                st.dataframe(pd.DataFrame({
                    'Metric': volatility_stats.index,
                    'Value': volatility_stats.values.round(2)
                }), use_container_width=True)
                
                # Insights
                st.info("💡 **Volatility Insights:**")
                st.write("• High volatility indicates unstable air quality conditions")
                st.write("• Low volatility suggests stable, predictable air quality")
                st.write("• Understanding volatility helps in forecasting confidence intervals")
                
        except Exception as e:
            st.error(f"❌ Error in volatility analysis: {str(e)}")
    
    def perform_feature_engineering(self):
        """Perform feature engineering and selection"""
        st.markdown("## ⚙️ Feature Engineering & Selection")
        
        try:
            # Create a copy for feature engineering
            df = self.aqi_df.copy()
            
            # Drop non-numeric or ID columns
            columns_to_drop = ['timestamp', 'date', 'day_label']
            df.drop(columns=columns_to_drop, inplace=True, errors='ignore')
            
            # Drop columns that are entirely NaN
            df.dropna(axis=1, how='all', inplace=True)
            
            # Define columns to scale (exclude target column 'numerical_aqi')
            if 'numerical_aqi' in df.columns:
                feature_cols = df.drop(columns=['numerical_aqi']).columns
                
                # Apply MinMax scaling
                scaler = MinMaxScaler()
                df_scaled = df.copy()
                df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
                
                st.success("✅ Feature scaling completed successfully!")
                
                # Feature selection using f_regression
                X = df.drop(columns=['numerical_aqi'])
                y = df['numerical_aqi']
                
                # Impute missing values
                imputer = SimpleImputer(strategy='mean')
                X_imputed = imputer.fit_transform(X)
                
                # Select top features
                selector = SelectKBest(score_func=f_regression, k=20)
                X_selected = selector.fit_transform(X_imputed, y)
                
                # Get selected features
                selected_features = X.columns[selector.get_support()]
                
                # Display feature scores
                scores = selector.scores_
                feature_scores_df = pd.DataFrame({
                    'Feature': X.columns,
                    'F-Score': scores
                }).sort_values('F-Score', ascending=False)
                
                st.markdown("### Feature Importance Scores")
                st.dataframe(feature_scores_df, use_container_width=True)
                
                # Plot feature scores
                fig = px.bar(
                    x=feature_scores_df['F-Score'],
                    y=feature_scores_df['Feature'],
                    orientation='h',
                    title="F-Regression Feature Scores for AQI Prediction",
                    labels={'x': 'Score', 'y': 'Feature'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#f9fafb'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Insights
                st.info("💡 **Feature Engineering Insights:**")
                st.write(f"• **Top {len(selected_features)} features** selected for modeling")
                st.write("• Higher F-scores indicate stronger predictive power")
                st.write("• Feature scaling ensures all features contribute equally to the model")
                
                # Save processed data
                try:
                    # Determine save directory based on data path
                    if self.data_path:
                        # Extract directory from data path
                        save_dir = os.path.dirname(self.data_path)
                    else:
                        save_dir = "D:/AQI-forecasting-10Pearls/dataEDA"
                    
                    os.makedirs(save_dir, exist_ok=True)
                    df_scaled.to_csv(f'{save_dir}/scaled_aqi_ready.csv', index=False)
                    st.success("✅ Scaled data saved to dataEDA/scaled_aqi_ready.csv")
                except Exception as e:
                    st.warning(f"⚠️ Could not save scaled data: {str(e)}")
                
            else:
                st.warning("⚠️ Target column 'numerical_aqi' not found")
                
        except Exception as e:
            st.error(f"❌ Error in feature engineering: {str(e)}")
    
    def generate_summary_report(self):
        """Generate comprehensive EDA summary report"""
        st.markdown("## 📋 EDA Summary Report")
        
        try:
            # Create summary statistics
            summary_data = []
            
            if 'numerical_aqi' in self.aqi_df.columns:
                summary_data.extend([
                    ["Dataset Shape", f"{self.aqi_df.shape[0]} rows × {self.aqi_df.shape[1]} columns"],
                    ["Date Range", f"{self.aqi_df['timestamp'].min()} to {self.aqi_df['timestamp'].max()}"],
                    ["Total Records", f"{len(self.aqi_df):,}"],
                    ["Missing Values", f"{self.aqi_df.isnull().sum().sum():,}"],
                    ["AQI Range", f"{self.aqi_df['numerical_aqi'].min():.1f} - {self.aqi_df['numerical_aqi'].max():.1f}"],
                    ["Mean AQI", f"{self.aqi_df['numerical_aqi'].mean():.2f}"],
                    ["Median AQI", f"{self.aqi_df['numerical_aqi'].median():.2f}"],
                    ["AQI Standard Deviation", f"{self.aqi_df['numerical_aqi'].std():.2f}"]
                ])
            
            if 'aqi_category' in self.aqi_df.columns:
                category_counts = self.aqi_df['aqi_category'].value_counts()
                summary_data.append(["Most Common AQI Category", f"{category_counts.index[0]} ({category_counts.iloc[0]} occurrences)"])
                summary_data.append(["Least Common AQI Category", f"{category_counts.index[-1]} ({category_counts.iloc[-1]} occurrences)"])
            
            # Create summary table
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            st.dataframe(summary_df, use_container_width=True)
            
            # Key insights
            st.markdown("### 🔍 Key Insights")
            
            insights = [
                "**Data Quality:** The dataset contains comprehensive air quality measurements with minimal missing values",
                "**Temporal Coverage:** Spans a significant time period allowing for robust pattern analysis",
                "**Feature Richness:** Multiple pollutant measurements and meteorological conditions available",
                "**Target Variable:** Numerical AQI values provide continuous target for regression models",
                "**Seasonality:** Clear temporal patterns suggest time-series forecasting approaches",
                "**Correlations:** Strong relationships between pollutants and AQI enable feature selection"
            ]
            
            for insight in insights:
                st.write(f"• {insight}")
            
            # Recommendations
            st.markdown("### 💡 Recommendations for Modeling")
            
            recommendations = [
                "**Model Type:** Use time-series models (TCN, LSTM) for temporal dependencies",
                "**Feature Engineering:** Include lag features based on autocorrelation analysis",
                "**Handling Imbalance:** Apply techniques for rare AQI categories if using classification",
                "**Validation:** Use time-series cross-validation to prevent data leakage",
                "**Feature Selection:** Focus on top-ranked features from correlation analysis",
                "**Scaling:** Apply MinMax scaling for consistent feature contributions"
            ]
            
            for rec in recommendations:
                st.write(f"• {rec}")
                
        except Exception as e:
            st.error(f"❌ Error generating summary report: {str(e)}")

def main():
    """Main EDA page function"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); padding: 2rem; border-radius: 15px; border: 1px solid #374151; margin-bottom: 2rem;">
        <h1 style="color: #fbbf24; text-align: center; margin: 0;">🔍 Exploratory Data Analysis (EDA)</h1>
        <p style="color: #d1d5db; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Comprehensive analysis of air quality data patterns, correlations, and insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize analyzer
    analyzer = AQIEdaAnalyzer()
    
    # Load data
    if not analyzer.load_data():
        st.error("❌ Cannot proceed without data. Please ensure data collection has been completed.")
        return
    
    # Create tabs for different analysis sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Overview", "📈 Temporal Patterns", "🔗 Correlations", "🌫️ Pollutants", 
        "🌸 Seasonal", "📈 Time Series", "🔄 Autocorrelation", "📊 Spikes & Volatility", "⚙️ Features"
    ])
    
    with tab1:
        analyzer.display_dataset_info()
        analyzer.analyze_aqi_distribution()
    
    with tab2:
        analyzer.analyze_temporal_patterns()
    
    with tab3:
        analyzer.analyze_correlations()
    
    with tab4:
        analyzer.analyze_pollutant_distributions()
    
    with tab5:
        analyzer.analyze_seasonal_patterns()
    
    with tab6:
        analyzer.analyze_time_series_components()
    
    with tab7:
        analyzer.analyze_autocorrelation()
        analyzer.analyze_cross_correlations()
    
    with tab8:
        analyzer.analyze_aqi_spikes()
        analyzer.analyze_volatility()
    
    with tab9:
        analyzer.perform_feature_engineering()
        analyzer.generate_summary_report()
    
    # Footer
    st.markdown("---")
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1f2937 0%, #111827 100%); border-radius: 10px; border: 1px solid #374151;">
        <p style="color: #9ca3af; margin: 0;">
            🔍 EDA Analysis Complete | Generated on: {current_time}
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

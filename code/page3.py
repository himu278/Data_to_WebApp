import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Load the data
@st.cache_data
def load_data():
    file_path = "D:/Project/Data_to_WebApp/data/Job_Posting_Analytics_8_Occupations_in_3194_Counties_5318.xls"
    df = pd.read_excel(file_path, sheet_name="Job Postings Timeseries", engine='xlrd', skiprows=2)
    df = df.dropna(subset=["Month"])
    df["Month"] = pd.to_datetime(df["Month"], format="%b %Y")
    df["Unique Postings"] = pd.to_numeric(df["Unique Postings"], errors="coerce")
    df = df.sort_values("Month").reset_index(drop=True)
    return df

df = load_data()

# Streamlit App Layout
st.title("Job Postings Time Series Dashboard")
st.write("Visualize monthly job posting trends by time.")

# Date Range Picker
min_date = df["Month"].min().date()
max_date = df["Month"].max().date()

start_date, end_date = st.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Convert selected dates to datetime64[ns]
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data based on selected date range
filtered_df = df[(df["Month"] >= start_date) & (df["Month"] <= end_date)]

# Display raw data option
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df)

# Plot the raw data
st.subheader("Raw Time Series of Unique Job Postings")
plt.figure(figsize=(10, 6))
plt.plot(filtered_df["Month"], filtered_df["Unique Postings"])
plt.title("Unique Job Postings Over Time")
plt.xlabel("Month")
plt.ylabel("Unique Postings")
plt.grid(True)
st.pyplot(plt)

# Preprocessing: Take log of the data for stabilization
filtered_df['log_postings'] = np.log(filtered_df['Unique Postings'])

# Interactive SARIMA Parameters
st.sidebar.subheader("SARIMA Model Parameters")
p = st.sidebar.slider('AR (p)', 0, 5, 1)
d = st.sidebar.slider('I (d)', 0, 2, 1)
q = st.sidebar.slider('MA (q)', 0, 5, 1)

# Seasonal components
seasonal_p = st.sidebar.slider('Seasonal AR (P)', 0, 3, 1)
seasonal_d = st.sidebar.slider('Seasonal I (D)', 0, 1, 1)
seasonal_q = st.sidebar.slider('Seasonal MA (Q)', 0, 3, 1)
seasonal_periods = st.sidebar.slider('Seasonality Period (s)', 1, 12, 12)  # Typically 12 for monthly data

# SARIMA Model: Fit a SARIMAX model with interactive parameters
sarima_model = SARIMAX(filtered_df['log_postings'], 
                       order=(p, d, q),  # AR, I, MA terms
                       seasonal_order=(seasonal_p, seasonal_d, seasonal_q, seasonal_periods),  # Seasonal components
                       enforce_stationarity=False, 
                       enforce_invertibility=False)

results = sarima_model.fit()

# Forecasting period - Allow the user to select the number of months to forecast
forecast_steps = st.slider('Forecast Steps (Months)', 1, 24, 12)

# Forecast the next 'forecast_steps' months
forecast = results.get_forecast(steps=forecast_steps)
forecast_index = pd.date_range(start=filtered_df['Month'].iloc[-1], periods=forecast_steps+1, freq='M')[1:]

# Convert forecasted values from log scale back to original scale
forecast_values = np.exp(forecast.predicted_mean)

# Plot the forecast alongside the historical data
st.subheader(f"SARIMA Forecast for Unique Job Postings (Next {forecast_steps} months)")
plt.figure(figsize=(10, 6))
plt.plot(filtered_df["Month"], filtered_df["Unique Postings"], label="Actual")
plt.plot(forecast_index, forecast_values, label="Forecast", linestyle='dashed', color='red')
plt.title("Job Postings with SARIMA Forecast")
plt.xlabel("Month")
plt.ylabel("Unique Postings")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# Optional: Posting Intensity table
if st.checkbox("Show Posting Intensity Table"):
    st.dataframe(filtered_df[["Month", "Posting Intensity"]].reset_index(drop=True))

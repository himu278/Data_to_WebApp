import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
st.write("""
    This app allows you to visualize job posting trends over time and forecast future job postings using a SARIMA model.
    You can filter the data based on a custom date range, adjust model parameters, and see forecasts for job postings.
""")

# Date Range Picker
st.write("### Step 1: Filter the Data by Date Range")
st.write("Select the start and end dates for the data you'd like to analyze.")
min_date = df["Month"].min().date()
max_date = df["Month"].max().date()

start_date, end_date = st.date_input(
    "Select the date range for your analysis:",
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
if st.checkbox("Show Raw Data (within selected date range)", help="Check this box to view the data table for the selected period."):
    st.dataframe(filtered_df)

# Plot the raw data
st.subheader("Raw Time Series of Unique Job Postings")
st.write("This plot shows the raw job postings trend over time, based on the selected date range.")
fig = go.Figure()

# Add trace for the actual job postings
fig.add_trace(go.Scatter(
    x=filtered_df['Month'],
    y=filtered_df['Unique Postings'],
    mode='lines+markers',
    name='Actual Job Postings',
    text=filtered_df['Unique Postings'],  # Tooltip with unique postings value
    hovertemplate='<b>%{x}</b><br>Unique Postings: %{text}<extra></extra>',  # Hover info
))

fig.update_layout(
    title="Unique Job Postings Over Time",
    xaxis_title="Month",
    yaxis_title="Unique Postings",
    hovermode="closest",  # Show the hover details closest to the cursor
    template="plotly_dark"
)

st.plotly_chart(fig)

# Preprocessing: Take log of the data for stabilization
filtered_df['log_postings'] = np.log(filtered_df['Unique Postings'])

# Interactive SARIMA Parameters
st.sidebar.subheader("SARIMA Model Parameters")
st.sidebar.write("Use these sliders to adjust the SARIMA model parameters. Experiment with different values to observe the effect on the forecast.")

p = st.sidebar.slider('AR (p)', 0, 5, 1, help="The AR parameter controls the autoregressive part of the model.")
d = st.sidebar.slider('I (d)', 0, 2, 1, help="The I parameter controls the differencing of the data to make it stationary.")
q = st.sidebar.slider('MA (q)', 0, 5, 1, help="The MA parameter controls the moving average part of the model.")

# Seasonal components
seasonal_p = st.sidebar.slider('Seasonal AR (P)', 0, 3, 1, help="The seasonal AR parameter controls the seasonal autoregressive part.")
seasonal_d = st.sidebar.slider('Seasonal I (D)', 0, 1, 1, help="The seasonal I parameter controls seasonal differencing.")
seasonal_q = st.sidebar.slider('Seasonal MA (Q)', 0, 3, 1, help="The seasonal MA parameter controls the seasonal moving average.")
seasonal_periods = st.sidebar.slider('Seasonality Period (s)', 1, 12, 12, help="The period (months) for seasonality. Typically 12 for monthly data.")

# Perform Grid Search over different SARIMA configurations
best_aic = float('inf')
best_order = None
best_seasonal_order = None
best_model = None

# Try different combinations of AR, I, MA, and seasonal parameters
for p in range(0, 3):  # Trying AR values from 0 to 2
    for d in range(0, 2):  # Trying I values from 0 to 1
        for q in range(0, 3):  # Trying MA values from 0 to 2
            for seasonal_p in range(0, 2):  # Seasonal AR values
                for seasonal_q in range(0, 2):  # Seasonal MA values
                    try:
                        sarima_model = SARIMAX(filtered_df['log_postings'], 
                                               order=(p, d, q),  # AR, I, MA terms
                                               seasonal_order=(seasonal_p, seasonal_d, seasonal_q, seasonal_periods),  # Seasonal components
                                               enforce_stationarity=False, 
                                               enforce_invertibility=False)

                        results = sarima_model.fit(disp=False)
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_order = (p, d, q)
                            best_seasonal_order = (seasonal_p, seasonal_d, seasonal_q, seasonal_periods)
                            best_model = results
                    except:
                        continue

# Output the best SARIMA parameters
st.write(f"### Best SARIMA Parameters Found:")
st.write(f"- AR, I, MA = {best_order}")
st.write(f"- Seasonal AR, I, MA = {best_seasonal_order}")
st.write(f"- Best AIC: {best_aic}")

# Forecasting period - Allow the user to select the number of months to forecast
forecast_steps = st.slider('Forecast Steps (Months)', 1, 24, 12, help="Select how many months into the future you want the forecast.")

# Forecast the next 'forecast_steps' months
forecast = best_model.get_forecast(steps=forecast_steps)
forecast_index = pd.date_range(start=filtered_df['Month'].iloc[-1], periods=forecast_steps+1, freq='M')[1:]

# Convert forecasted values from log scale back to original scale
forecast_values = np.exp(forecast.predicted_mean)

# Plot the forecast alongside the historical data using Plotly
st.subheader(f"SARIMA Forecast for Unique Job Postings (Next {forecast_steps} months)")
show_forecast = st.checkbox("Show Forecast Plot", value=True, help="Toggle to display or hide the forecast plot.")

if show_forecast:
    fig = go.Figure()

    # Add trace for actual job postings
    fig.add_trace(go.Scatter(
        x=filtered_df['Month'],
        y=filtered_df['Unique Postings'],
        mode='lines+markers',
        name='Actual Job Postings',
        text=filtered_df['Unique Postings'],
        hovertemplate='<b>%{x}</b><br>Unique Postings: %{text}<extra></extra>',
    ))

    # Add trace for forecasted values
    fig.add_trace(go.Scatter(
        x=forecast_index,
        y=forecast_values,
        mode='lines+markers',
        name='Forecast',
        line=dict(dash='dash', color='red'),
        text=forecast_values,
        hovertemplate='<b>%{x}</b><br>Forecasted Postings: %{text}<extra></extra>',
    ))

    fig.update_layout(
        title="Job Postings with SARIMA Forecast",
        xaxis_title="Month",
        yaxis_title="Unique Postings",
        hovermode="closest",
        template="plotly_dark"
    )

    st.plotly_chart(fig)

# Option to download the forecast data
if st.button("Download Forecast Data as CSV"):
    forecast_df = pd.DataFrame({
        'Date': forecast_index,
        'Forecasted Unique Postings': forecast_values
    })
    st.download_button(label="Download CSV", data=forecast_df.to_csv(index=False), file_name="forecasted_job_postings.csv", mime="text/csv")

# Optional: Posting Intensity table
if st.checkbox("Show Posting Intensity Table"):
    st.dataframe(filtered_df[["Month", "Posting Intensity"]].reset_index(drop=True))

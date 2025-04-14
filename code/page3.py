import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Load the data
@st.cache_data
def load_data():
    file_path = "D:/Project/Data_to_WebApp/data/Job_Posting_Analytics_8_Occupations_in_3194_Counties_5318.xls"
    df_jpt = pd.read_excel(file_path, sheet_name="Job Postings Timeseries", engine='xlrd', skiprows=2)
    df_jpt = df_jpt.dropna(subset=["Month"])
    df_jpt["Month"] = pd.to_datetime(df_jpt["Month"], format="%b %Y")
    df_jpt["Unique Postings"] = pd.to_numeric(df_jpt["Unique Postings"], errors="coerce")
    df_jpt = df_jpt.sort_values("Month").reset_index(drop=True)
    return df_jpt

df_jpt = load_data()

# Professional Header using HTML and CSS
st.markdown("""
    <style>
        /* General styles for the page */
        body {
            font-family: 'Arial', sans-serif;
            color: #2c3e50;
            background-color: #ecf0f1;
        }
        .header {
            text-align: center;
            padding: 40px;
            background-color: #2c3e50;
            color: white;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 36px;  /* Smaller font size */
            font-weight: 700;
            letter-spacing: 3px;
            text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.2);
        }
        .header p {
            font-size: 18px;
            margin-top: 10px;
            font-weight: 400;
            color: #ecf0f1;
        }

        .section-header {
            font-size: 24px;
            font-weight: 600;
            margin-top: 30px;
            color: #34495e;
        }

        .description {
            font-size: 16px;
            color: #7f8c8d;
            margin-bottom: 30px;
        }

        .stSlider {
            margin-top: 20px;
        }

        .stSelectbox, .stDateInput, .stCheckbox {
            margin-bottom: 20px;
        }

        .stMarkdown {
            font-size: 16px;
        }

        .stButton {
            margin-top: 20px;
        }

        /* Animation styles */
        .fadeIn {
            animation: fadeIn 1.5s ease-in-out;
        }

        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
    </style>
    <div class="header fadeIn">
        <h1>Job Postings Time Series Analysis</h1>
        <p>Explore and analyze trends in job postings over time with detailed visualizations and forecasts.</p>
    </div>
""", unsafe_allow_html=True)

# Streamlit App Layout
st.write("""
    This tool allows you to explore job posting trends over time and forecast future postings using a SARIMA model.
    You can filter the data by selecting a custom date range, fine-tune the model parameters, and view projected job posting trends.
    The SARIMA model allows us to predict future data points based on past trends, considering both seasonality and trends in the data.
""")

# Date Range Picker
st.write("### Filter the Data by Date Range")
st.write("Select the start and end dates for the data you'd like to analyze.")
min_date = df_jpt["Month"].min().date()
max_date = df_jpt["Month"].max().date()

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
filtered_df_jpt = df_jpt[(df_jpt["Month"] >= start_date) & (df_jpt["Month"] <= end_date)]

# Display raw data option
if st.checkbox("Show Raw Data (within selected date range)", help="Check this box to view the data table for the selected period."):
    st.dataframe(filtered_df_jpt)

# Plot the raw data
st.subheader("Raw Time Series of Unique Job Postings")
st.write("This plot shows the raw job postings trend over time, based on the selected date range.")
fig = go.Figure()

# Add trace for the actual job postings
fig.add_trace(go.Scatter(
    x=filtered_df_jpt['Month'],
    y=filtered_df_jpt['Unique Postings'],
    mode='lines+markers',
    name='Actual Job Postings',
    text=filtered_df_jpt['Unique Postings'],  # Tooltip with unique postings value
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
filtered_df_jpt['log_postings'] = np.log(filtered_df_jpt['Unique Postings'])

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
                        sarima_model = SARIMAX(filtered_df_jpt['log_postings'], 
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
forecast_index = pd.date_range(start=filtered_df_jpt['Month'].iloc[-1], periods=forecast_steps+1, freq='M')[1:]

# Convert forecasted values from log scale back to original scale
forecast_values = np.exp(forecast.predicted_mean)

# Plot the forecast alongside the historical data using Plotly
st.subheader(f"SARIMA Forecast for Unique Job Postings (Next {forecast_steps} months)")
show_forecast = st.checkbox("Show Forecast Plot", value=True, help="Toggle to display or hide the forecast plot.")

if show_forecast:
    fig = go.Figure()

    # Add trace for actual job postings
    fig.add_trace(go.Scatter(
        x=filtered_df_jpt['Month'],
        y=filtered_df_jpt['Unique Postings'],
        mode='lines+markers',
        name='Actual Job Postings',
        text=filtered_df_jpt['Unique Postings'],
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
    forecast_df_jpt = pd.DataFrame({
        'Date': forecast_index,
        'Forecasted Unique Postings': forecast_values
    })
    st.download_button(label="Download CSV", data=forecast_df_jpt.to_csv(index=False), file_name="forecasted_job_postings.csv", mime="text/csv")

# **Add Expandable Description Section**
with st.expander("Understanding the Results 📝"):
    st.write("""
    ### Job Postings Time Series:
    - The primary graph above represents the **actual job postings** over time.
    - The **X-axis** shows the **months**, while the **Y-axis** shows the **number of job postings**.
    - The trend line helps visualize how the job postings have evolved over the period.

    ### What is SARIMA?
    - **SARIMA (Seasonal ARIMA)** is a time series forecasting model that captures the patterns of seasonality and trends in historical data.
    - This model tries to predict future data points based on the observed patterns in the historical data.
    - It uses three key parameters: **AR (AutoRegressive)**, **I (Integrated)**, and **MA (Moving Average)** for non-seasonal data, and similar seasonal components for modeling seasonality.

    ### How to Interpret the Forecast Plot:
    - **Actual Job Postings**: The plot represents the actual number of job postings over time.
    - **Forecasted Job Postings**: The dashed red line shows the forecasted values for the next 12 months (or as per your selection).
    - **Forecast Period**: This forecast predicts the future trend based on the historical data. The number of months you want to forecast can be adjusted using the "Forecast Steps" slider in the sidebar.

    ### SARIMA Model Parameters:
    - **AR (p)**: Controls the relationship between an observation and several lagged observations.
    - **I (d)**: Defines the differencing method used to make the series stationary (eliminates trends).
    - **MA (q)**: Models the relationship between an observation and a lagged forecast error.
    - **Seasonal AR, I, MA (P, D, Q)**: These seasonal components are responsible for modeling periodic fluctuations over time (e.g., yearly cycles, monthly patterns).

    ### How to Use the Model:
    - You can use the sliders in the sidebar to experiment with different values for AR, I, MA, and the seasonal components.
    - **Higher AR or MA values** might make the model more sensitive to trends, while **lower values** may generalize the forecast.
    - By adjusting the seasonal periods, you can model different seasonal patterns, such as **yearly or monthly cycles**.

    ### Download Forecast Data:
    - You can download the forecasted data as a CSV file to further analyze or use in reports. Just click the "Download Forecast Data as CSV" button below the forecast plot.

    ### Tips for Interpreting the Forecast:
    - If your forecast looks very different from actual postings, you might need to adjust the model parameters.
    - Look for any **seasonal trends**—for example, job postings might increase in certain months of the year, which the model should capture.
    """)

# Optional: Posting Intensity table
if st.checkbox("Show Posting Intensity Table"):
    st.dataframe(filtered_df_jpt[["Month", "Posting Intensity"]].reset_index(drop=True))

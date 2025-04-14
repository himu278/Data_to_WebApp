import streamlit as st
import pandas as pd
import plotly.express as px
from prophet import Prophet

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

# Convert to date for compatibility with st.date_input
min_date = df["Month"].min().date()
max_date = df["Month"].max().date()

start_date, end_date = st.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Convert selected dates to datetime64[ns] for compatibility with the 'Month' column in df
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filtered data
filtered_df = df[(df["Month"] >= start_date) & (df["Month"] <= end_date)]

# Prophet Forecasting Model
forecast_periods = 12  # Number of months to forecast into the future
prophet_df = filtered_df[["Month", "Unique Postings"]].rename(columns={"Month": "ds", "Unique Postings": "y"})

# Initialize and fit the model
model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
model.fit(prophet_df)

# Manually create the future dates
last_date = prophet_df["ds"].max()
future_dates = pd.date_range(start=last_date, periods=forecast_periods + 1, freq='M')[1:]

# Create a new dataframe with the future dates
future_df = pd.DataFrame({'ds': future_dates})

# Forecast the future
forecast = model.predict(future_df)

# Add forecast values to the dataframe
forecasted_df = pd.concat([prophet_df, future_df], ignore_index=True)
forecasted_df["forecast"] = model.predict(forecasted_df)["yhat"]

# Interactive Plotly Time Series Plot with Forecast
st.subheader("Unique Job Postings Over Time with Forecast")
fig = px.line(filtered_df, x="Month", y="Unique Postings", title="Time Series of Unique Job Postings with Forecast", markers=True)

# Plot the forecast only for the forecast period
fig.add_scatter(x=forecasted_df["ds"], y=forecasted_df["forecast"], mode="lines", name="Forecast", line=dict(dash='dot', color='red'))

fig.update_layout(xaxis_title="Month", yaxis_title="Unique Postings", template="plotly_dark")
st.plotly_chart(fig)

# Optional: Posting Intensity table
if st.checkbox("Show Posting Intensity Table"):
    st.dataframe(filtered_df[["Month", "Posting Intensity"]].reset_index(drop=True))

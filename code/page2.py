import streamlit as st
import pandas as pd
import altair as alt
import folium
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster, HeatMap
import os
import time
import streamlit.components.v1 as components  # To render the folium map

# Load the data
file_path = "D:/Project/Data_to_WebApp/data/Job_Postings_by_Location_STEM_Occupations_SOC_2021_in_3194_Counties_8653.xls"
df = pd.read_excel(file_path, sheet_name="Job Postings by Location", engine='xlrd')

# Create the 'State Name' column by extracting state abbreviation
df['State Name'] = df['County Name'].str.split(',').str[-1].str.strip()

# Convert the 'State Name' column to uppercase
df['State Name'] = df['State Name'].str.upper()

# Set up Streamlit app - Make sure this is at the very top of your script
st.set_page_config(layout="wide")
st.title("Job Postings Dashboard (STEM Occupations)")

# Sidebar Filters
states = df['State Name'].unique()

# Ensure unique states are listed only once
states = [state for state in states if pd.notnull(state)]

# Sort and display the states in the sidebar with enhanced visibility
selected_state = st.sidebar.selectbox("Select a State", sorted(states), key="state_select")

# Filter by selected state
filtered_df = df[df['State Name'] == selected_state]

# Display the highest and lowest "Median Annual Advertised Salary"
highest_salary_row = filtered_df.loc[filtered_df['Median Annual Advertised Salary'].idxmax()]
lowest_salary_row = filtered_df.loc[filtered_df['Median Annual Advertised Salary'].idxmin()]

st.metric(
    "Highest Median Annual Advertised Salary",
    f"${highest_salary_row['Median Annual Advertised Salary']:,.0f} in {highest_salary_row['County Name']}"
)

st.metric(
    "Lowest Median Annual Advertised Salary",
    f"${lowest_salary_row['Median Annual Advertised Salary']:,.0f} in {lowest_salary_row['County Name']}"
)

# Geolocator with User-Agent
geolocator = Nominatim(user_agent="my_job_postings_app")

# Function to get latitude and longitude with error handling
def geocode_county(county):
    try:
        location = geolocator.geocode(county)
        if location:
            return location.latitude, location.longitude
        else:
            st.warning(f"Location not found for: {county}")
            return None, None
    except Exception as e:
        st.error(f"Error geocoding {county}: {e}")
        return None, None

# Clean the county names
df['County Name'] = df['County Name'].str.strip()  # Remove any leading/trailing whitespace

# Create a map centered around the US (you can adjust this as per your needs)
map_center = [37.0902, -95.7129]  # Approximate center of the US
map_obj = folium.Map(location=map_center, zoom_start=5)

# Add county markers to the map
marker_cluster = MarkerCluster().add_to(map_obj)

# Prepare data for heatmap
heat_data = []

# Loop through counties and add markers with delay
for index, row in filtered_df.iterrows():
    county_name = row['County Name']
    latitude, longitude = geocode_county(county_name)
    if latitude and longitude:
        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(f"""
                <b>County:</b> {county_name}<br>
                <b>Median Salary:</b> ${row['Median Annual Advertised Salary']}<br>
                <b>Unique Postings:</b> {row['Unique Postings from Jan 2023 - Dec 2023']}<br>
                <b>Median Posting Duration:</b> {row['Median Posting Duration from Jan 2023 - Dec 2023']} days
            """, max_width=300),  # Customizable popup size
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)
        
        # Add coordinates to heatmap data
        heat_data.append([latitude, longitude, row['Median Annual Advertised Salary']])  # Add a weight (median salary)
    time.sleep(1)  # Adding delay of 1 second between requests

# Create HeatMap
HeatMap(heat_data).add_to(map_obj)

# Render the folium map in Streamlit
st.title("Job Postings Location Heatmap")
st.subheader("Heatmap showing counties with job posting information")
st.write("Hover over a marker for more details.")
# Render the folium map using Streamlit components
map_html = map_obj._repr_html_()  # Get the HTML representation of the map
components.html(map_html, height=600)  # Display the map in Streamlit

# Add visual chart for Median Salary, Median Posting Duration, and Unique Postings
# First Plot - Median Salary
chart_1 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Median Annual Advertised Salary:Q', title='Median Annual Advertised Salary'),
        color=alt.value('#4682B4')
    )
    .properties(title='Median Annual Advertised Salary by County (2023)')
    .interactive()
)

# Second Plot - Unique Postings
chart_2 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Unique Postings from Jan 2023 - Dec 2023:Q', title='Unique Job Postings (2023)'),
        color=alt.value('#E97451')
    )
    .properties(title='Unique Job Postings by County (2023)')
    .interactive()
)

# Third Plot - Median Posting Duration
chart_3 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Median Posting Duration from Jan 2023 - Dec 2023:Q', title='Median Posting Duration (2023)'),
        color=alt.value('#2ecc71')
    )
    .properties(title='Median Posting Duration by County (2023)')
    .interactive()
)

# Display charts
st.altair_chart(chart_1, use_container_width=True)
st.altair_chart(chart_2, use_container_width=True)
st.altair_chart(chart_3, use_container_width=True)

# Add some additional customization for clarity
st.markdown(""" 
    <style>
        .st-bd {
            padding: 5%;
        }
        .stSidebar > div {
            width: 350px;  /* Adjust the sidebar width */
        }
    </style>
""", unsafe_allow_html=True)

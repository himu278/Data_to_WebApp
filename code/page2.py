import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from folium.plugins import HeatMap  # Import HeatMap
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

# List to hold the coordinates for HeatMap
heat_data = []

# Loop through counties and get coordinates
for index, row in filtered_df.iterrows():
    county_name = row['County Name']
    latitude, longitude = geocode_county(county_name)
    if latitude and longitude:
        # Use the median salary or other data as a weight for heatmap intensity
        heat_data.append([latitude, longitude, row['Median Annual Advertised Salary']])  # Add a weight (median salary)

# Add HeatMap to the map
HeatMap(heat_data).add_to(map_obj)

# Render the folium map in Streamlit
st.title("Job Postings Location Heatmap")
st.subheader("Heatmap showing counties with job posting information")
st.write("Higher intensity represents areas with higher job posting information.")

# Render the folium map using Streamlit components
map_html = map_obj._repr_html_()  # Get the HTML representation of the map
components.html(map_html, height=600)  # Display the map in Streamlit

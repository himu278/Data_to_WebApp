import streamlit as st
import pandas as pd
import altair as alt
import folium
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster, HeatMap
import os
import time
import streamlit.components.v1 as components  # To render the folium map
from pathlib import Path

# Suppress Streamlit warnings
st.set_option('client.showErrorDetails', False)

# Load the data
file_path = Path("data/Job_Postings_by_Location_STEM_Occupations_SOC_2021_in_3194_Counties_8653.xls")
df = pd.read_excel(file_path, sheet_name="Job Postings by Location", engine='xlrd')

# Create the 'State Name' column by extracting state abbreviation
df['State Name'] = df['County Name'].str.split(',').str[-1].str.strip()

# Convert the 'State Name' column to uppercase
df['State Name'] = df['State Name'].str.upper()

# Clean 'Median Annual Advertised Salary' to numeric
df['Median Annual Advertised Salary'] = pd.to_numeric(df['Median Annual Advertised Salary'], errors='coerce')

# Handle missing values or errors
df = df.dropna(subset=['Median Annual Advertised Salary'])

# Set up Streamlit app - Make sure this is at the very top of your script
st.set_page_config(layout="wide")
###
st.title("Welcome to the **STEM Job Postings dashboard**, a comprehensive platform for exploring job posting data across the United States.")

st.markdown("""
    This tool offers valuable insights into the **demand for STEM occupations** by displaying job postings, salary information, and posting durations across counties and states.

    Whether you're an industry professional, a job seeker, or a researcher, this tool enables you to:
    - Explore job postings by **county** and **state**.
    - Visualize **median salaries**, **posting durations**, and **job posting volumes**.
    - Analyze trends in STEM job markets across different geographic regions.
    
    Use the interactive maps and charts to gain deeper insights into the evolving STEM job landscape. 
    You can select a state to view county-level data, access detailed job posting statistics, and explore the latest trends in job demands and salary offerings.

    **Navigate** using the sidebar to:
    - Select a state for a detailed view.
    - View geographical heatmaps that highlight job posting intensity.
    - Compare salary data across counties.
    - Track the median posting durations and posting volumes for STEM-related jobs.

    Start exploring now and gain valuable insights into the **STEM employment trends** that can guide your next career decision, research, or business strategy.

    If you have any questions or need further assistance, feel free to explore the additional information at the bottom of the page.
""")
###

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
# Track counties that can't be geocoded
missing_locations = []

def geocode_county(county):
    try:
        location = geolocator.geocode(county)
        if location:
            return location.latitude, location.longitude
        else:
            # Track missing counties
            missing_locations.append(county)
            return None, None
    except Exception as e:
        # Track counties that failed
        missing_locations.append(county)
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
st.write("Zoom the map to find the location. Hover over a marker for more details.")
# Render the folium map using Streamlit components
map_html = map_obj._repr_html_()  # Get the HTML representation of the map
components.html(map_html, height=600)  # Display the map in Streamlit

###
# Added map footer with missing locations
if missing_locations:
    # Create a bullet list with line breaks
    locations_html = "<br>".join([f"• {location}" for location in missing_locations])
    
    st.markdown(f"""
        <footer>
            <p style="font-size:14px; color:gray;">
                Some locations cannot be located by this service.<br>
                {locations_html}
            </p>
        </footer>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <footer>
            <p style="font-size:14px; color:gray;">
                Some locations cannot be located by this service.
            </p>
        </footer>
    """, unsafe_allow_html=True)


###


###
# Create a selectbox for counties in the selected state
counties_in_state = filtered_df['County Name'].unique()
selected_county = st.selectbox('Select a County to view details:', counties_in_state)

# Filter by selected county
county_data = filtered_df[filtered_df['County Name'] == selected_county]

# Display the selected county details
st.subheader(f"Details for {selected_county}")
st.metric("Median Salary", f"${county_data['Median Annual Advertised Salary'].values[0]:,.0f}")
st.metric("Unique Postings", f"{county_data['Unique Postings from Jan 2023 - Dec 2023'].values[0]:,}")
st.metric("Posting Duration", f"{county_data['Median Posting Duration from Jan 2023 - Dec 2023'].values[0]} days")

###
# Add a clear separation between the map and the chart sections
st.markdown("---")  # This adds a horizontal line divider

# Add a section header indicating the completion of the map section
st.markdown("""
    ## Job Posting Statistics
    Now, let's dive into the job posting statistics for the selected state. 
    Below you will find visualizations that provide insights into the **median annual advertised salaries**, **unique job postings**, and **posting durations** across counties.
    Explore the charts to analyze trends and make data-driven decisions for your next career or business strategy.
""")
###

###
# Add visual chart for Median Salary, Median Posting Duration, and Unique Postings
# Add description before the first chart - Median Salary
st.markdown("""
    ### Median Annual Advertised Salary by County (2023)
    This chart displays the **Median Annual Advertised Salary** for STEM-related job postings across different counties in the selected state. 
    The height of each bar represents the median salary for job postings in each county, helping you to identify the regions with the highest and lowest salaries for STEM occupations.
    Use this chart to compare salary offerings across counties and find areas with the best-paying job opportunities in the STEM field.
""")

# First Plot - Median Salary
chart_1 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name', axis=alt.Axis(labelAngle=45)),  # Rotate labels
        y=alt.Y('Median Annual Advertised Salary:Q', title='Median Annual Advertised Salary'),
        color=alt.value('#4682B4')
    )
    .properties(
        title='Median Annual Advertised Salary by County (2023)',
        width=800,  # Increase chart width
        height=400  # Increase chart height for better spacing
    )
    .configure_axis(
        labelFontSize=10,  # Reduce label font size for readability
        titleFontSize=12
    )
    .configure_title(
        fontSize=14,  # Set title font size
        anchor='middle',  # Center the title
        font='Helvetica'
    )
    .interactive()
)
# Display the first chart
st.altair_chart(chart_1, use_container_width=True)

# Add description before the second chart - Unique Postings
st.markdown("""
    ### Unique Job Postings by County (2023)
    This chart visualizes the **Unique Job Postings** for STEM occupations in each county. It shows the number of unique job postings from January to December 2023. 
    This data can help identify areas with a high volume of job opportunities, providing insights into the demand for STEM professionals in different regions.
    Use this chart to determine which counties have the greatest number of unique job postings in STEM fields.
""")

# Second Plot - Unique Postings
chart_2 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name', axis=alt.Axis(labelAngle=45)),  # Rotate labels
        y=alt.Y('Unique Postings from Jan 2023 - Dec 2023:Q', title='Unique Job Postings (2023)'),
        color=alt.value('#E97451')
    )
    .properties(
        title='Unique Job Postings by County (2023)',
        width=800,
        height=400
    )
    .configure_axis(
        labelFontSize=10,  # Reduce label font size for readability
        titleFontSize=12
    )
    .configure_title(
        fontSize=14,
        anchor='middle',
        font='Helvetica'
    )
    .interactive()
)

# Display the second chart
st.altair_chart(chart_2, use_container_width=True)

# Add description before the third chart - Median Posting Duration
st.markdown("""
    ### Median Posting Duration by County (2023)
    This chart shows the **Median Posting Duration** for STEM-related job postings in each county from January to December 2023. The median posting duration indicates how long a job posting stays open before being filled. 
    A shorter duration suggests higher demand or faster hiring cycles, while a longer duration may indicate lower demand or a more selective hiring process. 
    Use this chart to identify which counties have the fastest job posting turnovers and to understand the hiring dynamics in STEM occupations.
""")

# Third Plot - Median Posting Duration
chart_3 = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('County Name:N', sort='-y', title='County Name', axis=alt.Axis(labelAngle=45)),  # Rotate labels
        y=alt.Y('Median Posting Duration from Jan 2023 - Dec 2023:Q', title='Median Posting Duration (2023)'),
        color=alt.value('#2ecc71')
    )
    .properties(
        title='Median Posting Duration by County (2023)',
        width=800,
        height=400
    )
    .configure_axis(
        labelFontSize=10,  # Reduce label font size for readability
        titleFontSize=12
    )
    .configure_title(
        fontSize=14,
        anchor='middle',
        font='Helvetica'
    )
    .interactive()
)

# Display the third chart
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


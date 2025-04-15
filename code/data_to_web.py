# Import necessary libraries
import streamlit as st
import pandas as pd
import altair as alt
import folium
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster, HeatMap
import os
import time
import streamlit.components.v1 as components  # To render the folium map
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pathlib import Path

# Set up Streamlit app - Make sure this is at the very top of your script
st.set_page_config(layout="wide")


# --- Page Navigation in the Upper Bar ---
# Add a "Choose a page" dropdown at the top
page = st.selectbox("Choose a Page", ["Job Postings Top Companies", "Job Postings by Location", "Job Postings Timeseries"]) # Make page names as you like, ex page 1...
                    # I put here the excel Sheet name for each page.
                    # Job Postings Top Companies
                    # Job Postings by Location
                    # Job Postings Timeseries
                    
########################################################################
# --- Job Postings Top Companies ---
if page == "Job Postings Top Companies":

    # Load Excel data
    file_path = Path("data/Program_Overview_6046.xls")
    company_df = pd.read_excel(file_path, sheet_name="Job Postings Top Companies", skiprows=2, engine='xlrd')

    # Clean 'Median Posting Duration'
    company_df['Median Posting Duration'] = company_df['Median Posting Duration'].str.extract(r'(\d+)').astype(int)

    # General description
    st.title("Job Postings Dashboard for Top Companies in 2023")
    st.write("""
    This dashboard displays job posting data from the top companies for the year 2023. 
    It highlights the total number of job postings and the number of unique job postings for each company.
    The data can help you understand the job posting trends across various companies and the job market in general.
    """)

    # Selection for posting type
    posting_type = st.radio(
        "Select posting data to display",
        options=["Total Postings", "Unique Postings", "Both"],
        index=2,
        horizontal=True
    )

    # Determine sorting column based on selection
    if posting_type == "Total Postings":
        sort_col = 'Total Postings (Jan 2023 - Dec 2023)'
    elif posting_type == "Unique Postings":
        sort_col = 'Unique Postings (Jan 2023 - Dec 2023)'
    else:
        sort_col = 'Total Postings (Jan 2023 - Dec 2023)'

    # Slicer: Select Top N Companies
    max_companies = len(company_df)
    top_n = st.slider("Select number of top companies to display", min_value=1, max_value=max_companies, value=5)

    # Filter and sort top companies
    top_companies_df = company_df.sort_values(by=sort_col, ascending=False).head(top_n)

    # Melt and prepare chart data
    if posting_type == "Both":
        melted_df = top_companies_df.melt(
            id_vars=['Company', 'Median Posting Duration'],
            value_vars=[
                'Total Postings (Jan 2023 - Dec 2023)', 
                'Unique Postings (Jan 2023 - Dec 2023)'
            ],
            var_name='Posting Type',
            value_name='Postings'
        )
        melted_df['Posting Type'] = melted_df['Posting Type'].replace({
            'Total Postings (Jan 2023 - Dec 2023)': 'Total Postings',
            'Unique Postings (Jan 2023 - Dec 2023)': 'Unique Postings'
        })
        
        # Create pivot to calculate ratio
        pivot_df = melted_df.pivot(index='Company', columns='Posting Type', values='Postings').reset_index()
        pivot_df['Ratio'] = (pivot_df['Total Postings'] / pivot_df['Unique Postings']).apply(
            lambda x: f"{int(x)}:1"
        )

        
        # Merge ratio back to melted_df
        melted_df = melted_df.merge(pivot_df[['Company', 'Ratio']], on='Company', how='left')
        chart_df = melted_df
    else:
        chart_df = top_companies_df[['Company', 'Median Posting Duration', sort_col]].copy()
        chart_df = chart_df.rename(columns={sort_col: 'Postings'})
        chart_df['Posting Type'] = posting_type

    # Subheader
    st.subheader(f"{posting_type} for Top {top_n} Companies in 2023" if posting_type != "Both" 
                else f"Total vs Unique Job Postings for Top {top_n} Companies in 2023")

    # Explanation of Postings
    st.write("""
    **Total Postings**: This refers to the total number of job postings published by a company during 2023.
    **Unique Postings**: This refers to the distinct job positions posted by the company, excluding any duplicate listings for the same role.
    """)

    # Company order
    company_order = chart_df.groupby('Company')['Postings'].sum().sort_values(ascending=False).index.tolist()

    # Base bar chart
    bar = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('Company:N',
                sort=company_order,
                title='Company',
                axis=alt.Axis(labelAngle=270, labelLimit=300)),
        y=alt.Y('Postings:Q', title='Number of Postings'),
        color=alt.Color('Posting Type:N',
            scale=alt.Scale(domain=['Total Postings', 'Unique Postings'], range=['#4682B4', '#E97451'])),
        tooltip=[
            alt.Tooltip('Company:N'),
            alt.Tooltip('Postings:Q'),
            alt.Tooltip('Median Posting Duration:Q')
        ]
    )

    # Label data
    if posting_type == "Both":
        label_data = chart_df.groupby('Company').apply(
            lambda x: x.loc[x['Postings'].idxmax()]).reset_index(drop=True)
        label_data = label_data[['Company', 'Postings', 'Ratio']]
    else:
        label_data = chart_df.copy()
        label_data['Ratio'] = label_data['Median Posting Duration'].astype(str)

    # Label background box
    label_bg = alt.Chart(label_data).mark_rect(
        angle=270,
        cornerRadius=6,
        width=20,
        height=15,
        fill='lightgray',
        opacity=0.75
    ).encode(
        x=alt.X('Company:N', sort=company_order),
        y=alt.Y('Postings:Q', stack=None)
    )

    # Label text with 270-degree rotation
    label_text = alt.Chart(label_data).mark_text(
        angle=270,
        align='left',
        baseline='middle',
        fontSize=11,
        fontWeight='bold',
        color='#1f2937'
    ).encode(
        x=alt.X('Company:N', sort=company_order),
        y=alt.Y('Postings:Q', stack=None),
        text=alt.Text('Ratio:N')
    )

    # Combine chart
    final_chart = (bar + label_text).properties(
        width=700,
        height=600
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )

    # Show chart
    st.altair_chart(final_chart, use_container_width=True)

    # Caption
    if posting_type == "Both":
        st.caption("The value shown on each bar is the ratio of Total to Unique Postings.")
    else:
        st.caption("The value shown on each bar is the Median Posting Duration (in days).")

########################################################################
# --- Job Postings by Location ---
elif page == "Job Postings by Location":
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
    #st.set_page_config(layout="wide")
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
    st.sidebar.markdown("### State Selection")
    st.sidebar.markdown("Select a state to explore job data across its counties.")

    selected_state = st.sidebar.selectbox(
        "Select a State",
        sorted(states),
        key="state_select",
        help="Choose a U.S. state to view county-level STEM job posting data."
    )
        

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
    # st.markdown("""
    #     ## Job Posting Statistics""")

    st.markdown(f"<h1 style='text-align: center;'>Job Posting Statistics for <strong>{selected_state}</strong> State</h1>", unsafe_allow_html=True)


    st.markdown("""
        Now, let's dive into the job posting statistics for this state. 
        Below you will find visualizations that provide insights into the **median annual advertised salaries**, **unique job postings**, and **posting durations** across counties.
        Explore the charts to analyze trends and make data-driven decisions for your next career or business strategy.
                
    """)
    ###

    ###
    # Add visual chart for Median Salary, Median Posting Duration, and Unique Postings
    # Add description before the first chart - Median Salary
    st.markdown("""
        ### Median Annual Advertised Salary (2023)
        This chart displays the **Median Annual Advertised Salary** for STEM-related job postings across different counties in this state. 
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
            title='Median Annual Advertised Salary (2023)',
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
        ### Unique Job Postings (2023)
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
            title='Unique Job Postings (2023)',
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
        ### Median Posting Duration (2023)
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
            title='Median Posting Duration (2023)',
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


########################################################################
# --- Job Postings Timeseries ---
elif page == "Job Postings Timeseries":

        
    # Load the data
    @st.cache_data
    def load_data():
        file_path = Path("data/Job_Posting_Analytics_8_Occupations_in_3194_Counties_5318.xls")
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
                                                trend='ME',
                                                maxiter=1000,  # Increase maximum iterations    
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
    forecast_index = pd.date_range(start=filtered_df_jpt['Month'].iloc[-1], periods=forecast_steps+1, freq='ME')[1:]

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


###
# Run this lines in the Terminal
# cd code  # Navigate into the 'code' folder
# streamlit run data_to_web.py  # Run the Streamlit app

import streamlit as st
import pandas as pd
import altair as alt
import os

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


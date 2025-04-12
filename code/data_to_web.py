import streamlit as st
import pandas as pd
import os

# Load the data
#file_path = os.path.expanduser("~/Desktop/h/Job_Postings_by_Location_STEM_Occupations_SOC_2021_in_3194_Counties_8653.xls")
file_path = "D:/Project/Data_to_WebApp/data/Job_Postings_by_Location_STEM_Occupations_SOC_2021_in_3194_Counties_8653.xls"
df = pd.read_excel(file_path, sheet_name="Job Postings by Location", engine='xlrd')

st.set_page_config(layout="wide")
st.title("Job Postings Dashboard (STEM Occupations)")

# Sidebar Filters
counties = df['County Name'].unique()
selected_county = st.sidebar.selectbox("Select a County", sorted(counties))

filtered_df = df[df['County Name'] == selected_county]

# Display metrics
st.subheader(f"Key Metrics for {selected_county}")
st.metric("Median Salary", f"${filtered_df['Median Annual Advertised Salary'].values[0]:,.0f}")
st.metric("Unique Postings", f"{filtered_df['Unique Postings from Jan 2023 - Dec 2023'].values[0]:,}")
st.metric("Posting Duration", f"{filtered_df['Median Posting Duration from Jan 2023 - Dec 2023'].values[0]} days")


import altair as alt

# Filter top 5 counties with the highest number of unique job postings (Jan–Dec 2023)
# #top5_df = filtered_df.nlargest(5,'Unique Postings from Jan 2023 - Dec 2023')

#  Create an interactive bar chart using Altair
chart = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X(
            'County Name:N',
            sort='-y',
            title='County Name'
        ),
        y=alt.Y(
            'Unique Postings from Jan 2023 - Dec 2023:Q',
            title='Unique Job Postings (2023)'
        ),
        color=alt.value('darkgreen')  # Solid dark green color for all bars
    )
    .properties(
        title='County by Unique Job Postings (Jan–Dec 2023)'
    )
    .interactive()
)

#  Step 3: Display the chart in your Streamlit app
st.altair_chart(chart, use_container_width=True)


###
# Run this lines in the Terminal
# cd code  # Navigate into the 'code' folder
# streamlit run data_to_web.py  # Run the Streamlit app


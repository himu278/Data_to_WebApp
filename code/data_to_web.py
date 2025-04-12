import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Load Data ---
file_path = "D:/Project/Data_to_WebApp/data/Job_Postings_by_Location_STEM_Occupations_SOC_2021_in_3194_Counties_8653.xls"
df = pd.read_excel(file_path, sheet_name="Job Postings by Location", engine='xlrd')

# Clean 'State Name' column by extracting the state abbreviation
df['State Name'] = df['County Name'].str.split(',').str[-1].str.strip()
df['State Name'] = df['State Name'].str.upper()

# --- Page Navigation in the Upper Bar ---
# Add a "Choose a page" dropdown at the top
page = st.selectbox("Choose a Page", ["Top Companies Job Postings", "Job Postings Dashboard"])

# --- Job Postings Dashboard (State and County Filters) ---
if page == "Job Postings Dashboard":
    st.title("Job Postings Dashboard (STEM Occupations)")
    
    # Sidebar filter by State
    states = df['State Name'].unique()
    selected_state = st.sidebar.selectbox("Select a State", sorted(states))

    # Filter data by selected state
    filtered_df = df[df['State Name'] == selected_state]

    # Display metrics for selected state
    st.subheader(f"Key Metrics for {selected_state}")
    st.metric("Median Salary", f"${filtered_df['Median Annual Advertised Salary'].values[0]:,.0f}")
    st.metric("Unique Postings", f"{filtered_df['Unique Postings from Jan 2023 - Dec 2023'].values[0]:,}")
    st.metric("Posting Duration", f"{filtered_df['Median Posting Duration from Jan 2023 - Dec 2023'].values[0]} days")

    # Plot 1: Median Annual Advertised Salary (Y-axis updated)
    chart1 = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Median Annual Advertised Salary:Q', title='Median Annual Advertised Salary'),
        color=alt.value('darkblue')
    ).properties(title='County by Median Annual Advertised Salary').interactive()

    st.altair_chart(chart1, use_container_width=True)

    # Plot 2: Unique Job Postings (Unchanged)
    chart2 = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Unique Postings from Jan 2023 - Dec 2023:Q', title='Unique Job Postings (2023)'),
        color=alt.value('darkgreen')
    ).properties().interactive()
    #).properties(title='County by Unique Job Postings (Jan–Dec 2023)').interactive()

    st.altair_chart(chart2, use_container_width=True)

    # Plot 3: Median Posting Duration (Y-axis updated)
    chart3 = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X('County Name:N', sort='-y', title='County Name'),
        y=alt.Y('Median Posting Duration from Jan 2023 - Dec 2023:Q', title='Median Posting Duration (days)'),
        color=alt.value('darkred')
    ).properties(title='County by Median Posting Duration').interactive()

    st.altair_chart(chart3, use_container_width=True)

# --- Top Companies Job Postings ---
elif page == "Top Companies Job Postings":
    st.title("Top Companies Job Postings (STEM Occupations)")

    # Load Top Companies Data
    company_file_path = "D:/Project/Data_to_WebApp/data/Program_Overview_6046.xls"
    company_df = pd.read_excel(company_file_path, sheet_name="Job Postings Top Companies", skiprows=2, engine='xlrd')

    # Clean 'Median Posting Duration'
    company_df['Median Posting Duration'] = company_df['Median Posting Duration'].str.extract(r'(\d+)').astype(int)

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

    # Slicer for selecting Top N Companies
    max_companies = len(company_df)
    top_n = st.slider("Select number of top companies to display", min_value=1, max_value=max_companies, value=5)

    # Filter and sort top companies
    top_companies_df = company_df.sort_values(by=sort_col, ascending=False).head(top_n)

    # Prepare chart data
    if posting_type == "Both":
        melted_df = top_companies_df.melt(
            id_vars=['Company', 'Median Posting Duration'],
            value_vars=['Total Postings (Jan 2023 - Dec 2023)', 'Unique Postings (Jan 2023 - Dec 2023)'],
            var_name='Posting Type',
            value_name='Postings'
        )
        melted_df['Posting Type'] = melted_df['Posting Type'].replace({
            'Total Postings (Jan 2023 - Dec 2023)': 'Total Postings',
            'Unique Postings (Jan 2023 - Dec 2023)': 'Unique Postings'
        })
        pivot_df = melted_df.pivot(index='Company', columns='Posting Type', values='Postings').reset_index()
        pivot_df['Ratio'] = (pivot_df['Total Postings'] / pivot_df['Unique Postings']).apply(lambda x: f"{int(x)}:1")
        melted_df = melted_df.merge(pivot_df[['Company', 'Ratio']], on='Company', how='left')
        chart_df = melted_df
    else:
        chart_df = top_companies_df[['Company', 'Median Posting Duration', sort_col]].copy()
        chart_df = chart_df.rename(columns={sort_col: 'Postings'})
        chart_df['Posting Type'] = posting_type

    # Subheader for Company Job Postings Visualization
    st.subheader(f"{posting_type} for Top {top_n} Companies in 2023" if posting_type != "Both"
                 else f"Total vs Unique Job Postings for Top {top_n} Companies in 2023")

    # Company order for the bar chart
    company_order = chart_df.groupby('Company')['Postings'].sum().sort_values(ascending=False).index.tolist()

    # Base bar chart for company data
    bar = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('Company:N', sort=company_order, title='Company', axis=alt.Axis(labelAngle=270, labelLimit=300)),
        y=alt.Y('Postings:Q', title='Number of Postings'),
        color=alt.Color('Posting Type:N', scale=alt.Scale(domain=['Total Postings', 'Unique Postings'], range=['#4682B4', '#E97451']),
                       legend=alt.Legend(title="Posting Type")) if posting_type == "Both" else alt.ColorValue('#4682B4'),
        tooltip=[alt.Tooltip('Company:N'), alt.Tooltip('Postings:Q'), alt.Tooltip('Median Posting Duration:Q')]
    )

    # Labeling chart
    if posting_type == "Both":
        label_data = chart_df.groupby('Company').apply(lambda x: x.loc[x['Postings'].idxmax()]).reset_index(drop=True)
        label_data = label_data[['Company', 'Postings', 'Ratio']]
    else:
        label_data = chart_df.copy()
        label_data['Ratio'] = label_data['Median Posting Duration'].astype(str)

    # Combine chart
    final_chart = (bar).properties(width=700, height=600).configure_axis(grid=False).configure_view(strokeWidth=0)

    # Display the chart
    st.altair_chart(final_chart, use_container_width=True)

    # Caption
    if posting_type == "Both":
        st.caption("The value shown on each bar is the ratio of Total to Unique Postings.")
    else:
        st.caption("The value shown on each bar is the Median Posting Duration (in days).")

###
# Run this lines in the Terminal
# cd code  # Navigate into the 'code' folder
# streamlit run data_to_web.py  # Run the Streamlit app
# streamlit run test.py  # Run the Streamlit app

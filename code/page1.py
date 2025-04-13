import streamlit as st
import pandas as pd
import altair as alt
import os

# Load Excel data
#file_path = os.path.expanduser("~/Desktop/himu/Program_Overview_6046.xls")
file_path = "D:/Project/Data_to_WebApp/data/Program_Overview_6046.xls"
company_df = pd.read_excel(file_path, sheet_name="Job Postings Top Companies", skiprows=2, engine='xlrd')

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
        scale=alt.Scale(domain=['Total Postings', 'Unique Postings'], range=['#4682B4', '#E97451']),
        legend=alt.Legend(title="Posting Type")
    ) if posting_type == "Both" else alt.ColorValue('#4682B4'),
    tooltip=[
        alt.Tooltip('Company:N'),
        alt.Tooltip('Postings:Q'),
        alt.Tooltip('Median Posting Duration:Q')
    ]
)

# Label data
if posting_type == "Both":
    label_data = chart_df.groupby('Company').apply(
        lambda x: x.loc[x['Postings'].idxmax()]
    ).reset_index(drop=True)
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
    st.caption(" The value shown on each bar is the ratio of Total to Unique Postings.")
else:
    st.caption(" The value shown on each bar is the Median Posting Duration (in days).")
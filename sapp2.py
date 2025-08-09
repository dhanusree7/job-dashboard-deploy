import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np

# Inject CSS to remove max-width and make dark mode cover full page
st.markdown("""
    <style>
        /* Make the main container use full width */
        .block-container {
            max-width: 100% !important;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        /* Dark mode full background */
        body {
            background-color: black !important;
        }

        /* Make Plotly charts fit full width */
        .stPlotlyChart {
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    return pd.read_csv('cleaned_jobposts.csv', encoding='utf-8')

df = load_data()

def clean_salary(val):
    if pd.isnull(val):
        return np.nan
    val = str(val)

    # Extract all numbers (handle ranges like "50,000 - 70,000")
    numbers = re.findall(r'[\d,]+', val)
    if not numbers:
        return np.nan

    try:
        # Convert all to float after removing commas
        numbers = [float(num.replace(',', '')) for num in numbers]
        if len(numbers) == 1:
            return numbers[0]
        else:
            return sum(numbers) / len(numbers)  # take average of range
    except:
        return np.nan

df['Salary_Cleaned'] = df['Salary'].apply(clean_salary)
average_salary = round(df['Salary_Cleaned'].dropna().mean(), 2)

# Dark mode toggle
dark_mode = st.checkbox("Dark Mode")

# Apply styles based on theme
if dark_mode:
    st.markdown("""
    <style>
    html, body, .main { background-color: #121212 !important; color: #f0f0f0 !important; }
    .block-container { background-color: #121212 !important; }
    h1, h2, h3, .stMetricValue, .stMetricLabel, label, p { color: #f0f0f0 !important; }
    .stCheckbox > label { color: white !important; font-weight: 600; font-size: 16px; }
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
    }
    .stMetricValue, .stMetricLabel {
        color: #f0f0f0 !important;
        font-weight: 600;
    }
    .stCheckbox > label {
        color: white !important;
        font-weight: 600;
        font-size: 16px;
    }
    div[data-testid="stMetricValue"] {
        color: white !important;
        font-weight: 700;
        font-size: 22px;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    html, body, .main { background-color: white !important; color: black !important; }
    .block-container { background-color: white !important; }
    h1, h2, h3, .stMetricValue, .stMetricLabel, label, p { color: black !important; }
    .stCheckbox > label { color: black !important; font-weight: 600; font-size: 16px; }
    .stMetric {
    background-color: #f2f2f2; /* Light gray card background */
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    }
    .stMetricValue, .stMetricLabel {
    color: black !important;
    font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
    color: black !important;
    font-weight: 700;
    font-size: 22px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ROW 1: Title and KPIs ---
# --- ROW 1: Title and KPIs ---
st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center;">
    <h1>Job Posts Dashboard</h1>
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 30px; margin-top: 10px;">
""", unsafe_allow_html=True)

# Compute KPIs
total_posts = len(df)
unique_titles = df['Title'].nunique()
unique_companies = df['Company'].nunique()
top_skill = df['Skill_Cleaned'].explode().value_counts().idxmax() if 'Skill_Cleaned' in df.columns else "N/A"
top_category = df['Category'].value_counts().idxmax() if 'Category' in df.columns else "N/A"

# KPI display
c1, c2 = st.columns(2)
with c1:
    st.metric("Total Job Posts", total_posts)
    st.metric("Unique Companies", unique_companies)

with c2:
    st.metric("Unique Job Titles", unique_titles)
    st.metric("Average Salary", f"${average_salary:,.2f}")


st.markdown("</div></div>", unsafe_allow_html=True)

# --- ROW 2: Charts in 2 columns ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 5 Job Terms")
    job_terms = df['Term_Clean_Final'].value_counts().head(5).reset_index()
    job_terms.columns = ['Term', 'Count']
    fig1 = px.bar(job_terms, x='Term', y='Count', title='Top 5 Job Terms')
    fig1.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.subheader("Top 5 Locations")
    locations = df['Location'].value_counts().head(5).reset_index()
    locations.columns = ['Location', 'Count']
    fig2 = px.bar(locations, x='Location', y='Count', title='Top 5 Locations')
    fig2.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ==== ROW 3 ====
col1, col2 = st.columns(2)

# --- Chart 3: Category Distribution (Treemap) ---
with col1:
    st.subheader("📂 Category Distribution")
    if 'Term_Clean_Final' in df.columns:
        
        # Remove unwanted categories
        unwanted_categories = ["Others", "Unspecified", "Other/Unspecified", "", None]
        filtered_df = df[~df['Term_Clean_Final'].isin(unwanted_categories)]

        if not filtered_df.empty:
            all_categories = sorted(filtered_df['Term_Clean_Final'].unique())

            # Start with 'All Categories' as default
            selected = st.multiselect(
                "Select Job Categories",
                options=["All Categories"] + all_categories,
                default=["All Categories"]
            )

            # If 'All Categories' is selected, ignore other selections
            if "All Categories" in selected:
                chart_df = filtered_df
            else:
                chart_df = filtered_df[filtered_df['Term_Clean_Final'].isin(selected)]

            if not chart_df.empty:
                category_counts = chart_df['Term_Clean_Final'].value_counts().reset_index()
                category_counts.columns = ['Category', 'Count']

                fig_treemap = px.treemap(
                    category_counts,
                    path=['Category'],
                    values='Count',
                    title="Job Category Distribution",
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                fig_treemap.update_layout(
                    template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
                )
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.warning("No data available for the selected category.")
        else:
            st.warning("No valid categories found after filtering.")
    else:
        st.warning("`Term_Clean_Final` column not found in dataset.")


# --- Chart 4: Hiring Pattern (Heatmap) ---
with col2:
    st.subheader("📅 Hiring Pattern")

    possible_date_cols = [col for col in df.columns if 'date' in col.lower()]

    if possible_date_cols:
        date_col = possible_date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        # Extract month & day
        df['Month'] = df[date_col].dt.month_name()
        df['DayOfWeek'] = df[date_col].dt.day_name()

        # Define quarters mapping
        quarter_map = {
            "Q1 (Jan-Mar)": ["January", "February", "March"],
            "Q2 (Apr-Jun)": ["April", "May", "June"],
            "Q3 (Jul-Sep)": ["July", "August", "September"],
            "Q4 (Oct-Dec)": ["October", "November", "December"],
            "All": ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
        }

        # Two dropdowns in same row
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_quarter = st.selectbox("Select Quarter", list(quarter_map.keys()), index=len(quarter_map)-1)
        with filter_col2:
            selected_day = st.selectbox(
                "Select Day",
                ["All", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )

        # Apply filters
        filtered_df = df[df['Month'].isin(quarter_map[selected_quarter])]
        if selected_day != "All":
            filtered_df = filtered_df[filtered_df['DayOfWeek'] == selected_day]

        # Group for heatmap
        heatmap_data = filtered_df.groupby(['DayOfWeek', 'Month']).size().reset_index(name='Job_Count')

        # Order months & days
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months_order = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"]

        heatmap_data['DayOfWeek'] = pd.Categorical(heatmap_data['DayOfWeek'], categories=days_order, ordered=True)
        heatmap_data['Month'] = pd.Categorical(heatmap_data['Month'], categories=months_order, ordered=True)

        # Plot
        fig_heatmap = px.density_heatmap(
            heatmap_data,
            x='Month',
            y='DayOfWeek',
            z='Job_Count',
            color_continuous_scale='Viridis',
            title=f"Hiring Pattern ({selected_quarter} - {selected_day})"
        )
        fig_heatmap.update_layout(
            template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.warning("No date column found in dataset.")
col_left, col_right = st.columns(2)

# Left Column - Job Postings Over Time
with col_left:
    st.subheader("📈 Job Postings Over Time")

    possible_date_cols = [col for col in df.columns if 'date' in col.lower()]

    if possible_date_cols:
        date_col = possible_date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])

        # Month-Year column
        df['Month_Year'] = df[date_col].dt.to_period('M').astype(str)

        # Group and sort
        job_trend = df.groupby('Month_Year').size().reset_index(name='Job_Count')
        job_trend['Month_Year'] = pd.to_datetime(job_trend['Month_Year'])
        job_trend = job_trend.sort_values('Month_Year')

        # Plot
        fig_line = px.line(
            job_trend,
            x='Month_Year',
            y='Job_Count',
            title="Job Postings Trend",
            markers=True
        )
        fig_line.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Month-Year",
            yaxis_title="Number of Job Postings",
            template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
        )

        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No date column found in dataset.")

# Right Column - Placeholder for Salary Distribution or another chart
with col_right:
    st.subheader("💰 Salary Distribution")

    possible_salary_cols = [col for col in df.columns if 'salary' in col.lower()]
    
    if possible_salary_cols:
        salary_col = possible_salary_cols[0]

        # Clean salary values
        df[salary_col] = (
            df[salary_col]
            .astype(str)
            .str.replace(r'[^0-9\.]', '', regex=True)
        )
        df[salary_col] = pd.to_numeric(df[salary_col], errors='coerce')

        # Filter unrealistic salaries
        df_salary = df[(df[salary_col] >= 100) & (df[salary_col] <= 1_000_000)]

        if not df_salary.empty:
            # Convert to thousands
            df_salary[salary_col] = df_salary[salary_col] / 1000

            # Histogram
            fig_hist = px.histogram(
                df_salary,
                x=salary_col,
                nbins=30,
                title="Salary Distribution (Histogram, in Thousands)"
            )
            fig_hist.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Salary (in thousands)",
                yaxis_title="Count",
                template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            

        else:
            st.warning("No valid salary data available after filtering.")
    else:
        st.warning("No salary column found in dataset.")
col_left, col_right = st.columns(2)

# Box Plot in left column
with col_left:
    st.subheader("💰 Salary Distribution (Box Plot, in Thousands)")

    possible_salary_cols = [col for col in df.columns if 'salary' in col.lower()]
    
    if possible_salary_cols:
        salary_col = possible_salary_cols[0]

        # Clean salary values
        df[salary_col] = (
            df[salary_col]
            .astype(str)
            .str.replace(r'[^0-9\.]', '', regex=True)
        )
        df[salary_col] = pd.to_numeric(df[salary_col], errors='coerce')

        # Filter unrealistic salaries
        df_salary = df[(df[salary_col] >= 100) & (df[salary_col] <= 1_000_000)]

        if not df_salary.empty:
            # Convert to thousands
            df_salary[salary_col] = df_salary[salary_col] / 1000

       # Box Plot
            fig_box = px.box(
                df_salary,
                y=salary_col,
                title="Salary Distribution (Box Plot, in Thousands)"
            )
            fig_box.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="Salary (in thousands)",
                template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
            )
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.warning("No salary column found in dataset.")

# Skill Demand Bar Chart in right column
with col_right:
    st.subheader("📊 Top Skills in Demand")

    # Merge all relevant text columns into one
    text_cols = ["JobDescription", "JobRequirment", "RequiredQual"]
    for col in text_cols:
        df[col] = df[col].astype(str)  # Ensure text type
    df["all_skills_text"] = df[text_cols].agg(" ".join, axis=1)

    # Define skill keywords to search for
    skill_keywords = [
        "Python", "Excel", "SQL", "Java", "JavaScript", "C++", "C#", "AWS", "Azure", 
        "HTML", "CSS", "R", "Tableau", "Power BI", "Machine Learning", "Data Analysis", 
        "Communication", "Leadership", "Project Management", "Git", "Django", "Flask"
    ]

    # Count occurrences
    skill_counts = {}
    for skill in skill_keywords:
        count = df["all_skills_text"].str.contains(rf"\b{re.escape(skill)}\b", case=False, na=False).sum()
        skill_counts[skill] = count

    # Create DataFrame and get Top N
    skill_df = pd.DataFrame(list(skill_counts.items()), columns=["Skill", "Count"])
    skill_df = skill_df.sort_values(by="Count", ascending=False).head(10)

    # Plot Bar Chart
    fig = px.bar(
        skill_df,
        x="Skill",
        y="Count",
        title="Top 10 Skills in Job Postings",
        text="Count"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="Skill",
        yaxis_title="Frequency",
        template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white"
    )

    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    # IT vs Non-IT
    st.subheader("💼 IT vs Non-IT Job Distribution")

    if 'IT' in df.columns:
        it_map = df['IT'].fillna(False).apply(
            lambda x: 'IT' if str(x).strip().lower() in ['true', '1', 'yes'] else 'Non-IT'
        )
        it_counts = it_map.value_counts().reset_index()
        it_counts.columns = ['Category', 'Count']

        fig = px.pie(
            it_counts, 
            names='Category', 
            values='Count', 
            title='IT vs Non-IT Jobs',
            hole=0.35
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0), 
            template="plotly_white"  # or "plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Column 'IT' not found in dataset.")

with col_right:
    st.subheader("📈 Salary Trends Bubble Chart")

    # Drop missing salary values
    df_bubble = df.dropna(subset=['Year', 'Salary_clean', 'Term_Clean_Final'])

    # Aggregate job counts
    agg_df = df_bubble.groupby(['Year', 'Term_Clean_Final']).agg(
        avg_salary=('Salary_clean', 'mean'),
        job_count=('jobpost', 'count')
    ).reset_index()

    fig_bubble = px.scatter(
        agg_df,
        x="Year",
        y="avg_salary",
        size="job_count",
        color="Term_Clean_Final",
        hover_name="Term_Clean_Final",
        size_max=50,
        title="Salary Trends by Job Term",
    )

    fig_bubble.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="Year",
        yaxis_title="Average Salary",
        template="plotly_white"
    )

    st.plotly_chart(fig_bubble, use_container_width=True)

import plotly.express as px

st.subheader("🌍 Location Insights")

if 'Location' in df.columns:
    # Count jobs per location
    location_counts = df['Location'].value_counts().reset_index()
    location_counts.columns = ['Location', 'Count']

    # Choropleth Map with bright Turbo color scale
    fig = px.choropleth(
        location_counts,
        locations="Location",
        locationmode="country names",  # Works with country names directly
        color="Count",
        hover_name="Location",
        color_continuous_scale="Turbo",  # Bright, high-contrast color scale
        title="Job Postings by Location"
    )

    # Layout settings for responsiveness
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_white",
        coloraxis_colorbar=dict(title="Job Count")
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Column 'Location' not found in dataset.")

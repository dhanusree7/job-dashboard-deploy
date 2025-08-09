import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# -------------------------
# Load Data
# -------------------------
df = pd.read_csv('data job posts.csv', encoding='utf-8')

print("Initial data shape:", df.shape)
print("Columns:", df.columns.tolist())

# -------------------------
# Drop Unwanted Columns
# -------------------------
drop_cols = ["AnnouncementCode", "Eligibility", "Audience", "StartDate", "Duration", "ApplicationP", "Attach", "Notes"]
df.drop(columns=drop_cols, inplace=True)

# -------------------------
# Handle Deadline Column
# -------------------------
df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce')
df = df.dropna(subset=['Deadline']).reset_index(drop=True)

# -------------------------
# Handle Missing Values for Important Columns
# -------------------------
fill_values = {
    "Title": "Not Specified",
    "Company": "Unknown Company",
    "Term": "Not Specified",
    "Location": "Unknown Location",
    "JobDescription": "",
    "JobRequirment": "",
    "RequiredQual": "Not Specified",
    "Salary": "Not Disclosed",
    "OpeningDate": pd.NaT,
    "AboutC": "Not Provided"
}
df.fillna(value=fill_values, inplace=True)

# Convert OpeningDate to datetime, fill missing with min date
df["OpeningDate"] = pd.to_datetime(df["OpeningDate"], errors="coerce")
min_date = df["OpeningDate"].min()
df["OpeningDate"].fillna(min_date, inplace=True)
df["Year"] = df["OpeningDate"].dt.year
df["Month"] = df["OpeningDate"].dt.month

# -------------------------
# Salary Cleaning Functions
# -------------------------
def clean_salary(salary):
    """Extract numeric salary from salary string."""
    if pd.isnull(salary):
        return np.nan
    salary = str(salary).lower()
    if 'not disclosed' in salary or 'competitive' in salary or salary.strip() == '':
        return np.nan
    
    match = re.search(r'(\d+[,.]?\d*)', salary.replace(',', ''))
    if match:
        try:
            val = float(match.group(1))
            if val < 1000:
                val *= 1000  # scale up small numbers
            return val
        except:
            return np.nan
    else:
        return np.nan

def extract_currency(salary):
    """Extract currency code from salary string."""
    if pd.isnull(salary):
        return "Unknown"
    salary = str(salary).upper()
    if "AMD" in salary:
        return "AMD"
    elif "USD" in salary:
        return "USD"
    elif "EURO" in salary or "EUR" in salary:
        return "Euro"
    elif "INR" in salary or "₹" in salary:
        return "INR"
    else:
        return "Other/Unknown"

df['Salary_clean'] = df['Salary'].apply(clean_salary)
df['Salary_Currency'] = df['Salary'].apply(extract_currency)

# Filter for known currency salaries (for stats & charts)
salary_known = df[df['Salary_Currency'] != 'Other/Unknown']

# -------------------------
# Job Term Cleaning Function
# -------------------------
def clean_job_term(term):
    """Standardize job term categories."""
    if not isinstance(term, str):
        return np.nan
    
    term_lower = term.lower()

    full_time_keywords = ['full time', 'full-time', 'fulltime', 'full term', 'full-term']
    part_time_keywords = ['part time', 'part-time', 'parttime']
    contract_keywords = ['contract', 'fixed term', 'term appointment', 'renewable term', 'fixed-term', 'termless']
    freelance_keywords = ['freelance', 'free lance']
    temporary_keywords = ['temporary', 'temp']
    internship_keywords = ['intern', 'internship']
    shift_keywords = ['shift', 'night', 'morning', 'afternoon', 'day shift']
    flexible_keywords = ['flexible', 'flex time', 'free schedule', 'flexible hours']
    permanent_keywords = ['permanent', 'indefinite', 'open ended', 'long term', 'long-term']

    if any(k in term_lower for k in full_time_keywords):
        return 'Full-time'
    if any(k in term_lower for k in part_time_keywords):
        return 'Part-time'
    if any(k in term_lower for k in contract_keywords):
        return 'Contract'
    if any(k in term_lower for k in freelance_keywords):
        return 'Freelance'
    if any(k in term_lower for k in temporary_keywords):
        return 'Temporary'
    if any(k in term_lower for k in internship_keywords):
        return 'Internship'
    if any(k in term_lower for k in shift_keywords):
        return 'Shift-based'
    if any(k in term_lower for k in flexible_keywords):
        return 'Flexible'
    if any(k in term_lower for k in permanent_keywords):
        return 'Permanent'

    # Patterns for hours/days per week
    hours_week_match = re.search(r'(\d{1,2})\s*(hours|hrs|h)\s*(per week|weekly|week)', term_lower)
    if hours_week_match:
        hours = int(hours_week_match.group(1))
        if hours >= 35:
            return 'Full-time'
        elif hours >= 15:
            return 'Part-time'
        else:
            return 'Flexible'

    days_week_match = re.search(r'(\d{1,2})\s*(days|day)\s*(per week|weekly|week)', term_lower)
    if days_week_match:
        days = int(days_week_match.group(1))
        if days >= 5:
            return 'Full-time'
        elif days >= 2:
            return 'Part-time'
        else:
            return 'Flexible'

    contract_duration_match = re.search(r'(\d{1,2})\s*(months|month|years|year)', term_lower)
    if contract_duration_match:
        return 'Contract'

    unspecified_keywords = ['not specified', 'non-specified', 'unspecified', 'asap', 'according to', 'immediately']
    if any(k in term_lower for k in unspecified_keywords):
        return 'Other/Unspecified'
    
    return 'Other/Unspecified'

df['Term_Clean_v2'] = df['Term'].apply(clean_job_term)

# -------------------------
# Clustering to Reclassify "Other/Unspecified"
# -------------------------
other_terms = df[df['Term_Clean_v2'] == 'Other/Unspecified']['Term'].dropna().unique()

vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
X = vectorizer.fit_transform(other_terms)

num_clusters = 10
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
kmeans.fit(X)
labels = kmeans.labels_

clustered_terms = pd.DataFrame({'Term': other_terms, 'Cluster': labels})

print("\n--- Terms grouped by cluster ---")
for cluster_num in range(num_clusters):
    print(f"\nCluster {cluster_num}:")
    print(clustered_terms[clustered_terms['Cluster'] == cluster_num]['Term'].tolist())

# Manual cluster to category mapping (adjust based on inspection)
cluster_to_category = {
    0: 'Other/Unspecified',
    1: 'Shift-based',
    2: 'Full-time / Part-time',
    3: 'Full-time / Part-time',
    4: 'Shift-based',
    5: 'Flexible',
    6: 'Flexible',
    7: 'Contract',
    8: 'Contract',
    9: 'Shift-based'
}

term_to_category = dict(zip(clustered_terms['Term'], clustered_terms['Cluster'].map(cluster_to_category)))

def final_term_category(term, original_cat):
    if original_cat != 'Other/Unspecified':
        return original_cat
    return term_to_category.get(term, 'Other/Unspecified')

df['Term_Clean_Final'] = df.apply(lambda row: final_term_category(row['Term'], row['Term_Clean_v2']), axis=1)

print("\nFinal Term Distribution:")
print(df['Term_Clean_Final'].value_counts())

# -------------------------
# KPIs and Summary Stats
# -------------------------
total_jobs = len(df)
unique_titles = df['Title'].nunique()
unique_companies = df['Company'].nunique()
term_counts = df['Term_Clean_Final'].value_counts()
top_locations = df['Location'].value_counts().head(10)
avg_salary_currency = salary_known.groupby('Salary_Currency')['Salary_clean'].mean()

print(f"\nTotal job posts: {total_jobs}")
print(f"Unique job titles: {unique_titles}")
print(f"Unique companies: {unique_companies}")
print("\nJob term distribution:")
print(term_counts)
print("\nTop 10 locations by job count:")
print(top_locations)
print("\nAverage salary by currency:")
print(avg_salary_currency)

df.to_csv('cleaned_jobposts.csv', index=False)
print("Cleaned data saved to cleaned_jobposts.csv")

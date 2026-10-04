import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="NexusFlow | PLG Analytics",
    page_icon="🚀",
    layout="wide"
)

# 2. Custom CSS Injection for Modern SaaS UI
st.markdown("""
    <style>
    /* Main background and font styling */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    div[data-testid="stMetric"] label {
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. App Header
st.title("NexusFlow: Product-Led Growth Engine")
st.markdown("Real-time telemetry tracking user activation loops, retention cohorts, and feature adoption.")
st.markdown("---")

# Load Data with Caching & Safe Date Parsing
@st.cache_data
def load_data():
    try:
        users = pd.read_csv('data/cleaned_users.csv')
        if 'signup_date' in users.columns:
            users['signup_date'] = pd.to_datetime(users['signup_date'])
            
        events = pd.read_csv('data/cleaned_events.csv')
        
        # Safely parse date columns if they exist in the CSV
        date_cols = ['timestamp', 'signup_date', 'signup_week', 'event_week']
        for col in date_cols:
            if col in events.columns:
                events[col] = pd.to_datetime(events[col], errors='coerce')
                
        return users, events
    except FileNotFoundError as e:
        st.error(f"Cleaned dataset files not found inside 'data/': {e}")
        return pd.DataFrame(), pd.DataFrame()

users_df, events_df = load_data()

if users_df.empty or events_df.empty:
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Controls")

min_date = users_df['signup_date'].min().date()
max_date = users_df['signup_date'].max().date()

date_range = st.sidebar.date_input(
    "Signup Date Range", 
    [min_date, max_date], 
    min_value=min_date, 
    max_value=max_date
)

company_sizes = users_df['company_size'].unique().tolist()
selected_sizes = st.sidebar.multiselect("Company Size", company_sizes, default=company_sizes)

channels = users_df['acquisition_channel'].unique().tolist()
selected_channels = st.sidebar.multiselect("Acquisition Channel", channels, default=channels)

# Apply Filters
filtered_users = users_df[
    (users_df['signup_date'].dt.date >= date_range[0]) &
    (users_df['signup_date'].dt.date <= date_range[1]) &
    (users_df['company_size'].isin(selected_sizes)) &
    (users_df['acquisition_channel'].isin(selected_channels))
]

filtered_events = events_df[events_df['user_id'].isin(filtered_users['user_id'])]

# --- TOP-LEVEL EXECUTIVE METRICS ---
total_signups = len(filtered_users)
upgraded_users = filtered_events[filtered_events['event_name'] == 'upgraded_to_paid']['user_id'].unique()
conversion_rate = (len(upgraded_users) / total_signups * 100) if total_signups > 0 else 0

first_project = filtered_events[filtered_events['event_name'] == 'created_project'].groupby('user_id')['days_since_signup'].min()
avg_ttfv = first_project.mean() if not first_project.empty else 0

active_30d = filtered_events[filtered_events['days_since_signup'] >= 30]['user_id'].nunique()
retention_30d = (active_30d / total_signups * 100) if total_signups > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Signups", f"{total_signups:,}")
col2.metric("Free-to-Paid Conversion", f"{conversion_rate:.2f}%")
col3.metric("Avg. Time-to-First-Value", f"{avg_ttfv:.1f} days")
col4.metric("30-Day Retention Rate", f"{retention_30d:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# --- DASHBOARD TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Cohort Retention", 
    "⚡ Feature Impact & 'Aha!'", 
    "📊 Onboarding Funnel", 
    "🎯 Channel & Segment Breakdown"
])

# Tab 1: Cohort Retention Matrix
with tab1:
    st.subheader("Week-over-Week Cohort Retention Matrix")
    st.markdown("Percentage of users returning each week relative to their signup week cohort.")
    
    cohort_pivot = filtered_events.groupby(['signup_week', 'cohort_week'])['user_id'].nunique().unstack()
    cohort_sizes = filtered_users.groupby(pd.to_datetime(filtered_users['signup_date']).dt.to_period('W').dt.start_time)['user_id'].nunique()
    cohort_pivot = cohort_pivot.loc[cohort_pivot.index.intersection(cohort_sizes.index)]
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    if not retention_matrix.empty:
        fig_cohort = px.imshow(
            retention_matrix,
            labels=dict(x="Weeks Since Signup", y="Signup Week", color="Retention (%)"),
            x=[str(i) for i in retention_matrix.columns],
            y=pd.to_datetime(retention_matrix.index).strftime('%Y-%m-%d').tolist(),
            color_continuous_scale="Teal",
            aspect="auto",
            text_auto=".1f"
        )
        fig_cohort.update_layout(
            template="plotly_white",
            margin=dict(t=20, b=20, l=20, r=20),
            font=dict(family="sans-serif", size=12)
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    else:
        st.warning("Insufficient data for the selected filters.")

# Tab 2: Feature Adoption & Aha! Moment
with tab2:
    st.subheader("Feature Adoption & 'Aha! Moment' Correlation")
    st.markdown("Product behaviors correlating strongest with paid plan upgrades.")

    user_feats = pd.pivot_table(
        filtered_events, index='user_id', columns='event_name', values='event_id', aggfunc='count', fill_value=0
    )
    user_feats = (user_feats > 0).astype(int)

    if 'upgraded_to_paid' in user_feats.columns:
        user_feats['did_upgrade'] = user_feats['upgraded_to_paid']
        corrs = user_feats.corr()['did_upgrade'].drop(['upgraded_to_paid', 'did_upgrade'], errors='ignore').sort_values(ascending=True)

        fig_corr = px.bar(
            x=corrs.values, y=corrs.index, orientation='h',
            labels={'x': 'Correlation Coefficient (r)', 'y': 'Feature Action'},
            color=corrs.values, color_continuous_scale="Sunset"
        )
        fig_corr.update_layout(
            template="plotly_white",
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("No upgrade events detected.")

# Tab 3: Onboarding Funnel
with tab3:
    st.subheader("Product Onboarding Conversion Funnel")
    st.markdown("Step-by-step drop-off analysis across core milestones.")

    steps = ['viewed_dashboard', 'created_project', 'invited_team_member', 'exported_report', 'upgraded_to_paid']
    funnel_counts = [total_signups] + [filtered_events[filtered_events['event_name'] == s]['user_id'].nunique() for s in steps]
    funnel_stages = ['Signed Up', 'Viewed Dashboard', 'Created Project', 'Invited Teammate', 'Exported Report', 'Upgraded to Paid']

    fig_funnel = go.Figure(go.Funnel(
        y=funnel_stages, x=funnel_counts,
        textinfo="value+percent initial",
        marker=dict(color=["#0F172A", "#1E293B", "#334155", "#0284C7", "#0EA5E9", "#10B981"])
    ))
    fig_funnel.update_layout(
        template="plotly_white",
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

# Tab 4: Segmentation
with tab4:
    st.subheader("Acquisition Channel & Company Size Breakdown")
    col_a, col_b = st.columns(2)

    with col_a:
        channel_conv = filtered_events.groupby('acquisition_channel')['user_id'].nunique().reset_index(name='active_users')
        fig_chan = px.bar(channel_conv, x='acquisition_channel', y='active_users', title="Active Users by Channel", color='acquisition_channel', color_discrete_sequence=px.colors.qualitative.Prism)
        fig_chan.update_layout(template="plotly_white", margin=dict(t=40, b=20, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_chan, use_container_width=True)

    with col_b:
        size_conv = filtered_events.groupby('company_size')['user_id'].nunique().reset_index(name='active_users')
        fig_size = px.bar(size_conv, x='company_size', y='active_users', title="Active Users by Company Size", color='company_size', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_size.update_layout(template="plotly_white", margin=dict(t=40, b=20, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_size, use_container_width=True)
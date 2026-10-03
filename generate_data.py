import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# 1. Generate Users Table
n_users = 5000
start_date = datetime(2025, 9, 1)
end_date = datetime(2026, 9, 1)

date_range_days = (end_date - start_date).days
signup_dates = [start_date + timedelta(days=int(np.random.randint(0, date_range_days))) for _ in range(n_users)]
signup_dates.sort()

user_ids = [f"usr_{1000 + i}" for i in range(n_users)]
company_sizes = np.random.choice(['Startup (1-10)', 'SMB (11-50)', 'Mid-Market (51-200)', 'Enterprise (200+)'], size=n_users, p=[0.5, 0.3, 0.15, 0.05])
channels = np.random.choice(['Organic Search', 'Paid Ads', 'Product-Led Referral', 'Direct', 'Social'], size=n_users, p=[0.35, 0.25, 0.2, 0.15, 0.05])

users_df = pd.DataFrame({
    'user_id': user_ids,
    'signup_date': signup_dates,
    'company_size': company_sizes,
    'acquisition_channel': channels
})

# 2. Generate Events Table
event_types = ['viewed_dashboard', 'created_project', 'invited_team_member', 'exported_report', 'upgraded_to_paid']
event_weights = [0.45, 0.25, 0.15, 0.10, 0.05]

events_list = []

for _, user in users_df.iterrows():
    # Determine how active a user is based on their channel/randomness
    n_events = int(np.random.gamma(shape=2, scale=15)) + 1
    
    for _ in range(n_events):
        # Event timestamp must be after signup date
        days_after_signup = np.random.exponential(scale=14) # Most activity happens early
        event_time = user['signup_date'] + timedelta(days=days_after_signup)
        
        if event_time <= end_date:
            event_name = np.random.choice(event_types, p=event_weights)
            events_list.append({
                'user_id': user['user_id'],
                'timestamp': event_time,
                'event_name': event_name
            })

events_df = pd.DataFrame(events_list)
events_df = events_df.sort_values(by='timestamp').reset_index(drop=True)
events_df['event_id'] = [f"evt_{200000 + i}" for i in range(len(events_df))]

# Reorder columns
events_df = events_df[['event_id', 'user_id', 'timestamp', 'event_name']]

# Save to CSV files for your EDA and Streamlit app
users_df.to_csv('users.csv', index=False)
events_df.to_csv('events.csv', index=False)

print(f"Generated {len(users_df)} users and {len(events_df)} interaction events successfully!")
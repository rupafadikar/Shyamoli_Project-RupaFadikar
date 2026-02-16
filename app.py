import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Travel Data Analyst Dashboard", layout="wide")
st.title("Travel & Logistics Analysis Dashboard")

# -------------------------------------------------
# DATA PATH
# -------------------------------------------------
DATA_PATH = "travel_data.xlsx"

# -------------------------------------------------
# LOAD DATA (SAFE VERSION)
# -------------------------------------------------
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("Dataset file not found. Please make sure 'travel_data.xlsx' is uploaded to the repository.")
        return pd.DataFrame()

    try:
        df = pd.read_excel(DATA_PATH)

        # Convert Date Columns
        date_cols = ['Journey Date', 'Booked On', 'Issued On']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Lead Time Calculation
        if 'Journey Date' in df.columns and 'Booked On' in df.columns:
            df['Advance Days'] = (df['Journey Date'] - df['Booked On']).dt.days

        return df

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


df = load_data()

# Stop execution if dataframe empty
if df.empty:
    st.stop()

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("Data Filters")

if 'Status' in df.columns:
    status_list = df['Status'].dropna().unique().tolist()

    selected_status = st.sidebar.multiselect(
        "Filter by Status",
        status_list,
        default=status_list
    )

    df = df[df['Status'].isin(selected_status)]

# -------------------------------------------------
# KPI METRICS
# -------------------------------------------------
m1, m2, m3, m4 = st.columns(4)

m1.metric("Total Bookings", len(df))

if 'Net Amount' in df.columns:
    m2.metric("Total Revenue", f"₹{df['Net Amount'].sum():,.2f}")

if 'Status' in df.columns:
    m3.metric("Confirmed Bookings", len(df[df['Status'] == 'Booked']))
    m4.metric("Cancellations", len(df[df['Status'] == 'Cancel']))

# -------------------------------------------------
# VISUAL ANALYSIS
# -------------------------------------------------
col1, col2 = st.columns(2)

# Booking Channels
with col1:
    if 'Booked By' in df.columns:
        st.subheader("Top Booking Channels")

        top_channels = (
            df['Booked By']
            .value_counts()
            .head(10)
            .reset_index()
        )
        top_channels.columns = ['Channel', 'Transactions']

        fig1 = px.bar(
            top_channels,
            x='Transactions',
            y='Channel',
            orientation='h',
            color='Transactions'
        )

        st.plotly_chart(fig1, use_container_width=True)

# Weekly Demand
with col2:
    if 'Journey Date' in df.columns:
        st.subheader("Demand by Day of Week")

        df['Weekday'] = df['Journey Date'].dt.day_name()

        day_order = [
            'Monday','Tuesday','Wednesday',
            'Thursday','Friday','Saturday','Sunday'
        ]

        week_data = (
            df['Weekday']
            .value_counts()
            .reindex(day_order)
            .fillna(0)
            .reset_index()
        )
        week_data.columns = ['Day','Bookings']

        fig2 = px.line(
            week_data,
            x='Day',
            y='Bookings',
            markers=True
        )

        st.plotly_chart(fig2, use_container_width=True)

# -------------------------------------------------
# TABS
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["Route Analysis", "Financials", "Operational Efficiency"]
)

# Route Analysis
with tab1:
    if 'Route' in df.columns and 'Net Amount' in df.columns:
        st.subheader("Top Routes by Revenue")

        route_rev = (
            df.groupby('Route')['Net Amount']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        st.dataframe(route_rev, use_container_width=True)

# Financial Analysis
with tab2:
    if 'Category' in df.columns and 'Net Amount' in df.columns:
        st.subheader("Revenue by Category")

        cat_rev = (
            df.groupby('Category')['Net Amount']
            .sum()
            .reset_index()
        )

        fig3 = px.pie(
            cat_rev,
            values='Net Amount',
            names='Category',
            hole=0.4
        )

        st.plotly_chart(fig3, use_container_width=True)

# Operational Efficiency
with tab3:
    if 'Drivers' in df.columns and 'Net Amount' in df.columns:
        st.subheader("Top Performing Drivers (by Revenue)")

        driver_rev = (
            df.groupby('Drivers')['Net Amount']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig4 = px.bar(
            driver_rev,
            x='Drivers',
            y='Net Amount',
            color='Net Amount'
        )

        st.plotly_chart(fig4, use_container_width=True)

# -------------------------------------------------
# CHURN ANALYSIS
# -------------------------------------------------
st.divider()
st.subheader("🚨 High-Risk Churn Passengers")

if 'Phone number' in df.columns and 'Status' in df.columns:
    churn_data = df.groupby('Phone number').agg(
        Total_Cancellations=('Status', lambda x: (x == 'Cancel').sum()),
        Name=('Name', 'first')
    ).sort_values('Total_Cancellations', ascending=False)

    high_risk = churn_data[churn_data['Total_Cancellations'] >= 2]

    st.write(f"Found {len(high_risk)} passengers with multiple cancellations.")
    st.dataframe(high_risk.head(10))

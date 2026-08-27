import pandas as pd
import streamlit as st
import numpy as np
import altair as alt

# --- PAGE CONFIG & UI ---
st.set_page_config(page_title="Social Security Break-Even Sandbox", layout="wide")
st.title("Social Security Break-Even Sandbox")
st.write("Dynamic break-even analysis incorporating opportunity cost, marginal taxation, and systemic risk.")

# Filing Status Selection
filing_status = st.sidebar.radio("Filing Status", ["Single", "Married (Joint)"])

# --- SIDEBAR INPUTS ---
st.sidebar.header("Claiming Strategy")
if filing_status == "Single":
    claim_age_1 = st.sidebar.slider("Claim Age Strategy 1", 62, 70, 62)
    claim_age_2 = st.sidebar.slider("Claim Age Strategy 2", 62, 70, 67)
else:
    st.sidebar.subheader("Primary Earner Strategy")
    p1_claim_1 = st.sidebar.slider("Primary Claim Strategy 1", 62, 70, 62)
    p1_claim_2 = st.sidebar.slider("Primary Claim Strategy 2", 62, 70, 70)
    
    st.sidebar.subheader("Spouse Strategy")
    p2_claim_1 = st.sidebar.slider("Spouse Claim Strategy 1", 62, 70, 62)
    p2_claim_2 = st.sidebar.slider("Spouse Claim Strategy 2", 62, 70, 67)

st.sidebar.header("Model Assumptions")
pia_1 = st.sidebar.number_input("Primary PIA ($/mo)", value=2500, step=100)
if filing_status == "Married (Joint)":
    spouse_age_diff = st.sidebar.number_input("Spouse Age Difference (Spouse Age - Primary Age)", value=0, step=1)
    pia_2 = st.sidebar.number_input("Spouse PIA ($/mo)", value=1200, step=100)

real_return = st.sidebar.number_input("Expected annual real return (%)", value=5.0, step=0.1) / 100

st.sidebar.header("Tax Assumptions")
t_base = st.sidebar.number_input("T_base: Tax on Base Early Benefit (%)", value=8.0, step=0.5) / 100
t_gap = st.sidebar.number_input("T_gap: Tax on Extra Benefit (The Gap) (%)", value=18.0, step=0.5) / 100
roth_mode = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True)

st.sidebar.header("Systemic Risk (Insolvency 2032)")
benefit_cut = st.sidebar.number_input("Projected Benefit Cut (%)", value=11.0, step=1.0) / 100
cut_age = st.sidebar.number_input("Age Cut Takes Effect", value=69, step=1)

# --- CORE CALCULATION LOGIC ---
def get_monthly_benefit(pia, claim_age, fra=67):
    # Standard Social Security actuarial adjustment factors
    months_diff = (claim_age - fra) * 12
    if months_diff < 0:
        # Early reduction: 5/9 of 1% per month for first 36 months, 5/12 of 1% thereafter
        reduction_months = abs(months_diff)
        if reduction_months <= 36:
            factor = 1 - (reduction_months * (5/9 / 100))
        else:
            factor = 1 - (36 * (5/9 / 100) + (reduction_months - 36) * (5/12 / 100))
    else:
        # Delayed retirement credit: 8% per year (2/3 of 1% per month) up to age 70
        factor = 1 + (months_diff * (2/3 / 100))
    return pia * max(0.5, factor) # Floor safeguard

# (Simulation engine execution mapping cumulative wealth over ages 60 to 104)
ages = np.arange(60, 105, 1/12)
# Placeholder simulation arrays for the two independent user-selected strategies:
wealth_strat_1 = np.cumsum(np.random.normal(1000, 200, len(ages))) # Placeholder math
wealth_strat_2 = np.cumsum(np.random.normal(1100, 200, len(ages))) # Placeholder math

# --- CHARTING ---
chart_data = pd.DataFrame({
    "Age": ages,
    "Strategy 1": wealth_strat_1,
    "Strategy 2": wealth_strat_2
})

chart_melted = chart_data.melt(id_vars=["Age"], var_name="Strategy", value_name="Cumulative Wealth")

chart = alt.Chart(chart_melted).mark_line().encode(
    x=alt.X("Age", title="Age"),
    y=alt.Y("Cumulative Wealth", title="Cumulative Wealth ($)"),
    color=alt.Color("Strategy", legend=alt.Legend(orient="bottom", direction="vertical"))
).properties(height=500).interactive()

st.subheader("Dynamic Break-Even Milestone")
st.altair_chart(chart, use_container_width=True)

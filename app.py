import pandas as pd
import streamlit as st
import numpy as np
import altair as alt

# --- PAGE CONFIG & UI ---
st.set_page_config(page_title="Social Security Break-Even Sandbox", layout="wide")
st.title("Social Security Break-Even Sandbox")
st.write("Dynamic joint retirement modeling incorporating independent claiming strategies, widow's limits, tax bracket compression, and systemic risk.")

# --- SIDEBAR INPUTS ---
filing_status = st.sidebar.radio("Filing Status", ["Single", "Married (Joint)"])

st.sidebar.header("Claiming Strategy")
if filing_status == "Single":
    claim_age_1 = st.sidebar.slider("Claim Age Strategy 1", 62, 70, 62)
    claim_age_2 = st.sidebar.slider("Claim Age Strategy 2", 62, 70, 67)
else:
    st.sidebar.subheader("Strategy 1 (Baseline)")
    p1_claim_1 = st.sidebar.slider("Primary Claim (Strategy 1)", 62, 70, 62)
    p2_claim_1 = st.sidebar.slider("Spouse Claim (Strategy 1)", 62, 70, 62)
    
    st.sidebar.subheader("Strategy 2 (Comparison)")
    p1_claim_2 = st.sidebar.slider("Primary Claim (Strategy 2)", 62, 70, 70)
    p2_claim_2 = st.sidebar.slider("Spouse Claim (Strategy 2)", 62, 70, 67)

st.sidebar.header("Model Assumptions")
pia_1 = st.sidebar.number_input("Primary PIA ($/mo)", value=2500, step=100)

if filing_status == "Married (Joint)":
    pia_2 = st.sidebar.number_input("Spouse PIA ($/mo) [Must be <= Primary]", value=1200, step=100)
    spouse_age_diff = st.sidebar.number_input("Spouse Age Difference (Spouse Age - Primary Age)", value=0, step=1)
    
    st.sidebar.subheader("Mortality & Survivor Settings")
    first_death_person = st.sidebar.selectbox("Who Passes Away First?", ["Primary Earner", "Spouse"])
    
    # Self-consistent dynamic label based on who passes away first
    if first_death_person == "Primary Earner":
        age_of_first_death = st.sidebar.number_input("Age of Primary Earner at First Death", value=85, step=1)
    else:
        age_of_first_death = st.sidebar.number_input("Age of Spouse at First Death", value=83, step=1)

real_return = st.sidebar.number_input("Expected annual real return (%)", value=5.0, step=0.1) / 100

st.sidebar.header("Tax Assumptions")
t_base = st.sidebar.number_input("T_base: Tax on Base Early Benefit (%)", value=8.0, step=0.5) / 100
t_gap = st.sidebar.number_input("T_gap: Tax on Extra Benefit (The Gap) (%)", value=18.0, step=0.5) / 100
roth_mode = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True)

st.sidebar.header("Systemic Risk (Insolvency 2032)")
benefit_cut = st.sidebar.number_input("Projected Benefit Cut (%)", value=11.0, step=1.0) / 100
cut_age = st.sidebar.number_input("Primary Age Cut Takes Effect", value=69, step=1)

# --- BENEFIT & WIDOW'S LIMIT CALCULATION LOGIC ---
def get_monthly_benefit(pia, claim_age, fra=67):
    months_diff = (claim_age - fra) * 12
    if months_diff < 0:
        reduction_months = abs(months_diff)
        if reduction_months <= 36:
            factor = 1 - (reduction_months * (5/9 / 100))
        else:
            factor = 1 - (36 * (5/9 / 100) + (reduction_months - 36) * (5/12 / 100))
    else:
        factor = 1 + (months_diff * (2/3 / 100))
    return pia * max(0.5, factor)

def calculate_joint_lifetime_wealth(p1_claim, p2_claim, pia_p1, pia_p2, age_diff, death_person, death_age):
    # Simulation horizon from age 60 to 100 for primary earner
    ages = np.arange(60, 101, 1/12)
    portfolio_balance = 0
    
    p1_benefit_full = get_monthly_benefit(pia_p1, p1_claim)
    p2_benefit_full = get_monthly_benefit(pia_p2, p2_claim)
    
    # Widow's limit (RIB-LIM): If primary claims early (< FRA 67), survivor benefit is capped at reduced amount or 82.5% of PIA
    survivor_cap = max(p1_benefit_full, 0.825 * pia_p1) if p1_claim >= 67 else p1_benefit_full
    
    monthly_growth = (1 + real_return)**(1/12) - 1
    wealth_path = []
    
    for age in ages:
        spouse_age = age + age_diff
        
        # Determine active benefits based on age and mortality
        p1_active = p1_benefit_full if age >= p1_claim else 0
        p2_active = p2_benefit_full if spouse_age >= p2_claim else 0
        
        is_survivor_phase = False
        if filing_status == "Married (Joint)":
            if death_person == "Primary Earner":
                if age >= death_age:
                    is_survivor_phase = True
                    p1_active = 0
                    p2_active = max(p2_active, survivor_cap)
            else:
                if spouse_age >= death_age:
                    is_survivor_phase = True
                    p2_active = 0  # Primary earner keeps their own benefit
                    
        monthly_household_benefit = p1_active + p2_active
        
        # Apply 2032 Systemic Risk Cut if applicable
        if age >= cut_age:
            monthly_household_benefit *= (1 - benefit_cut)
            
        # Tax application (Simulating bracket compression if in survivor phase)
        effective_tax = t_base if not is_survivor_phase else (t_base * 1.35)
        after_tax_benefit = monthly_household_benefit * (1 - effective_tax)
        
        portfolio_balance = portfolio_balance * (1 + monthly_growth) + after_tax_benefit
        wealth_path.append(portfolio_balance)
        
    return ages, np.array(wealth_path)

# --- EXECUTE STRATEGIES ---
ages = np.arange(60, 101, 1/12)
if filing_status == "Single":
    _, wealth_1 = calculate_joint_lifetime_wealth(claim_age_1, 62, 2500, 0, 0, "Primary Earner", 150)
    _, wealth_2 = calculate_joint_lifetime_wealth(claim_age_2, 62, 2500, 0, 0, "Primary Earner", 150)
    label_1, label_2 = f"Claim at {claim_age_1}", f"Claim at {claim_age_2}"
else:
    _, wealth_1 = calculate_joint_lifetime_wealth(p1_claim_1, p2_claim_1, pia_1, pia_2, spouse_age_diff, first_death_person, age_of_first_death)
    _, wealth_2 = calculate_joint_lifetime_wealth(p1_claim_2, p2_claim_2, pia_1, pia_2, spouse_age_diff, first_death_person, age_of_first_death)
    label_1 = f"Strategy 1 (P1: {p1_claim_1}, Spouse: {p2_claim_1})"
    label_2 = f"Strategy 2 (P1: {p1_claim_2}, Spouse: {p2_claim_2})"

# --- CHARTING ---
chart_data = pd.DataFrame({
    "Age": ages,
    label_1: wealth_1,
    label_2: wealth_2
})

chart_melted = chart_data.melt(id_vars=["Age"], var_name="Strategy", value_name="Cumulative Wealth")

chart = alt.Chart(chart_melted).mark_line().encode(
    x=alt.X("Age", title="Primary Earner Age"),
    y=alt.Y("Cumulative Wealth", title="Cumulative Household Wealth ($)"),
    color=alt.Color("Strategy", legend=alt.Legend(orient="bottom", direction="vertical"))
).properties(height=500).interactive()

st.subheader("Dynamic Joint Break-Even Analysis")
st.altair_chart(chart, use_container_width=True)

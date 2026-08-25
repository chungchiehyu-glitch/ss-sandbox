import streamlit as st
import pandas as pd

st.set_page_config(page_title="SS Compounding Sandbox", layout="wide")
st.title("Social Security Break-Even Sandbox")
st.write("Dynamic break-even analysis incorporating opportunity cost, marginal taxation, and systemic risk.")

# --- INSTRUCTIONS EXPANDER ---
with st.expander("📖 How to use this tool (and why it matters)"):
    st.markdown("""
    ### The Core Concept
    Standard Social Security calculators assume you spend your benefits in a vacuum. This sandbox models the **opportunity cost** of your claiming decision. 
    
    If you claim early at 62, you don't have to sell your own investments to fund your life during the 8-year delay to age 70. By leaving your portfolio alone, you are effectively letting that money compound. If that compounding interest outpaces the larger Age 70 payout, you achieve "escape velocity"—a perpetual endowment where the delayed strategy never catches up.

    ### How to Adjust the Variables
    *   **Model Assumptions:** Set your expected base payout (PIA) and your portfolio's real, inflation-adjusted return. (A 5% real return is a common benchmark for a diversified, factor-tilted equity portfolio).
    *   **Tax Assumptions (The Marginal Framework):** 
        *   **T_62:** The effective tax rate on your baseline early benefits.
        *   **T_gap:** The marginal tax rate on the *extra* benefits you get by delaying to 70. Because the IRS taxes benefits based on "provisional income" (which includes 50% of your Social Security check), larger delayed checks inherently push more of those extra dollars into higher taxable brackets.
        *   **Roth IRA Toggle:** If your investments are shielded in a tax-free Roth, leave this **ON**. If they are in a standard brokerage, turn it **OFF** to apply an annual tax drag to your compounding growth.
    *   **Systemic Risk (Insolvency 2032):** The Social Security Trust Fund is projected to be depleted in the early 2030s. If Congress does not act, standard law dictates an automatic, across-the-board benefit cut of up to 22%. Use these sliders to see how an across-the-board haircut disproportionately damages the Age 70 delayed strategy.

    ### Reading the Chart
    Look for where the lines cross. That is your **break-even age**. If the Age 62 (dark blue) line stays above the Age 70 (red) line forever, you have achieved mathematical escape velocity.
    """)

st.caption("* **PIA (Primary Insurance Amount):** The base monthly benefit you would receive if you claim at your exact full retirement age.*")

# --- Interactive Sidebar Controls ---
st.sidebar.header("Model Assumptions")
pia = st.sidebar.slider("Primary Insurance Amount (PIA)", 1000, 5000, 2500, 50)
roi = st.sidebar.slider("Expected annual real return (return over inflation, %)", 0.0, 12.0, 5.0, 0.1) / 100

st.sidebar.divider()
st.sidebar.header("Tax Assumptions")

t_62_display = st.sidebar.slider("T_62: Tax on Base Age 62 Benefit (%)", 0.0, 40.0, 0.0, 1.0)
default_t_gap = max(22.0, t_62_display)
t_gap_display = st.sidebar.slider("T_gap: Tax on Extra Benefit (The Gap) (%)", min_value=t_62_display, max_value=40.0, value=default_t_gap, step=1.0)

t_62 = t_62_display / 100
t_gap = t_gap_display / 100

is_roth = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True)
tax_drag = 0.0

if not is_roth:
    tax_drag = st.sidebar.slider("Estimated Tax Drag on Growth (%)", 0.0, 40.0, 15.0, 1.0) / 100

st.sidebar.divider()
st.sidebar.header("Systemic Risk (Insolvency 2032)")
insolvency_cut = st.sidebar.slider("Projected Benefit Cut (%)", 0.0, 22.0, 22.0, 1.0) / 100
cut_age = st.sidebar.slider("Age Cut Takes Effect", 62, 104, 69, 1)

# --- Core Math Engine ---
effective_roi = roi * (1 - tax_drag)
monthly_rate = (1 + effective_roi) ** (1/12) - 1

gross_62 = pia * 0.70
gross_67 = pia * 1.00
gross_70 = pia * 1.24

net_62 = gross_62 * (1 - t_62)
gap_67 = gross_67 - gross_62
net_67 = net_62 + (gap_67 * (1 - t_gap))
gap_70 = gross_70 - gross_62
net_70 = net_62 + (gap_70 * (1 - t_gap))

# --- Dynamic Break-Even Numerical Scanner ---
def get_dynamic_be_age(age_early, cf_early_base, age_late, cf_late_base, rate, cut_age_thresh, cut_pct):
    w_early = 0.0
    w_late = 0.0
    
    # Scan month-by-month up to age 115
    for current_year in range(age_early, 115):
        active_cut = cut_pct if current_year >= cut_age_thresh else 0.0
        cf_early = cf_early_base * (1 - active_cut)
        cf_late = cf_late_base * (1 - active_cut) if current_year >= age_late else 0.0
        
        for month in range(1, 13):
            w_early = w_early * (1 + rate) + cf_early
            w_late = w_late * (1 + rate) + cf_late
            
            # Check if the delayed strategy has overtaken the early strategy
            if current_year >= age_late and w_late > w_early:
                return current_year + (month / 12)
                
    return "Escape Velocity 🚀"

be_62_67 = get_dynamic_be_age(62, net_62, 67, net_67, monthly_rate, cut_age, insolvency_cut)
be_62_70 = get_dynamic_be_age(62, net_62, 70, net_70, monthly_rate, cut_age, insolvency_cut)
be_67_70 = get_dynamic_be_age(67, net_67, 70, net_70, monthly_rate, cut_age, insolvency_cut)

def format_age(val):
    if isinstance(val, str): return val
    return f"Age {val:.1f}"

# Display Break-Even Metrics
st.subheader("Dynamic Break-Even Milestones")
cols = st.columns(3)
cols[0].metric("62 vs 67", format_age(be_62_67))
cols[1].metric("62 vs 70", format_age(be_62_70))
cols[2].metric("67 vs 70", format_age(be_67_70))
st.divider()

# --- Time-Series Engine ---
ages = list(range(62, 105)) 
chart_data = {"Claim at 62": [], "Claim at 67": [], "Claim at 70": []}
wealth_62, wealth_67, wealth_70 = 0, 0, 0

for age in ages:
    chart_data["Claim at 62"].append(wealth_62)
    chart_data["Claim at 67"].append(wealth_67)
    chart_data["Claim at 70"].append(wealth_70)

    active_cut = insolvency_cut if age >= cut_age else 0.0
    cf_62 = net_62 * (1 - active_cut)
    cf_67 = net_67 * (1 - active_cut)
    cf_70 = net_70 * (1 - active_cut)
    
    for month in range(12):
        wealth_62 = wealth_62 * (1 + monthly_rate) + cf_62
        if age >= 67:
            wealth_67 = wealth_67 * (1 + monthly_rate) + cf_67
        if age >= 70:
            wealth_70 = wealth_70 * (1 + monthly_rate) + cf_70
            
df = pd.DataFrame(chart_data)
df["Age"] = ages
df = df.set_index("Age")

st.line_chart(df, width=0, height=500, use_container_width=True, x_label="Age", y_label="Cumulative Wealth ($)")

st.sidebar.divider()
st.sidebar.caption("© 2026 Chung-Chieh Yu. All Rights Reserved.")
st.sidebar.caption("💡 **Have questions or suggestions?** [Open an issue on GitHub](https://github.com/chungchiehyu-glitch/ss-sandbox/issues) to join the discussion.")

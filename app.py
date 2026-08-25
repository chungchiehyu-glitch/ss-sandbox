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
pia = st.sidebar.slider("Primary Insurance Amount (PIA)", 1000, 4000, 2500, 50)
roi = st.sidebar.slider("Expected annual real return (return over inflation, %)", 0.0, 12.0, 5.0, 0.1) / 100

st.sidebar.divider()
st.sidebar.header("Tax Assumptions")

# Independent marginal tax sliders
t_62 = st.sidebar.slider("T_62: Tax on Base Age 62 Benefit (%)", 0.0, 40.0, 0.0, 1.0) / 100
t_gap = st.sidebar.slider("T_gap: Tax on Extra Benefit (The Gap) (%)", 0.0, 40.0, 22.0, 1.0) / 100

is_roth = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True)
tax_drag = 0.0

if not is_roth:
    tax_drag = st.sidebar.slider("Estimated Tax Drag on Growth (%)", 0.0, 40.0, 15.0, 1.0) / 100

st.sidebar.divider()
st.sidebar.header("Systemic Risk (Insolvency 2032)")

# Allows the user to model future government benefit cuts, capped at 22%
insolvency_cut = st.sidebar.slider("Projected Benefit Cut (%)", 0.0, 22.0, 22.0, 1.0) / 100
cut_age = st.sidebar.slider("Age Cut Takes Effect", 62, 104, 69, 1)

# Calculate effective return after tax drag on the portfolio
effective_roi = roi * (1 - tax_drag)
monthly_rate = effective_roi / 12

# --- Core Benefit Math (Pre-Cut) ---
gross_62 = pia * 0.70
gross_67 = pia * 1.00
gross_70 = pia * 1.24

# The base is taxed at T_62
net_62 = gross_62 * (1 - t_62)

# The extra benefits (the gap) are taxed at T_gap
gap_67 = gross_67 - gross_62
net_67 = net_62 + (gap_67 * (1 - t_gap))

gap_70 = gross_70 - gross_62
net_70 = net_62 + (gap_70 * (1 - t_gap))

# --- Mathematical Engine ---
ages = list(range(62, 105)) 

chart_data = {
    "Claim at 62": [],
    "Claim at 67": [],
    "Claim at 70": []
}

wealth_62 = 0
wealth_67 = 0
wealth_70 = 0

for age in ages:
    # Determine if the systemic cut is active for this specific year
    active_cut = insolvency_cut if age >= cut_age else 0.0
    
    # Apply the haircut to the net cash flow
    cf_62 = net_62 * (1 - active_cut)
    cf_67 = net_67 * (1 - active_cut)
    cf_70 = net_70 * (1 - active_cut)
    
    for month in range(12):
        wealth_62 = wealth_62 * (1 + monthly_rate) + cf_62
        if age >= 67:
            wealth_67 = wealth_67 * (1 + monthly_rate) + cf_67
        if age >= 70:
            wealth_70 = wealth_70 * (1 + monthly_rate) + cf_70
            
    chart_data["Claim at 62"].append(wealth_62)
    chart_data["Claim at 67"].append(wealth_67)
    chart_data["Claim at 70"].append(wealth_70)

df = pd.DataFrame(chart_data)
df["Age"] = ages
df = df.set_index("Age")

# --- Visualization ---
st.line_chart(
    df, 
    width=0, 
    height=500, 
    use_container_width=True,
    x_label="Age",
    y_label="Cumulative Wealth ($)"
)

# --- Footer & Feedback ---
st.sidebar.divider()
st.sidebar.caption("© 2026 Chung-Chieh Yu. All Rights Reserved.")
st.sidebar.caption("💡 **Have questions or suggestions?** [Open an issue on GitHub](https://github.com/chungchiehyu-glitch/ss-sandbox/issues) to join the discussion.")

# Using standard Markdown instead of raw HTML to bypass Streamlit's security sanitizer
st.sidebar.markdown("[![Visits](https://profile-counter.glitch.me/ss-sandbox-chungchiehyu/count.svg)](https://github.com/chungchiehyu-glitch/ss-sandbox)")

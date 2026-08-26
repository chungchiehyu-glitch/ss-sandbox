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
    
    If you claim early, you don't have to sell your own investments to fund your life during the delay years. By leaving your portfolio alone, you are effectively letting that money compound. If that compounding interest outpaces the larger delayed payout, you achieve "escape velocity"—a perpetual endowment where the delayed strategy never catches up.

    ### How to Adjust the Variables
    *   **Claiming Strategy:** Choose any two ages to compare (e.g., 62 vs 65, or 65 vs 70).
    *   **Model Assumptions:** Set your expected base payout (PIA) and your portfolio's real return. The default yield reflects current real rates on intermediate Treasury Inflation-Protected Securities (TIPS), representing a risk-free benchmark.
    *   **Tax Assumptions (The Marginal Framework):** 
        *   **T_base:** The effective tax rate on your baseline early benefits.
        *   **T_gap:** The marginal tax rate on the *extra* benefits you get by delaying. 
        *   **Roth IRA Toggle:** If your investments are shielded in a tax-free Roth, leave this **ON**. If they are in a standard brokerage, turn it **OFF** to apply an annual tax drag to your compounding growth.
    *   **Systemic Risk (Insolvency 2032):** The Social Security Trust Fund is projected to be depleted in the early 2030s. If Congress does not act, standard law dictates an automatic, across-the-board benefit cut of up to 22%.

    ### Reading the Chart
    Look for where the lines cross. That is your **break-even age**. If the Early (dark blue) line stays above the Late (red) line forever, you have achieved mathematical escape velocity.
    """)

st.caption("* **PIA (Primary Insurance Amount):** The base monthly benefit you would receive if you claim at your exact full retirement age.*")

# --- Interactive Sidebar Controls ---
st.sidebar.header("Claiming Strategy")
early_claim = st.sidebar.slider("Early Claim Age", 62, 69, 62, 1)
# Ensure the late claim slider always starts higher than the early claim slider
late_claim = st.sidebar.slider("Late Claim Age", early_claim + 1, 70, max(67, early_claim + 1), 1)

st.sidebar.divider()
st.sidebar.header("Model Assumptions")
pia = st.sidebar.slider("Primary Insurance Amount (PIA)", 1000, 5000, 2500, 50)
# Updated default ROI to 2.37% based on current intermediate TIPS yields
roi = st.sidebar.slider("Expected annual real return (TIPS proxy, %)", 0.0, 12.0, 2.37, 0.01) / 100

st.sidebar.divider()
st.sidebar.header("Tax Assumptions")
t_62_display = st.sidebar.slider("T_base: Tax on Base Early Benefit (%)", 0.0, 40.0, 0.0, 1.0)
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
def get_pia_multiplier(age):
    # Standard SSA multipliers assuming a Full Retirement Age of 67
    multipliers = {
        62: 0.70, 63: 0.75, 64: 0.80, 65: 0.8667, 
        66: 0.9333, 67: 1.00, 68: 1.08, 69: 1.16, 70: 1.24
    }
    return multipliers.get(age, 1.0)

effective_roi = roi * (1 - tax_drag)
monthly_rate = (1 + effective_roi) ** (1/12) - 1

# Dynamically calculate payouts based on user-selected ages
gross_early = pia * get_pia_multiplier(early_claim)
gross_late = pia * get_pia_multiplier(late_claim)

net_early = gross_early * (1 - t_62)
gap_late = gross_late - gross_early
net_late = net_early + (gap_late * (1 - t_gap))

# --- Dynamic Break-Even Numerical Scanner ---
def get_dynamic_be_age(age_early, cf_early_base, age_late, cf_late_base, rate, cut_age_thresh, cut_pct):
    w_early = 0.0
    w_late = 0.0
    
    for current_year in range(age_early, 115):
        active_cut = cut_pct if current_year >= cut_age_thresh else 0.0
        cf_early = cf_early_base * (1 - active_cut)
        cf_late = cf_late_base * (1 - active_cut) if current_year >= age_late else 0.0
        
        for month in range(1, 13):
            w_early = w_early * (1 + rate) + cf_early
            w_late = w_late * (1 + rate) + cf_late
            
            if current_year >= age_late and w_late > w_early:
                return current_year + (month / 12)
                
    return "Escape Velocity 🚀"

be_age = get_dynamic_be_age(early_claim, net_early, late_claim, net_late, monthly_rate, cut_age, insolvency_cut)

def format_age(val):
    if isinstance(val, str): return val
    return f"Age {val:.1f}"

# Display Break-Even Metric
st.subheader("Dynamic Break-Even Milestone")
st.metric(f"Claim at {early_claim} vs Claim at {late_claim}", format_age(be_age))
st.divider()

# --- Time-Series Engine ---
ages = list(range(early_claim, 105)) 
chart_data = {
    f"Claim at {early_claim}": [], 
    f"Claim at {late_claim}": []
}
wealth_early, wealth_late = 0, 0

for age in ages:
    chart_data[f"Claim at {early_claim}"].append(wealth_early)
    chart_data[f"Claim at {late_claim}"].append(wealth_late)

    active_cut = insolvency_cut if age >= cut_age else 0.0
    cf_early = net_early * (1 - active_cut)
    cf_late = net_late * (1 - active_cut) if age >= late_claim else 0.0
    
    for month in range(12):
        wealth_early = wealth_early * (1 + monthly_rate) + cf_early
        wealth_late = wealth_late * (1 + monthly_rate) + cf_late
            
df = pd.DataFrame(chart_data)
df["Age"] = ages
df = df.set_index("Age")

st.line_chart(df, width=0, height=500, use_container_width=True, x_label="Age", y_label="Cumulative Wealth ($)")

st.sidebar.divider()
st.sidebar.caption("© 2026 Chung-Chieh Yu. All Rights Reserved.")
st.sidebar.caption("💡 **Have questions or suggestions?** [Open an issue on GitHub](https://github.com/chungchiehyu-glitch/ss-sandbox/issues) to join the discussion.")

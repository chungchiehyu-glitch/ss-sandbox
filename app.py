import streamlit as st
import pandas as pd

st.set_page_config(page_title="SS Compounding Sandbox", layout="wide")
st.title("Social Security Break-Even Sandbox")
st.write("Dynamic break-even analysis incorporating opportunity cost, compound growth, and taxation.")

st.caption("* **PIA (Primary Insurance Amount):** The base monthly benefit you would receive if you claim at your exact full retirement age.*")

# --- Interactive Sidebar Controls ---
st.sidebar.header("Model Assumptions")

pia = st.sidebar.slider("Primary Insurance Amount (PIA)", 1000, 4000, 2500, 50)
roi = st.sidebar.slider("Expected annual real return (return over inflation, %)", 0.0, 12.0, 5.0, 0.1) / 100

st.sidebar.divider()
st.sidebar.header("Tax Assumptions")

# NEW: Slider for income tax on the Social Security benefits themselves
ss_tax_rate = st.sidebar.slider("Effective Income Tax on SS Benefits (%)", 0.0, 40.0, 12.0, 1.0) / 100

is_roth = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True)
tax_drag = 0.0

if not is_roth:
    # Tax drag only applies to the growth of the investments
    tax_drag = st.sidebar.slider("Estimated Tax Drag on Growth (%)", 0.0, 40.0, 15.0, 1.0) / 100

# Calculate effective return after tax drag on the portfolio
effective_roi = roi * (1 - tax_drag)
monthly_rate = effective_roi / 12

# Calculate the actual take-home benefit after income taxes
after_tax_retention = 1.0 - ss_tax_rate

# Benefit scaling rules (Simplified for Age 67) applied to after-tax amounts
benefit_62 = (pia * 0.70) * after_tax_retention
benefit_67 = (pia * 1.00) * after_tax_retention
benefit_70 = (pia * 1.24) * after_tax_retention

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
    for month in range(12):
        wealth_62 = wealth_62 * (1 + monthly_rate) + benefit_62
        if age >= 67:
            wealth_67 = wealth_67 * (1 + monthly_rate) + benefit_67
        if age >= 70:
            wealth_70 = wealth_70 * (1 + monthly_rate) + benefit_70
            
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
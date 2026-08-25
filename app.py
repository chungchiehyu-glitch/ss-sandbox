# Calculate effective return after tax drag on the portfolio
effective_roi = roi * (1 - tax_drag)

# 1. FIXED: Geometric compounding for the monthly rate
monthly_rate = (1 + effective_roi) ** (1/12) - 1

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
    # 2. FIXED: Append current balances BEFORE applying the current year's growth and benefits.
    # This ensures age 67 shows $0, and age 68 shows the $12k accumulated during year 67.
    chart_data["Claim at 62"].append(wealth_62)
    chart_data["Claim at 67"].append(wealth_67)
    chart_data["Claim at 70"].append(wealth_70)

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

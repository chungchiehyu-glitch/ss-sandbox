import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="SS Compounding Sandbox", layout="wide")
st.title("Social Security Break-Even Sandbox")
st.write("Dynamic break-even analysis incorporating opportunity cost, marginal taxation, and systemic risk.")

# --- Interactive Sidebar Controls ---
filing_status = st.sidebar.radio("Filing Status", ["Single", "Married (Joint)"], key="filing_status_radio")

# --- DYNAMIC INSTRUCTIONS EXPANDER ---
with st.expander("📖 How to use this tool (and why it matters)"):
    if filing_status == "Single":
        st.markdown("""
        ### The Core Concept for Single Filers
        Standard Social Security calculators assume you spend your benefits in a vacuum. This sandbox models the **opportunity cost** of your individual claiming decision. 
        
        If you claim early, you don't have to sell your own investments to fund your life during the delay years. By leaving your portfolio alone, you are effectively letting that money compound. If that compounding interest outpaces the larger delayed payout, you achieve "escape velocity"—a perpetual endowment where the delayed strategy never catches up.

        ### How to Adjust the Single Variables
        * **Claiming Strategy:** Choose any two ages to compare (e.g., claiming at 62 versus waiting until 67 or 70).
        * **Model Assumptions:** Set your expected base payout (PIA) and your portfolio's real return. The default yield reflects current real rates on intermediate Treasury Inflation-Protected Securities (TIPS).
        * **Tax Assumptions:** Adjust $T_{base}$ for baseline early benefits and $T_{gap}$ for the marginal tax bracket hit on your extra delayed benefits.
        * **Systemic Risk (Insolvency 2032):** Models an automatic across-the-board benefit cut if the Trust Fund depletes.

        ### Reading the Chart
        Look for where the lines cross. That is your **break-even age**. If the early line stays above the late line forever without crossing, you have achieved mathematical escape velocity.
        """)
    else:
        st.markdown("""
        ### The Core Concept for Couples
        Standard Social Security calculators evaluate each spouse in a vacuum. This joint sandbox models the **opportunity cost and combined cash flow** of a coordinated spousal claiming strategy. 

        When a couple coordinates their claim, the decision is about managing the **higher earner's delayed credit** alongside the **survivor benefit floor** across asymmetric lifespans.

        ### How to Adjust the Joint Variables
        * **Claiming Strategy (Strategy 1 vs. Strategy 2):** Compare two distinct household approaches (e.g., both claiming early at 62 versus the higher earner waiting until 70).
        * **Age Difference & PIA:** Set each spouse's Primary Insurance Amount (PIA) and their exact age offset. A negative age difference means the lower earner is younger.
        * **Survivor & Mortality:** Model individual death ages for both spouses. The chart and simulation automatically truncate when the final surviving spouse passes away.
        * **The Joint Marginal Tax Framework ($T_{base}$ & $T_{gap}$):** Account for Married Filing Jointly brackets and the marginal tax rate applied to incremental delayed benefits.
        * **Systemic Risk:** Apply projected benefit cuts cleanly across active and survivor phases.

        ### Reading the Chart
        Look for where the cumulative wealth lines cross. That is your **joint break-even age**. If the Early strategy line stays above the Delayed strategy line forever without crossing, early compounding wins. If they cross, the delayed strategy achieves dominance past that milestone.
        """)

st.caption("* **PIA (Primary Insurance Amount):** The base monthly benefit you would receive if you claim at your exact full retirement age.*")

st.sidebar.header("Claiming Strategy")

if filing_status == "Single":
    early_claim = st.sidebar.slider("Early Claim Age", 62, 69, 62, 1, key="single_early")
    late_claim_min = max(63, early_claim + 1)
    late_claim = st.sidebar.slider("Late Claim Age", late_claim_min, 70, max(67, late_claim_min), 1, key="single_late")
else:
    st.sidebar.subheader("Strategy 1 (Baseline)")
    h_claim_1 = st.sidebar.slider("Higher Earner Claim (Strategy 1)", 62, 70, 62, 1, key="h_c1")
    if h_claim_1 > 62:
        l_claim_1 = st.sidebar.slider("Lower Earner Claim (Strategy 1)", 62, h_claim_1, min(62, h_claim_1), 1, key="l_c1")
    else:
        st.sidebar.text("Lower Earner Claim (Strategy 1): Age 62")
        l_claim_1 = 62
    
    st.sidebar.subheader("Strategy 2 (Comparison)")
    h_claim_2 = st.sidebar.slider("Higher Earner Claim (Strategy 2)", 62, 70, 70, 1, key="h_c2")
    if h_claim_2 > 62:
        l_claim_2 = st.sidebar.slider("Lower Earner Claim (Strategy 2)", 62, h_claim_2, 62, 1, key="l_c2")
    else:
        st.sidebar.text("Lower Earner Claim (Strategy 2): Age 62")
        l_claim_2 = 62

st.sidebar.divider()
st.sidebar.header("Model Assumptions")
h_pia = st.sidebar.slider("Higher Earner PIA", 1000, 5000, 2500, 50, key="pia_higher")

if filing_status == "Married (Joint)":
    max_lower_pia = min(h_pia, 5000)
    default_lower_pia = min(1200, max_lower_pia)
    
    l_pia = st.sidebar.slider("Lower Earner PIA", 0, max_lower_pia, default_lower_pia, 50, key="pia_lower_val")
    earner_age_diff = st.sidebar.slider("Lower Earner Age Difference (Lower Age - Higher Age)", -25, 25, 0, 1, key="earner_age_diff_val")
    
    st.sidebar.subheader("Survivor & Mortality")
    h_death_age = st.sidebar.slider("Higher Earner Age at Death", 70, 104, 85, 1, key="h_death_age_val")
    l_death_age = st.sidebar.slider("Lower Earner Age at Death", 70, 104, 90, 1, key="l_death_age_val")
else:
    earner_age_diff = 0
    l_pia = 0
    h_death_age = 105
    l_death_age = 105

# Session state setup for the Reset Button
if "roi_val" not in st.session_state:
    st.session_state.roi_val = 2.37

def reset_roi():
    st.session_state.roi_val = 2.37

roi_display = st.sidebar.slider(
    "Expected annual real return (%)", 
    0.0, 12.0, 
    key="roi_val", 
    step=0.01,
    help="The default 2.37% reflects the current risk-free real yield on a 10-Year Treasury Inflation-Protected Security (TIPS), which closely matches the duration of the delayed claiming gap."
)

st.sidebar.button("↺ Reset to 10-Year TIPS yield (2.37%)", on_click=reset_roi)

roi = roi_display / 100

st.sidebar.divider()
st.sidebar.header("Tax Assumptions")
t_62_display = st.sidebar.slider("T_base: Tax on Base Early Benefit (%)", 0.0, 40.0, 0.0, 1.0, key="t_base_slider")
default_t_gap = max(22.0, t_62_display)
t_gap_display = st.sidebar.slider("T_gap: Tax on Extra Benefit (The Gap) (%)", min_value=t_62_display, max_value=40.0, value=default_t_gap, step=1.0, key="t_gap_slider")

t_62 = t_62_display / 100
t_gap = t_gap_display / 100

is_roth = st.sidebar.toggle("Investments held in Roth IRA (Tax-Free)", value=True, key="roth_toggle")
tax_drag = 0.0

if not is_roth:
    tax_drag = st.sidebar.slider("Estimated Tax Drag on Growth (%)", 0.0, 40.0, 15.0, 1.0, key="tax_drag_slider") / 100

st.sidebar.divider()
st.sidebar.header("Systemic Risk (Insolvency 2032)")
insolvency_cut = st.sidebar.slider("Projected Benefit Cut (%)", 0.0, 22.0, 22.0, 1.0, key="insolvency_slider") / 100

cut_age_label = "Age (Higher Earner) When Cut Takes Effect" if filing_status == "Married (Joint)" else "Age When Cut Takes Effect"
cut_age = st.sidebar.slider(cut_age_label, 62, 104, 69, 1, key="cut_age_slider")

# --- Core Math Engine ---
def get_pia_multiplier(age):
    multipliers = {
        62: 0.70, 63: 0.75, 64: 0.80, 65: 0.8667, 
        66: 0.9333, 67: 1.00, 68: 1.08, 69: 1.16, 70: 1.24
    }
    return multipliers.get(age, 1.0)

effective_roi = roi * (1 - tax_drag)
monthly_rate = (1 + effective_roi) ** (1/12) - 1

if filing_status == "Single":
    label_early = f"Claim at {early_claim}"
    label_late = f"Claim at {late_claim}"
else:
    label_early = f"Strategy 1 (Higher: {h_claim_1}, Lower: {l_claim_1})"
    label_late = f"Strategy 2 (Higher: {h_claim_2}, Lower: {l_claim_2})"


def joint_net_cashflow(h_age, l_age, h_alive, l_alive, h_c, l_c, h_pia_val, l_pia_val, base_h_c, base_l_c, h_pia_base_val, l_pia_base_val, t_base, t_gap_rate, is_baseline_strategy):
    """
    Computes the net household Social Security cash flow for one strategy at one point in time.

    KEY FIX: each spouse's claimed benefit amount (h_amt / l_amt) depends ONLY on whether
    they have reached their own claiming age relative to their own current age -- NOT on
    whether they are still alive. Alive/dead status is then used separately to decide which
    combination rule applies (both alive / one alive / survivor). This preserves the deceased
    higher earner's (larger, especially under delayed claiming) benefit amount so the survivor
    step-up rule can correctly select max(own benefit, deceased spouse's benefit).
    """
    # Benefit amount each person WOULD be receiving, based purely on age vs. claim age.
    h_amt = h_pia_val * get_pia_multiplier(h_c) if h_age >= h_c else 0.0
    l_amt = l_pia_val * get_pia_multiplier(l_c) if l_age >= l_c else 0.0

    if h_alive and l_alive:
        gross = h_amt + l_amt
        if is_baseline_strategy:
            net = gross * (1 - t_base)
        else:
            base_h_amt = h_pia_base_val * get_pia_multiplier(base_h_c) if h_age >= base_h_c else 0.0
            base_l_amt = l_pia_base_val * get_pia_multiplier(base_l_c) if l_age >= base_l_c else 0.0
            base_gross = base_h_amt + base_l_amt
            base_net = base_gross * (1 - t_base)
            if gross > base_gross:
                net = base_net + (gross - base_gross) * (1 - t_gap_rate)
            else:
                net = gross * (1 - t_base)
    elif h_alive and not l_alive:
        # Lower earner deceased: higher earner keeps their own benefit
        # (survivor step-up doesn't apply since higher earner's own is already the larger amount).
        net = h_amt * (1 - t_base)
    elif (not h_alive) and l_alive:
        # SURVIVOR CASE (the bug): use the higher earner's actual claimed amount (h_amt),
        # computed independent of their alive status, not zero.
        survivor_amt = max(h_amt, l_amt)
        if is_baseline_strategy:
            net = survivor_amt * (1 - t_base)
        else:
            base_h_amt = h_pia_base_val * get_pia_multiplier(base_h_c) if h_age >= base_h_c else 0.0
            base_l_amt = l_pia_base_val * get_pia_multiplier(base_l_c) if l_age >= base_l_c else 0.0
            base_survivor_amt = max(base_h_amt, base_l_amt)
            if survivor_amt > base_survivor_amt:
                net = (base_survivor_amt * (1 - t_base)) + ((survivor_amt - base_survivor_amt) * (1 - t_gap_rate))
            else:
                net = survivor_amt * (1 - t_base)
    else:
        net = 0.0

    return net


# --- Dynamic Break-Even & Time-Series Simulation with Independent Corrected Slopes ---
def run_simulation(is_joint, h_c1, l_c1, h_c2, l_c2, single_early, single_late, age_diff, h_pia_val, l_pia_val, h_death, l_death):
    start_age = 60 if is_joint else 62
    
    if not is_joint:
        end_age = 104
        ages = list(range(start_age, end_age + 1))
        w_early, w_late = 0.0, 0.0
        chart_rows = []
        
        g_early = h_pia_val * get_pia_multiplier(early_claim)
        g_late = h_pia_val * get_pia_multiplier(late_claim)
        n_early = g_early * (1 - t_62)
        n_late = n_early + ((g_late - g_early) * (1 - t_gap))
        
        for age in ages:
            chart_rows.append({"Age": age, label_early: w_early, label_late: w_late})
            
            cut = insolvency_cut if age >= cut_age else 0.0
            cf_e = n_early * (1 - cut) if age >= early_claim else 0.0
            cf_l = n_late * (1 - cut) if age >= late_claim else 0.0
            
            for m in range(1, 13):
                w_early = w_early * (1 + monthly_rate) + cf_e
                w_late = w_late * (1 + monthly_rate) + cf_l
                    
        df_out = pd.DataFrame(chart_rows).set_index("Age")
        
        be_result = "Escape Velocity 🚀"
        w_e_test, w_l_test = 0.0, 0.0
        found_be = False
        
        for age in ages:
            cut = insolvency_cut if age >= cut_age else 0.0
            cf_e = n_early * (1 - cut) if age >= early_claim else 0.0
            cf_l = n_late * (1 - cut) if age >= late_claim else 0.0
            for m in range(1, 13):
                pe, pl = w_e_test, w_l_test
                w_e_test = w_e_test * (1 + monthly_rate) + cf_e
                w_l_test = w_l_test * (1 + monthly_rate) + cf_l
                curr_age = age + (m / 12)
                
                if not found_be and curr_age > float(late_claim):
                    if pe >= pl and w_l_test > w_e_test:
                        be_result = curr_age
                        found_be = True
                        
        return df_out, be_result

    else:
        max_lower_death_age = min(104, l_death)
        max_higher_death_age_equivalent = min(104, h_death + age_diff)
        max_sim_lower_age = max(max_lower_death_age, max_higher_death_age_equivalent)
        
        ages = list(range(start_age, max_sim_lower_age + 1))
        
        w_strat1, w_strat2 = 0.0, 0.0
        h_start_age = start_age - age_diff

        # Historical warmup loop before lower earner hits start_age (age 60)
        if h_start_age > 60:
            for h_temp in range(60, h_start_age):
                l_temp = h_temp + age_diff
                cut_t = insolvency_cut if h_temp >= cut_age else 0.0
                
                h_alive = h_temp < h_death
                l_alive = l_temp < l_death
                
                if not h_alive and not l_alive:
                    continue
                
                cf_s1_t = joint_net_cashflow(
                    h_temp, l_temp, h_alive, l_alive, h_c1, l_c1, h_pia_val, l_pia_val,
                    h_c1, l_c1, h_pia_val, l_pia_val, t_62, t_gap, is_baseline_strategy=True
                ) * (1 - cut_t)

                cf_s2_t = joint_net_cashflow(
                    h_temp, l_temp, h_alive, l_alive, h_c2, l_c2, h_pia_val, l_pia_val,
                    h_c1, l_c1, h_pia_val, l_pia_val, t_62, t_gap, is_baseline_strategy=False
                ) * (1 - cut_t)
                
                for _ in range(12):
                    w_strat1 = w_strat1 * (1 + monthly_rate) + cf_s1_t
                    w_strat2 = w_strat2 * (1 + monthly_rate) + cf_s2_t

        # Crossing detection: track WHICH strategy currently leads (state-transition based),
        # not a calendar-age gate -- a fixed gate can always be outrun by an extreme enough
        # age gap (found via stress testing: a hardcoded +1yr gate, then even a 0yr gate,
        # both eventually missed a real crossing for a big enough |age_diff|).
        # The lead as of the START of the visible window (age 60, after warmup) seeds
        # "previously_ahead" -- this correctly carries forward whichever strategy was already
        # ahead from the invisible pre-history, without ever reporting a crossing age below 60
        # (age 60 is the leftmost point on the chart, so a "crossing" the user can't see on the
        # graph would look like a bug, even though the underlying number would be correct).
        previously_ahead = "S1" if w_strat1 > w_strat2 else ("S2" if w_strat2 > w_strat1 else None)
        be_result = "Escape Velocity 🚀"
        found_be = False

        def _check_crossing(cur_age):
            nonlocal previously_ahead, be_result, found_be
            currently_ahead = "S1" if w_strat1 > w_strat2 else ("S2" if w_strat2 > w_strat1 else None)
            if not found_be and currently_ahead is not None:
                if previously_ahead is not None and currently_ahead != previously_ahead:
                    be_result = cur_age
                    found_be = True
                previously_ahead = currently_ahead

        chart_rows = []
        
        for l_age in ages:
            chart_rows.append({"Lower Earner Age": l_age, label_early: w_strat1, label_late: w_strat2})
            
            h_age = l_age - age_diff
            cut = insolvency_cut if h_age >= cut_age else 0.0
            
            h_alive = h_age < h_death
            l_alive = l_age < l_death
            
            if not h_alive and not l_alive:
                cf_s1, cf_s2 = 0.0, 0.0
            else:
                net_s1 = joint_net_cashflow(
                    h_age, l_age, h_alive, l_alive, h_c1, l_c1, h_pia_val, l_pia_val,
                    h_c1, l_c1, h_pia_val, l_pia_val, t_62, t_gap, is_baseline_strategy=True
                )
                net_s2 = joint_net_cashflow(
                    h_age, l_age, h_alive, l_alive, h_c2, l_c2, h_pia_val, l_pia_val,
                    h_c1, l_c1, h_pia_val, l_pia_val, t_62, t_gap, is_baseline_strategy=False
                )
                cf_s1 = net_s1 * (1 - cut)
                cf_s2 = net_s2 * (1 - cut)
            
            for m in range(1, 13):
                w_strat1 = w_strat1 * (1 + monthly_rate) + cf_s1
                w_strat2 = w_strat2 * (1 + monthly_rate) + cf_s2
                _check_crossing(l_age + (m / 12))
                    
        df_out = pd.DataFrame(chart_rows).set_index("Lower Earner Age")
        return df_out, be_result

df_chart, be_age = run_simulation(
    is_joint=(filing_status == "Married (Joint)"),
    h_c1=h_claim_1 if filing_status == "Married (Joint)" else 0,
    l_c1=l_claim_1 if filing_status == "Married (Joint)" else 0,
    h_c2=h_claim_2 if filing_status == "Married (Joint)" else 0,
    l_c2=l_claim_2 if filing_status == "Married (Joint)" else 0,
    single_early=early_claim if filing_status == "Single" else 0,
    single_late=late_claim if filing_status == "Single" else 0,
    age_diff=earner_age_diff,
    h_pia_val=h_pia,
    l_pia_val=l_pia,
    h_death=h_death_age,
    l_death=l_death_age
)

def format_age(val):
    if isinstance(val, str): return val
    if filing_status == "Married (Joint)":
        return f"Age {val:.1f} (Lower Earner)"
    return f"Age {val:.1f}"

st.subheader("Dynamic Break-Even Milestone")
st.metric(f"{label_early} vs {label_late}", format_age(be_age))
st.divider()

chart_x_label = "Lower Earner Age" if filing_status == "Married (Joint)" else "Age"

# --- Chart rendering (Altair, for aspect-ratio / dual-axis-label / full-legend-text control) ---
plot_df = df_chart.reset_index()
x_col = plot_df.columns[0]  # "Lower Earner Age" or "Age"
series_cols = [c for c in plot_df.columns if c != x_col]

long_df = plot_df.melt(id_vars=[x_col], value_vars=series_cols, var_name="Strategy", value_name="Cumulative Wealth ($)")

if filing_status == "Married (Joint)":
    # Show both Lower Earner Age and Higher Earner Age on each x-axis tick, computed
    # arithmetically from the numeric x value so line positions/order stay correct.
    x_axis = alt.Axis(
        title="Lower Earner Age / Higher Earner Age",
        labelExpr=f"datum.value + ' / ' + (datum.value - ({earner_age_diff}))",
        values=sorted(plot_df[x_col].unique().tolist()),  # force a tick for every year, not just min/max
    )
else:
    x_axis = alt.Axis(
        title=chart_x_label,
        values=sorted(plot_df[x_col].unique().tolist()),
    )

chart = (
    alt.Chart(long_df)
    .mark_line()
    .encode(
        x=alt.X(f"{x_col}:Q", axis=x_axis),
        y=alt.Y("Cumulative Wealth ($):Q", title="Cumulative Wealth ($)"),
        color=alt.Color(
            "Strategy:N",
            legend=alt.Legend(title=None, labelLimit=0, symbolLimit=0)  # labelLimit=0 -> no legend text truncation
        ),
    )
    .properties(width=1260, height=600)  # 30% narrower than the previous 1800
)

st.altair_chart(chart, use_container_width=False)

st.sidebar.divider()
st.sidebar.caption("© 2026 Chung-Chieh Yu. All Rights Reserved.")
st.sidebar.caption("💡 **Have questions or suggestions?** [Open an issue on GitHub](https://github.com/chungchiehyu-glitch/ss-sandbox/issues) to join the discussion.")

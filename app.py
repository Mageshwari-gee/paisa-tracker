import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, date, timedelta
import calendar
import numpy as np
import auth

st.set_page_config(page_title="Paisa Tracker 💰", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

# ── Auth gate ──────────────────────────────────────────────────────────────────
# Blocks here with a login/signup form until the visitor is authenticated.
# Everything below this line is the original app, unchanged, except that
# DATA_DIR/SETUP_FILE/BUDGET_FILE now point at this user's own folder.
CURRENT_USER = auth.require_login()

DATA_DIR    = os.path.join("data", CURRENT_USER)
os.makedirs(DATA_DIR, exist_ok=True)
SETUP_FILE  = os.path.join(DATA_DIR, "setup.csv")
BUDGET_FILE = os.path.join(DATA_DIR, "budget_rules.csv")
COLS        = ["Date","Description","Category","Amount","Payment Mode","Type","Notes"]

CATEGORIES  = ["Life Infrastructure","Lifestyle Enjoyment","Performance & Growth","Relationships & Generosity","Future Me"]
CATEGORY_TYPES = {"Life Infrastructure":"Need","Lifestyle Enjoyment":"Want","Performance & Growth":"Need","Relationships & Generosity":"Want","Future Me":"Saving"}
PAYMENT_MODES  = ["UPI","Credit Card","Debit Card","Cash","Bank Transfer"]
MONTH_NAMES    = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CAT_COLORS  = {"Life Infrastructure":"#3B82F6","Lifestyle Enjoyment":"#F59E0B","Performance & Growth":"#10B981","Relationships & Generosity":"#EC4899","Future Me":"#8B5CF6"}
TYPE_COLORS = {"Need":"#3B82F6","Want":"#F59E0B","Saving":"#10B981"}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);}
div[data-testid="metric-container"]{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:20px !important;backdrop-filter:blur(10px);}
div[data-testid="metric-container"] label{font-size:12px !important;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.5) !important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif !important;font-size:28px !important;font-weight:700;color:#e2e8f0 !important;}
section[data-testid="stSidebar"]{background:rgba(10,10,20,0.95) !important;border-right:1px solid rgba(255,255,255,0.06);}
.stButton button{background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;color:white !important;border:none !important;border-radius:10px !important;font-weight:600 !important;}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:6px 8px;margin-bottom:28px;}
.stTabs [data-baseweb="tab"]{border-radius:12px !important;color:rgba(255,255,255,0.5) !important;font-weight:500 !important;font-size:14px !important;padding:10px 22px !important;border:none !important;background:transparent !important;}
.stTabs [data-baseweb="tab"]:hover{color:rgba(255,255,255,0.85) !important;background:rgba(255,255,255,0.06) !important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(99,102,241,0.35),rgba(139,92,246,0.35)) !important;color:white !important;font-weight:600 !important;box-shadow:0 2px 12px rgba(99,102,241,0.25) !important;border:1px solid rgba(99,102,241,0.4) !important;}
.stTabs [data-baseweb="tab-highlight"]{display:none !important;}
.stTabs [data-baseweb="tab-border"]{display:none !important;}
.section-header{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#e2e8f0;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid rgba(99,102,241,0.3);}
.app-title{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;background:linear-gradient(135deg,#6366f1,#a78bfa,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.budget-alert{padding:12px 16px;border-radius:10px;margin:8px 0;font-size:14px;font-weight:500;}
.alert-danger{background:rgba(239,68,68,0.15);border-left:3px solid #ef4444;color:#fca5a5;}
.alert-warning{background:rgba(245,158,11,0.15);border-left:3px solid #f59e0b;color:#fcd34d;}
.alert-success{background:rgba(16,185,129,0.15);border-left:3px solid #10b981;color:#6ee7b7;}
/* Action icon buttons — minimal circle style */
.icon-btn {
    display:inline-flex; align-items:center; justify-content:center;
    width:30px; height:30px; border-radius:50%;
    border:none; cursor:pointer; transition:all 0.18s ease;
    font-size:14px; line-height:1; padding:0;
}
.icon-btn-edit {
    background:rgba(99,102,241,0.15);
    color:#a78bfa;
    border:1px solid rgba(99,102,241,0.3);
}
.icon-btn-edit:hover { background:rgba(99,102,241,0.3); border-color:#6366f1; }
.icon-btn-delete {
    background:rgba(239,68,68,0.12);
    color:#f87171;
    border:1px solid rgba(239,68,68,0.25);
}
.icon-btn-delete:hover { background:rgba(239,68,68,0.28); border-color:#ef4444; }
/* Keep all other streamlit buttons clean */
button[data-testid="baseButton-secondary"]{
    padding:4px 10px !important; font-size:12px !important;
    min-height:28px !important; height:28px !important;
    border-radius:8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Data helpers ───────────────────────────────────────────────────────────────
def year_file(year): return os.path.join(DATA_DIR, f"expenses_{int(year)}.csv")

def available_years():
    yrs = []
    for f in os.listdir(DATA_DIR):
        if f.startswith("expenses_") and f.endswith(".csv"):
            try: yrs.append(int(f.replace("expenses_","").replace(".csv","")))
            except: pass
    return sorted(yrs)

@st.cache_data(ttl=1)
def _load_year_cached(year, data_dir):
    # data_dir is part of the cache key (along with year) so that two users
    # requesting the same year at the same moment never share a cached frame.
    fp = os.path.join(data_dir, f"expenses_{int(year)}.csv")
    empty = pd.DataFrame(columns=COLS)
    empty["Date"]   = pd.to_datetime(empty["Date"])
    empty["Amount"] = pd.to_numeric(empty["Amount"], errors="coerce")
    if os.path.exists(fp):
        try:
            df = pd.read_csv(fp)
            if df.empty or "Date" not in df.columns:
                return empty
            df["Date"]   = pd.to_datetime(df["Date"], errors="coerce")
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
            df = df.dropna(subset=["Date"])   # drop rows where date couldn't parse
            return df
        except Exception:
            return empty
    return empty

def load_year(year):
    return _load_year_cached(year, DATA_DIR)

def save_year(df, year):
    df.to_csv(year_file(year), index=False)
    _load_year_cached.clear()

def load_all_years():
    frames = [load_year(y) for y in available_years()]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)

def delete_year_data(year):
    fp = year_file(year)
    if os.path.exists(fp): os.remove(fp)
    _load_year_cached.clear()

def delete_month_data(year, month_num):
    df = load_year(year)
    if df.empty:
        return
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    save_year(df[df["Date"].dt.month != month_num].reset_index(drop=True), year)

def load_setup():
    if os.path.exists(SETUP_FILE):
        return pd.read_csv(SETUP_FILE)
    return pd.DataFrame({"Year":[2026,2027,2028,2029,2030],"Salary":[50000,55000,60500,66550,73205],
                          "Needs":[25000,27500,30250,33275,36602],"Wants":[15000,16500,18150,19965,21961],
                          "Savings":[10000,11000,12100,13310,14641],"Weekly_Limit":[10000]*5})

def save_setup(df): df.to_csv(SETUP_FILE, index=False)

def load_budget_rules():
    if os.path.exists(BUDGET_FILE):
        return pd.read_csv(BUDGET_FILE)
    return pd.DataFrame(columns=["Year","Month","Needs_Pct","Wants_Pct","Savings_Pct"])

def save_budget_rules(df): df.to_csv(BUDGET_FILE, index=False)

def get_budget_rule(year, month):
    rules = load_budget_rules()
    if rules.empty: return 50.0, 30.0, 20.0
    if month == "All":
        yr = rules[rules["Year"]==year]
        if yr.empty: return 50.0, 30.0, 20.0
        return float(yr["Needs_Pct"].mean()), float(yr["Wants_Pct"].mean()), float(yr["Savings_Pct"].mean())
    r = rules[(rules["Year"]==year) & (rules["Month"]==month)]
    if not r.empty:
        row = r.iloc[0]
        return float(row["Needs_Pct"]), float(row["Wants_Pct"]), float(row["Savings_Pct"])
    # fall back to last saved month
    mo_idx = MONTH_NAMES.index(month)
    for i in range(mo_idx-1,-1,-1):
        prev = rules[(rules["Year"]==year) & (rules["Month"]==MONTH_NAMES[i])]
        if not prev.empty:
            row = prev.iloc[0]
            return float(row["Needs_Pct"]), float(row["Wants_Pct"]), float(row["Savings_Pct"])
    return 50.0, 30.0, 20.0

def fmt_inr(amount):
    if amount >= 1_00_00_000: return f"₹{amount/1_00_00_000:.1f}Cr"
    elif amount >= 1_00_000:  return f"₹{amount/1_00_000:.1f}L"
    elif amount >= 1000:
        s = f"{int(amount):,}"; parts = s.split(",")
        return f"₹{','.join(parts[:-1])},{parts[-1]}" if len(parts)>1 else f"₹{s}"
    return f"₹{int(amount)}"

def score_calc(df_month, salary, needs_pct=50, wants_pct=30, savings_pct=20):
    if df_month.empty or salary==0: return 5
    needs   = df_month[df_month["Type"]=="Need"]["Amount"].sum()
    wants   = df_month[df_month["Type"]=="Want"]["Amount"].sum()
    savings = df_month[df_month["Type"]=="Saving"]["Amount"].sum()
    score = 10
    if needs/salary   > needs_pct/100:   score -= min(3,(needs/salary - needs_pct/100)*10)
    if wants/salary   > wants_pct/100:   score -= min(3,(wants/salary - wants_pct/100)*10)
    if savings/salary < savings_pct/100: score -= min(3,(savings_pct/100 - savings/salary)*10)
    return max(1, min(10, round(score,1)))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="app-title">💰 Paisa Tracker</div>', unsafe_allow_html=True)
    st.caption("Your personal finance companion")
    auth.logout_button(st.sidebar)
    st.divider()
    st.markdown("### 🗕 Quick Filter")
    setup_df = load_setup()
    _now = datetime.now()
    current_year  = _now.year
    current_month = MONTH_NAMES[_now.month-1]
    years_available = sorted(set(setup_df["Year"].tolist()) | set(available_years()))
    _yr_idx = years_available.index(current_year) if current_year in years_available else len(years_available)-1

    # FIX 5: use explicit session_state keys so switching month always reacts immediately
    if "sel_year" not in st.session_state:
        st.session_state["sel_year"]  = years_available[_yr_idx]
    if "sel_month" not in st.session_state:
        st.session_state["sel_month"] = current_month

    sel_year  = st.selectbox("Year",  years_available,
                              index=years_available.index(st.session_state["sel_year"]) if st.session_state["sel_year"] in years_available else _yr_idx,
                              key="sel_year")
    sel_month = st.selectbox("Month", ["All"]+MONTH_NAMES,
                              index=(["All"]+MONTH_NAMES).index(st.session_state["sel_month"]) if st.session_state["sel_month"] in ["All"]+MONTH_NAMES else 0,
                              key="sel_month")

    st.divider()
    yr_row = setup_df[setup_df["Year"]==sel_year]
    current_salary = int(yr_row["Salary"].values[0]) if not yr_row.empty else 50000
    weekly_limit   = int(yr_row["Weekly_Limit"].values[0]) if not yr_row.empty and "Weekly_Limit" in yr_row.columns else 10000
    _np, _wp, _sp  = get_budget_rule(sel_year, sel_month)

    st.markdown(f"### 📊 Budget ({_np:.0f}-{_wp:.0f}-{_sp:.0f} Rule)")
    st.markdown(f"""
<div style="display:flex;flex-direction:column;gap:8px;margin-top:4px;">
  <div style="background:linear-gradient(135deg,rgba(99,102,241,0.18),rgba(139,92,246,0.12));border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:12px 14px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:4px;">💼 Monthly Salary</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#c4b5fd;line-height:1;">{fmt_inr(current_salary)}</div>
  </div>
  <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:12px;padding:11px 14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🏠 Needs</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#93c5fd;line-height:1;">{fmt_inr(current_salary*_np/100)}</div></div>
      <div style="background:rgba(59,130,246,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#93c5fd;">{_np:.0f}%</div>
    </div>
    <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_np}%;height:100%;background:#3b82f6;border-radius:4px;"></div></div>
  </div>
  <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);border-radius:12px;padding:11px 14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🎉 Wants</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fcd34d;line-height:1;">{fmt_inr(current_salary*_wp/100)}</div></div>
      <div style="background:rgba(245,158,11,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#fcd34d;">{_wp:.0f}%</div>
    </div>
    <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_wp}%;height:100%;background:#f59e0b;border-radius:4px;"></div></div>
  </div>
  <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:11px 14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🏦 Savings</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#6ee7b7;line-height:1;">{fmt_inr(current_salary*_sp/100)}</div></div>
      <div style="background:rgba(16,185,129,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#6ee7b7;">{_sp:.0f}%</div>
    </div>
    <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_sp}%;height:100%;background:#10b981;border-radius:4px;"></div></div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.divider()
    st.caption("📁 Data stored as year-wise CSVs")
    st.caption("Made with ❤️ for India")

# ── Filtered data (FIX 5: always re-read from session_state keys) ──────────────
def filter_data(year, month):
    d = load_year(year).copy()
    if d.empty:
        return d
    if not pd.api.types.is_datetime64_any_dtype(d["Date"]):
        d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    d = d.dropna(subset=["Date"])
    if not d.empty and month != "All":
        d = d[d["Date"].dt.month == MONTH_NAMES.index(month)+1]
    return d

filtered_df = filter_data(sel_year, sel_month)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard", "📝 Daily Tracker", "📅 Weekly Analysis",
    "📆 Monthly Analysis", "🗓️ Yearly Calendar", "⚙️ Setup"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">📊 Financial Dashboard</div>', unsafe_allow_html=True)
    if filtered_df.empty:
        st.info("No expenses found for the selected period. Add expenses in the Daily Tracker tab!")
    else:
        total_spent   = filtered_df["Amount"].sum()
        needs_spent   = filtered_df[filtered_df["Type"]=="Need"]["Amount"].sum()
        wants_spent   = filtered_df[filtered_df["Type"]=="Want"]["Amount"].sum()
        savings_spent = filtered_df[filtered_df["Type"]=="Saving"]["Amount"].sum()
        budget_needs  = current_salary * _np / 100
        budget_wants  = current_salary * _wp / 100
        budget_savings= current_salary * _sp / 100
        score = score_calc(filtered_df, current_salary, _np, _wp, _sp)

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("💸 Total Spent",  fmt_inr(total_spent),   delta=fmt_inr(current_salary-total_spent)+" left")
        k2.metric("🏠 Needs",        fmt_inr(needs_spent),   delta=fmt_inr(budget_needs-needs_spent)+" left")
        k3.metric("🎉 Wants",        fmt_inr(wants_spent),   delta=fmt_inr(budget_wants-wants_spent)+" left")
        k4.metric("🏦 Savings",      fmt_inr(savings_spent), delta=fmt_inr(budget_savings-savings_spent)+" gap", delta_color="inverse")
        k5.metric("⭐ Health Score",  f"{score}/10")
        st.divider()

        ac, _ = st.columns([2,1])
        with ac:
            if needs_spent  > budget_needs:  st.markdown(f'<div class="budget-alert alert-danger">⚠️ Needs over budget by {fmt_inr(needs_spent-budget_needs)}</div>', unsafe_allow_html=True)
            if wants_spent  > budget_wants:  st.markdown(f'<div class="budget-alert alert-danger">⚠️ Wants over budget by {fmt_inr(wants_spent-budget_wants)}</div>', unsafe_allow_html=True)
            if savings_spent< budget_savings:st.markdown(f'<div class="budget-alert alert-warning">💡 Invest {fmt_inr(budget_savings-savings_spent)} more to hit savings goal</div>', unsafe_allow_html=True)
            if score >= 7:                   st.markdown(f'<div class="budget-alert alert-success">✅ Great financial health! Keep it up.</div>', unsafe_allow_html=True)
        st.divider()

        c1,c2,c3 = st.columns([1.2,1.2,1])
        with c1:
            st.markdown("**Spending by Category**")
            cat_sum = filtered_df.groupby("Category")["Amount"].sum().reset_index()
            fig = px.pie(cat_sum, values="Amount", names="Category", color="Category",
                         color_discrete_map=CAT_COLORS, hole=0.45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="white", legend_font_size=11, height=320,
                              margin=dict(t=10,b=10,l=10,r=10))
            fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown(f"**{_np:.0f}-{_wp:.0f}-{_sp:.0f} Budget vs Actual**")
            bdf = pd.DataFrame({"Type":["Needs","Wants","Savings"],
                                "Budget":[budget_needs,budget_wants,budget_savings],
                                "Actual":[needs_spent,wants_spent,savings_spent]})
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Budget",x=bdf["Type"],y=bdf["Budget"],marker_color="rgba(99,102,241,0.4)",marker_line_width=0))
            fig2.add_trace(go.Bar(name="Actual", x=bdf["Type"],y=bdf["Actual"], marker_color=["#3B82F6","#F59E0B","#10B981"],marker_line_width=0))
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",barmode="group",height=320,
                               legend=dict(orientation="h",y=1.1),margin=dict(t=30,b=10,l=10,r=10),
                               yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig2, use_container_width=True)
        with c3:
            st.markdown("**Payment Mode Split**")
            pm = filtered_df.groupby("Payment Mode")["Amount"].sum().reset_index()
            pm_col = {"UPI":"#6366f1","Credit Card":"#ec4899","Debit Card":"#3b82f6","Cash":"#f59e0b","Bank Transfer":"#10b981"}
            fig3 = px.pie(pm, values="Amount", names="Payment Mode", color="Payment Mode",
                          color_discrete_map=pm_col, hole=0.45)
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                               font_color="white",legend_font_size=10,height=320,margin=dict(t=10,b=10,l=10,r=10))
            fig3.update_traces(textposition="inside",textinfo="percent",textfont_size=10)
            st.plotly_chart(fig3, use_container_width=True)
        st.divider()

        c4,c5 = st.columns([2,1])
        with c4:
            st.markdown("**Daily Spending Trend**")
            daily = filtered_df.groupby(filtered_df["Date"].dt.date)["Amount"].sum().reset_index()
            daily.columns = ["Date","Amount"]
            daily["Date"] = pd.to_datetime(daily["Date"])
            daily["7d_avg"] = daily["Amount"].rolling(7,min_periods=1).mean()
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=daily["Date"],y=daily["Amount"],name="Daily",marker_color="rgba(99,102,241,0.5)",marker_line_width=0))
            fig4.add_trace(go.Scatter(x=daily["Date"],y=daily["7d_avg"],name="7-day avg",line=dict(color="#ec4899",width=2.5)))
            fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=280,
                               legend=dict(orientation="h",y=1.1),margin=dict(t=30,b=10,l=10,r=10),
                               xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig4, use_container_width=True)
        with c5:
            st.markdown("**Top 5 Categories**")
            top5 = filtered_df.groupby("Category")["Amount"].sum().nlargest(5).reset_index()
            fig5 = px.bar(top5,x="Amount",y="Category",orientation="h",color="Category",color_discrete_map=CAT_COLORS)
            fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=280,
                               showlegend=False,margin=dict(t=10,b=10,l=10,r=10),
                               xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig5, use_container_width=True)
        st.divider()
        st.markdown("**🕐 Recent Transactions**")
        recent = filtered_df.sort_values("Date",ascending=False).head(10).copy()
        recent["Date"] = recent["Date"].dt.strftime("%d %b %Y")
        recent["Amount"] = recent["Amount"].apply(fmt_inr)
        st.dataframe(recent[["Date","Description","Category","Amount","Payment Mode","Type","Notes"]],
                     use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 — DAILY TRACKER
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">📝 Daily Expense Tracker</div>', unsafe_allow_html=True)

    with st.expander("➕ Add New Expense", expanded=True):
        with st.form("add_expense_form", clear_on_submit=True):
            fc1,fc2,fc3 = st.columns(3)
            with fc1:
                exp_date   = st.date_input("Date", value=date.today())
                exp_amount = st.number_input("Amount (₹)", min_value=0, step=10, value=0)
            with fc2:
                exp_desc     = st.text_input("Description", placeholder="e.g. Swiggy lunch, Uber ride")
                exp_category = st.selectbox("Category", CATEGORIES)
            with fc3:
                exp_payment = st.selectbox("Payment Mode", PAYMENT_MODES)
                exp_type    = st.selectbox("Type", ["Need","Want","Saving"],
                                           index=["Need","Want","Saving"].index(CATEGORY_TYPES.get(exp_category,"Want")))
                exp_notes   = st.text_input("Notes (optional)", placeholder="Optional remark")
            submitted = st.form_submit_button("💾 Add Expense", use_container_width=True)
            if submitted:
                if exp_amount <= 0:       st.error("Please enter a valid amount!")
                elif not exp_desc.strip(): st.error("Please enter a description!")
                else:
                    df = load_year(exp_date.year)
                    df = pd.concat([df, pd.DataFrame([{"Date":pd.Timestamp(exp_date),
                        "Description":exp_desc.strip(),"Category":exp_category,"Amount":exp_amount,
                        "Payment Mode":exp_payment,"Type":exp_type,"Notes":exp_notes.strip()}])], ignore_index=True)
                    save_year(df, exp_date.year)
                    st.success(f"✅ Added: {exp_desc} — {fmt_inr(exp_amount)}")
                    st.rerun()

    st.divider()
    st.markdown("**🔍 Filter & Search**")
    f1,f2,f3,f4 = st.columns(4)
    with f1: filter_cat  = st.multiselect("Category",     CATEGORIES,              default=[])
    with f2: filter_pay  = st.multiselect("Payment Mode", PAYMENT_MODES,           default=[])
    with f3: filter_type = st.multiselect("Type",         ["Need","Want","Saving"], default=[])
    with f4: search_text = st.text_input("Search Description", placeholder="Search...")

    # FIX 4: load full year, stamp _file_idx BEFORE any filtering, then apply ALL filters
    _full_yr = load_year(sel_year).copy()
    _full_yr["_file_idx"] = _full_yr.index

    display_df = _full_yr.copy()
    # FIX 4+5: month filter applied here consistently
    if not pd.api.types.is_datetime64_any_dtype(display_df["Date"]):
        display_df["Date"] = pd.to_datetime(display_df["Date"], errors="coerce")
    display_df = display_df.dropna(subset=["Date"])
    if sel_month != "All" and not display_df.empty:
        display_df = display_df[display_df["Date"].dt.month == MONTH_NAMES.index(sel_month)+1]
    # Category / payment / type filters — FIX 4: these now work for "All" month too
    if filter_cat:  display_df = display_df[display_df["Category"].isin(filter_cat)]
    if filter_pay:  display_df = display_df[display_df["Payment Mode"].isin(filter_pay)]
    if filter_type: display_df = display_df[display_df["Type"].isin(filter_type)]
    if search_text: display_df = display_df[display_df["Description"].str.contains(search_text, case=False, na=False)]
    display_df = display_df.sort_values("Date", ascending=False)  # preserve _file_idx

    # Pagination controls
    pg_col1, pg_col2, pg_col3 = st.columns([2,1,1])
    with pg_col1:
        st.markdown(f"**{len(display_df)} transactions · Total: {fmt_inr(display_df['Amount'].sum())}**")
    with pg_col2:
        page_size_opt = st.selectbox("Rows per page", [10,25,50,100,"All"], index=0, key="page_size")
    with pg_col3:
        if page_size_opt != "All" and len(display_df) > 0:
            total_pages   = max(1, -(-len(display_df) // int(page_size_opt)))
            if "tracker_page" not in st.session_state: st.session_state["tracker_page"] = 1
            if st.session_state["tracker_page"] > total_pages: st.session_state["tracker_page"] = 1
            current_page  = st.session_state["tracker_page"]
            page_start    = (current_page-1)*int(page_size_opt)
            page_df       = display_df.iloc[page_start : page_start+int(page_size_opt)]
            st.markdown(f"<div style='padding:8px 0;font-size:13px;color:rgba(255,255,255,0.5);'>"
                        f"Page {current_page}/{total_pages}</div>", unsafe_allow_html=True)
        else:
            page_df = display_df
            total_pages, current_page = 1, 1

    # Edit panel — appears above the table
    if "edit_row" in st.session_state:
        _efi   = st.session_state["edit_row"]
        _eyear = st.session_state.get("edit_year", sel_year)
        _fy    = load_year(_eyear)
        if _efi < len(_fy):
            er = _fy.iloc[_efi]
            st.markdown(
                f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08));'
                f'border:1.5px solid rgba(99,102,241,0.4);border-radius:16px;padding:20px 24px;margin:12px 0 16px 0;">'
                f'<div style="font-family:Space Grotesk,sans-serif;font-size:15px;font-weight:700;'
                f'color:#a78bfa;margin-bottom:14px;">✏️ Editing — {er["Description"]}</div>',
                unsafe_allow_html=True)
            with st.form("edit_form"):
                ef1,ef2,ef3,ef4 = st.columns([1.2,2,1.5,1.5])
                with ef1:
                    new_date   = st.date_input("Date",        value=pd.Timestamp(er["Date"]).date())
                    new_amount = st.number_input("Amount (₹)", min_value=0, step=10, value=int(er["Amount"]))
                with ef2:
                    new_desc = st.text_input("Description", value=str(er["Description"]))
                    new_cat  = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(er["Category"]) if er["Category"] in CATEGORIES else 0)
                with ef3:
                    new_pay  = st.selectbox("Payment Mode", PAYMENT_MODES, index=PAYMENT_MODES.index(er["Payment Mode"]) if er["Payment Mode"] in PAYMENT_MODES else 0)
                    new_type = st.selectbox("Type", ["Need","Want","Saving"], index=["Need","Want","Saving"].index(er["Type"]) if er["Type"] in ["Need","Want","Saving"] else 0)
                with ef4:
                    new_notes = st.text_input("Notes", value=str(er["Notes"]) if pd.notna(er["Notes"]) else "")
                    st.markdown(" ")
                sb1,sb2 = st.columns(2)
                save_edit   = sb1.form_submit_button("💾 Save Changes", use_container_width=True)
                cancel_edit = sb2.form_submit_button("✖ Cancel",        use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if save_edit:
                _fy.at[_efi,"Date"]         = pd.Timestamp(new_date)
                _fy.at[_efi,"Description"]  = new_desc.strip()
                _fy.at[_efi,"Category"]     = new_cat
                _fy.at[_efi,"Amount"]       = new_amount
                _fy.at[_efi,"Payment Mode"] = new_pay
                _fy.at[_efi,"Type"]         = new_type
                _fy.at[_efi,"Notes"]        = new_notes.strip()
                save_year(_fy, _eyear)
                del st.session_state["edit_row"]
                st.success("✅ Transaction updated!")
                st.rerun()
            if cancel_edit:
                del st.session_state["edit_row"]
                st.rerun()

    # ── Modern fixed-height dataframe table ──────────────────────────────────────
    if page_df.empty:
        st.info("No transactions found.")
    else:
        # Build display copy with colored Type column using emoji badges
        tbl = page_df.copy()
        tbl["Date"]  = pd.to_datetime(tbl["Date"]).dt.strftime("%d %b %Y")
        tbl["₹ Amount"] = tbl["Amount"].apply(fmt_inr)
        # Type badge: colored circle + label
        type_badge = {"Need": "🔵 Need", "Want": "🟡 Want", "Saving": "🟢 Saving"}
        tbl["Type"] = tbl["Type"].apply(lambda t: type_badge.get(t, t))
        tbl["Notes"] = tbl["Notes"].fillna("").astype(str).replace("nan","")
        tbl["#"] = tbl["_file_idx"].astype(int)

        show_cols = ["#","Date","Description","Category","₹ Amount","Payment Mode","Type","Notes"]

        st.dataframe(
            tbl[show_cols],
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "#":            st.column_config.NumberColumn("#",             width=45),
                "Date":         st.column_config.TextColumn("Date",           width=105),
                "Description":  st.column_config.TextColumn("Description",    width=180),
                "Category":     st.column_config.TextColumn("Category",       width=165),
                "₹ Amount":     st.column_config.TextColumn("Amount",         width=90),
                "Payment Mode": st.column_config.TextColumn("Payment Mode",   width=120),
                "Type":         st.column_config.TextColumn("Type",           width=105),
                "Notes":        st.column_config.TextColumn("Notes",          width=140),
            }
        )

        # ── Row selector + Edit / Delete ──────────────────────────────────────
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        sel_c1, sel_c2, sel_c3 = st.columns([2.2, 0.9, 0.9])
        with sel_c1:
            row_options = {
                f"#{int(r['_file_idx'])}  {str(r['Description'])[:30]}  ·  {fmt_inr(r['Amount'])}": int(r["_file_idx"])
                for _, r in page_df.iterrows()
            }
            sel_label = st.selectbox(
                "Select row", ["— select a row to edit or delete —"] + list(row_options.keys()),
                key="row_selector", label_visibility="collapsed"
            )
            sel_fidx = row_options.get(sel_label)

        with sel_c2:
            if st.button("✎  Edit", key="tbl_edit_btn", use_container_width=True,
                         disabled=(sel_fidx is None)):
                st.session_state["edit_row"]  = sel_fidx
                st.session_state["edit_year"] = sel_year
                st.session_state.pop("confirm_del_idx", None)
                st.rerun()

        with sel_c3:
            if st.button("⌫  Delete", key="tbl_del_btn", use_container_width=True,
                         disabled=(sel_fidx is None)):
                st.session_state["confirm_del_idx"]  = sel_fidx
                st.session_state["confirm_del_year"] = sel_year
                st.session_state.pop("edit_row", None)
                st.rerun()

        # Delete confirmation
        if "confirm_del_idx" in st.session_state:
            _cdfi  = st.session_state["confirm_del_idx"]
            _match = page_df[page_df["_file_idx"] == _cdfi]
            if not _match.empty:
                _crow = _match.iloc[0]
                dc = st.columns([3.5, 1, 1])
                dc[0].markdown(
                    f"<div style='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);"
                    f"border-radius:10px;padding:9px 14px;font-size:13px;color:#fca5a5;margin-top:6px;'>"
                    f"⚠️ Delete <b>{_crow['Description']}</b> ({fmt_inr(_crow['Amount'])})? Cannot be undone.</div>",
                    unsafe_allow_html=True)
                if dc[1].button("✅ Yes", key="cy_confirm", use_container_width=True):
                    _fy2 = load_year(sel_year)
                    _fy2 = _fy2.drop(index=_cdfi).reset_index(drop=True)
                    save_year(_fy2, sel_year)
                    st.session_state.pop("confirm_del_idx", None)
                    st.session_state.pop("confirm_del_year", None)
                    st.session_state.pop("row_selector", None)
                    st.success(f"Deleted: {_crow['Description']}")
                    st.rerun()
                if dc[2].button("✖ No", key="cn_confirm", use_container_width=True):
                    st.session_state.pop("confirm_del_idx", None)
                    st.session_state.pop("confirm_del_year", None)
                    st.rerun()

        # Pagination footer
        if page_size_opt != "All" and total_pages > 1:
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            pf1,pf2,pf3,pf4,pf5 = st.columns([1,1,2,1,1])
            if pf1.button("⏮ First", use_container_width=True, key="pg_first"): st.session_state["tracker_page"]=1; st.rerun()
            if pf2.button("◀ Prev",  use_container_width=True, key="pg_prev"):  st.session_state["tracker_page"]=max(1,current_page-1); st.rerun()
            pf3.markdown(f"<div style='text-align:center;padding:8px;font-size:13px;color:rgba(255,255,255,0.6);'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
            if pf4.button("Next ▶",  use_container_width=True, key="pg_next"):  st.session_state["tracker_page"]=min(total_pages,current_page+1); st.rerun()
            if pf5.button("Last ⏭",  use_container_width=True, key="pg_last"):  st.session_state["tracker_page"]=total_pages; st.rerun()

    st.divider()
    _ecols = [c for c in display_df.columns if c != "_file_idx"]
    st.download_button("📥 Export to CSV", data=display_df[_ecols].to_csv(index=False),
                       file_name=f"expenses_{sel_year}_{sel_month}.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════
# TAB 3 — WEEKLY ANALYSIS
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">📅 Weekly Analysis</div>', unsafe_allow_html=True)
    if filtered_df.empty:
        st.info("No data for selected period.")
    else:
        df_w = filtered_df.copy()
        df_w["Date"] = pd.to_datetime(df_w["Date"], errors="coerce")
        df_w = df_w.dropna(subset=["Date"])
        if df_w.empty:
            st.info("No valid date data for this period.")
            st.stop()
        df_w["Week_Start"] = df_w["Date"].apply(lambda x: x - timedelta(days=x.weekday()))
        wt = df_w.groupby("Week_Start")["Amount"].sum().reset_index()
        wt.columns = ["Week_Start","Total"]
        wt["Week_Label"] = wt["Week_Start"].dt.strftime("W/S %d %b")
        wt["Over"] = wt["Total"] > weekly_limit
        wt["Ratio"] = (wt["Total"]/weekly_limit*100).round(1)

        w1,w2,w3,w4 = st.columns(4)
        w1.metric("Total Weeks", len(wt))
        w2.metric("Avg Weekly Spend", fmt_inr(wt["Total"].mean()))
        w3.metric("Weeks Over Limit", int(wt["Over"].sum()))
        w4.metric("Weekly Limit", fmt_inr(weekly_limit))
        st.divider()

        colors = ["#EF4444" if o else "#6366f1" for o in wt["Over"]]
        fig_w = go.Figure()
        fig_w.add_trace(go.Bar(x=wt["Week_Label"],y=wt["Total"],marker_color=colors,marker_line_width=0,
                               name="Weekly Spend",text=wt["Total"].apply(fmt_inr),textposition="outside",textfont=dict(color="white",size=11)))
        fig_w.add_hline(y=weekly_limit,line_dash="dash",line_color="#F59E0B",
                        annotation_text=f"Limit: {fmt_inr(weekly_limit)}",annotation_font_color="#F59E0B")
        fig_w.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=380,
                            margin=dict(t=40,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
        st.plotly_chart(fig_w, use_container_width=True)
        st.divider()

        wc1,wc2 = st.columns(2)
        with wc1:
            st.markdown("**Weekly Spending by Category**")
            wcat = df_w.groupby(["Week_Start","Category"])["Amount"].sum().reset_index()
            wcat["Week_Label"] = wcat["Week_Start"].dt.strftime("W/S %d %b")
            fig_ws = px.bar(wcat,x="Week_Label",y="Amount",color="Category",color_discrete_map=CAT_COLORS,barmode="stack")
            fig_ws.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
                                 legend_font_size=10,margin=dict(t=10,b=10,l=10,r=10),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_ws, use_container_width=True)
        with wc2:
            st.markdown("**Weekly Limit Performance (%)**")
            fig_wr = go.Figure()
            r_colors = ["#EF4444" if r>100 else "#F59E0B" if r>70 else "#10B981" for r in wt["Ratio"]]
            fig_wr.add_trace(go.Bar(x=wt["Week_Label"],y=wt["Ratio"],marker_color=r_colors,marker_line_width=0,
                                    text=[f"{r}%" for r in wt["Ratio"]],textposition="outside",textfont=dict(color="white",size=10)))
            fig_wr.add_hline(y=100,line_dash="dash",line_color="#F59E0B")
            fig_wr.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
                                 yaxis_title="% of Limit",margin=dict(t=10,b=10,l=10,r=10),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_wr, use_container_width=True)

        st.markdown("**Weekly Summary Table**")
        disp_w = wt.copy()
        disp_w["Total"]  = disp_w["Total"].apply(fmt_inr)
        disp_w["Status"] = disp_w["Over"].apply(lambda x: "🔴 Over" if x else "🟢 OK")
        disp_w["Ratio"]  = disp_w["Ratio"].apply(lambda x: f"{x}%")
        st.dataframe(disp_w[["Week_Label","Total","Ratio","Status"]].rename(columns={"Week_Label":"Week","Total":"Spent","Ratio":"% of Limit"}),
                     use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4 — MONTHLY ANALYSIS
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📆 Monthly Analysis</div>', unsafe_allow_html=True)
    year_df = filter_data(sel_year, "All")
    if year_df.empty:
        st.info("No data for selected year.")
    else:
        year_df["Date"] = pd.to_datetime(year_df["Date"], errors="coerce")
        year_df = year_df.dropna(subset=["Date"])
        if year_df.empty:
            st.info("No valid date data for this year.")
            st.stop()
        year_df["Month_Num"]  = year_df["Date"].dt.month
        year_df["Month_Name"] = year_df["Date"].dt.strftime("%b")
        monthly_total = year_df.groupby(["Month_Num","Month_Name"])["Amount"].sum().reset_index().sort_values("Month_Num")
        monthly_type  = year_df.groupby(["Month_Num","Month_Name","Type"])["Amount"].sum().reset_index().sort_values("Month_Num")

        monthly_scores = []
        for mn in monthly_total["Month_Num"].tolist():
            m_df = year_df[year_df["Month_Num"]==mn]
            mn_name = MONTH_NAMES[mn-1]
            mnp,mwp,msp = get_budget_rule(sel_year, mn_name)
            monthly_scores.append(score_calc(m_df, current_salary, mnp, mwp, msp))
        monthly_total["Score"] = monthly_scores

        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Highest Month", monthly_total.loc[monthly_total["Amount"].idxmax(),"Month_Name"], fmt_inr(monthly_total["Amount"].max()))
        m2.metric("Lowest Month",  monthly_total.loc[monthly_total["Amount"].idxmin(),"Month_Name"], fmt_inr(monthly_total["Amount"].min()))
        m3.metric("Avg Monthly Spend", fmt_inr(monthly_total["Amount"].mean()))
        m4.metric("Total Year Spend",  fmt_inr(year_df["Amount"].sum()))
        st.divider()

        mc1,mc2 = st.columns(2)
        with mc1:
            st.markdown("**Monthly Spending Trend**")
            fig_mt = go.Figure()
            fig_mt.add_trace(go.Bar(x=monthly_total["Month_Name"],y=monthly_total["Amount"],
                                    marker_color="rgba(99,102,241,0.7)",name="Spent",marker_line_width=0))
            fig_mt.add_hline(y=current_salary,line_dash="dot",line_color="#10b981",
                             annotation_text="Salary",annotation_font_color="#10b981")
            fig_mt.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
                                 margin=dict(t=20,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                 yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_mt, use_container_width=True)
        with mc2:
            st.markdown("**Need / Want / Saving by Month**")
            fig_mtype = px.bar(monthly_type,x="Month_Name",y="Amount",color="Type",
                               color_discrete_map=TYPE_COLORS,barmode="stack")
            fig_mtype.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
                                    margin=dict(t=20,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_mtype, use_container_width=True)

        st.divider()
        mc3,mc4 = st.columns(2)
        with mc3:
            st.markdown("**Monthly Health Score**")
            sc_colors = ["#10B981" if s>=7 else "#F59E0B" if s>=5 else "#EF4444" for s in monthly_total["Score"]]
            fig_sc = go.Figure(go.Bar(x=monthly_total["Month_Name"],y=monthly_total["Score"],
                                      marker_color=sc_colors,marker_line_width=0,
                                      text=monthly_total["Score"],textposition="outside",textfont=dict(color="white",size=11)))
            fig_sc.add_hline(y=7,line_dash="dash",line_color="#10B981",annotation_text="Good (7+)")
            fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",
                                 height=280,yaxis_range=[0,11],margin=dict(t=20,b=10,l=10,r=10),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_sc, use_container_width=True)

        # FIX 3: Replace heatmap with Top-5 Spending Days of Month chart
        with mc4:
            st.markdown("**Top Spending Days (Day of Month)**")
            year_df["Day"] = year_df["Date"].dt.day
            day_spend = year_df.groupby("Day")["Amount"].sum().reset_index().sort_values("Amount", ascending=False).head(10)
            fig_days = px.bar(day_spend, x="Day", y="Amount",
                              color="Amount", color_continuous_scale="Purples",
                              text=day_spend["Amount"].apply(fmt_inr))
            fig_days.update_traces(textposition="outside", textfont=dict(color="white", size=10))
            fig_days.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="white", height=280, showlegend=False,
                                   coloraxis_showscale=False,
                                   xaxis=dict(title="Day of Month", gridcolor="rgba(255,255,255,0.05)", dtick=1),
                                   yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                   margin=dict(t=20,b=10,l=10,r=10))
            st.plotly_chart(fig_days, use_container_width=True)

        st.divider()
        st.markdown("**Payment Mode Usage by Month**")
        pm_month = year_df.groupby(["Month_Name","Payment Mode"])["Amount"].sum().reset_index()
        month_order_map = {m:i for i,m in enumerate(MONTH_NAMES)}
        pm_month = pm_month.sort_values("Month_Name", key=lambda x: x.map(month_order_map))
        pm_colors_map = {"UPI":"#6366f1","Credit Card":"#ec4899","Debit Card":"#3b82f6","Cash":"#f59e0b","Bank Transfer":"#10b981"}

        # Keep raw amounts pivot (for hover tooltip) and pct pivot (for bar height)
        pm_raw   = pm_month.pivot_table(index="Month_Name", columns="Payment Mode", values="Amount", fill_value=0)
        pm_raw   = pm_raw.reindex([m for m in MONTH_NAMES if m in pm_raw.index])
        pm_pivot = pm_raw.div(pm_raw.sum(axis=1), axis=0) * 100   # % share

        fig_pmm = go.Figure()
        for pm, color in pm_colors_map.items():
            if pm in pm_pivot.columns:
                raw_vals = pm_raw[pm] if pm in pm_raw.columns else [0]*len(pm_pivot)
                fig_pmm.add_trace(go.Bar(
                    name=pm,
                    x=pm_pivot.index,
                    y=pm_pivot[pm].round(1),
                    marker_color=color,
                    marker_line_width=0,
                    # Show % label inside bar only if segment wide enough
                    text=pm_pivot[pm].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""),
                    textposition="inside",
                    textfont=dict(color="white", size=10, family="DM Sans"),
                    # Pass actual ₹ amounts as custom data for the tooltip
                    customdata=list(raw_vals),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Payment Mode: <b>" + pm + "</b><br>"
                        "Amount: <b>₹%{customdata:,.0f}</b><br>"
                        "Share: %{y:.1f}%"
                        "<extra></extra>"
                    )
                ))
        fig_pmm.update_layout(
            barmode="stack",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="white", height=260,
            hoverlabel=dict(bgcolor="#1e1e2e", font_size=13, font_family="DM Sans",
                            bordercolor="rgba(255,255,255,0.15)"),
            legend=dict(orientation="h", y=-0.22, x=0, font_size=11,
                        bgcolor="rgba(0,0,0,0)", borderwidth=0),
            margin=dict(t=10, b=60, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=11)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%", range=[0,100],
                       tickfont=dict(size=10))
        )
        st.plotly_chart(fig_pmm, use_container_width=True)

        st.markdown("**Monthly Summary Table**")
        mt2 = monthly_total.copy()
        mt2["Spent"]       = mt2["Amount"].apply(fmt_inr)
        mt2["Health Score"]= mt2["Score"].apply(lambda s: f"{'⭐'*int(s//2)} {s}/10")
        st.dataframe(mt2[["Month_Name","Spent","Health Score"]].rename(columns={"Month_Name":"Month"}),
                     use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 5 — YEARLY CALENDAR
# ══════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">🗓️ Yearly Calendar View</div>', unsafe_allow_html=True)
    year_df2 = filter_data(sel_year, "All")
    if year_df2.empty:
        st.info("No data for selected year.")
    else:
        st.markdown("**📅 Monthly Spending Bars**")
        daily_spend = year_df2.groupby(year_df2["Date"].dt.date)["Amount"].sum()
        month_cols  = st.columns(4)
        for mi, month_idx in enumerate(range(1,13)):
            col = month_cols[mi%4]
            with col:
                days_in_month = calendar.monthrange(sel_year, month_idx)[1]
                month_dates   = [date(sel_year, month_idx, d) for d in range(1, days_in_month+1)]
                month_amounts = [daily_spend.get(d, 0) for d in month_dates]
                total_month   = sum(month_amounts)
                st.markdown(f"**{MONTH_NAMES[month_idx-1]}** — {fmt_inr(total_month)}")
                if total_month > 0:
                    fig_m = go.Figure(go.Bar(
                        x=list(range(1,days_in_month+1)), y=month_amounts, marker_line_width=0,
                        marker_color=["#EF4444" if a>current_salary/20 else "#F59E0B" if a>current_salary/30 else "#6366f1" if a>0 else "#1f2937" for a in month_amounts]))
                    fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                        font_color="white",height=100,showlegend=False,
                                        margin=dict(t=0,b=0,l=0,r=0),
                                        xaxis=dict(showgrid=False,showticklabels=False),
                                        yaxis=dict(showgrid=False,showticklabels=False))
                    st.plotly_chart(fig_m, use_container_width=True, key=f"mb_{month_idx}")
                else:
                    st.caption("No data")

        st.divider()
        yc1,yc2 = st.columns(2)
        with yc1:
            monthly_agg = year_df2.groupby(year_df2["Date"].dt.month)["Amount"].sum().reset_index()
            monthly_agg.columns = ["Month_Num","Amount"]
            monthly_agg["Month"] = monthly_agg["Month_Num"].apply(lambda x: MONTH_NAMES[x-1])
            fig_yl = go.Figure()
            fig_yl.add_trace(go.Scatter(x=monthly_agg["Month"],y=monthly_agg["Amount"],
                                        mode="lines+markers+text",line=dict(color="#6366f1",width=3),
                                        marker=dict(size=8,color="#a78bfa"),
                                        text=monthly_agg["Amount"].apply(fmt_inr),
                                        textposition="top center",textfont=dict(color="white",size=10)))
            fig_yl.add_hline(y=current_salary,line_dash="dot",line_color="#10b981",annotation_text="Monthly Salary")
            fig_yl.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                 font_color="white",height=300,title="Monthly Spend vs Salary",
                                 margin=dict(t=30,b=10,l=10,r=10),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_yl, use_container_width=True)
        with yc2:
            cum = year_df2.sort_values("Date").groupby("Date")["Amount"].sum().cumsum().reset_index()
            fig_cum = go.Figure(go.Scatter(x=cum["Date"],y=cum["Amount"],mode="lines",fill="tozeroy",
                                           line=dict(color="#8b5cf6",width=2),fillcolor="rgba(139,92,246,0.15)"))
            fig_cum.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                  font_color="white",height=300,title="Cumulative Annual Spending",
                                  margin=dict(t=30,b=10,l=10,r=10),
                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_cum, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 6 — SETUP
# ══════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">⚙️ Setup & Configuration</div>', unsafe_allow_html=True)
    setup_df  = load_setup()
    rules_df  = load_budget_rules()

    st.markdown("### 🗓️ Monthly Budget Rules")
    st.markdown('<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:14px;padding:16px 20px;margin-bottom:20px;"><span style="font-family:\'Space Grotesk\',sans-serif;font-size:14px;font-weight:600;color:#a78bfa;">💡 How it works</span><br><span style="font-size:13px;color:rgba(255,255,255,0.55);line-height:1.7;">Each <b>Year + Month</b> can have its own budget rule. New months <b>auto-inherit</b> the last saved rule. The <b>Yearly View</b> shows a weighted blend.</span></div>', unsafe_allow_html=True)

    rb1,rb2,rb3 = st.columns([1,1,2])
    with rb1: rule_year  = st.selectbox("Year",  sorted(setup_df["Year"].tolist()), key="rule_yr")
    with rb2: rule_month = st.selectbox("Month", MONTH_NAMES, key="rule_mo", index=datetime.now().month-1)

    def get_last_rule_local(year, month_name):
        if rules_df.empty: return 50.0,30.0,20.0
        mo_idx = MONTH_NAMES.index(month_name)
        for i in range(mo_idx-1,-1,-1):
            prev = rules_df[(rules_df["Year"]==year)&(rules_df["Month"]==MONTH_NAMES[i])]
            if not prev.empty:
                r = prev.iloc[0]; return float(r["Needs_Pct"]),float(r["Wants_Pct"]),float(r["Savings_Pct"])
        for y in sorted(rules_df["Year"].unique(),reverse=True):
            if y < year:
                yr_r = rules_df[rules_df["Year"]==y]
                if not yr_r.empty: r=yr_r.iloc[-1]; return float(r["Needs_Pct"]),float(r["Wants_Pct"]),float(r["Savings_Pct"])
        return 50.0,30.0,20.0

    existing_rule = rules_df[(rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month)] if not rules_df.empty else pd.DataFrame()
    if not existing_rule.empty:
        r0=existing_rule.iloc[0]; pre_n,pre_w,pre_s=float(r0["Needs_Pct"]),float(r0["Wants_Pct"]),float(r0["Savings_Pct"]); rule_exists=True
    else:
        pre_n,pre_w,pre_s=get_last_rule_local(rule_year,rule_month); rule_exists=False

    with rb3:
        if rule_exists: st.markdown(f'<div class="budget-alert alert-success" style="margin-top:28px;">✅ Rule saved for {rule_month} {rule_year}: {pre_n:.0f}-{pre_w:.0f}-{pre_s:.0f}</div>', unsafe_allow_html=True)
        else:           st.markdown(f'<div class="budget-alert alert-warning" style="margin-top:28px;">⚡ No rule for {rule_month} {rule_year} — pre-filled from last saved rule</div>', unsafe_allow_html=True)

    sl_col,prev_col = st.columns([1.5,1])
    with sl_col:
        e_needs   = st.slider("🏠 Needs %",  10,80,int(pre_n),5,key="e_needs")
        e_wants   = st.slider("🎉 Wants %",   5,70,int(pre_w),5,key="e_wants")
        e_savings = max(0,100-e_needs-e_wants)
        if e_needs+e_wants<=100: st.markdown(f'<div class="budget-alert alert-success">✅ Valid — Savings auto-set to <b>{e_savings}%</b> · Total=100%</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="budget-alert alert-danger">⚠️ Needs+Wants={e_needs+e_wants}% — exceeds 100%</div>', unsafe_allow_html=True)
        bt1,bt2 = st.columns(2)
        with bt1:
            if st.button(f"💾 Save rule for {rule_month} {rule_year}", use_container_width=True):
                if e_needs+e_wants>100: st.error("Fix % split first")
                else:
                    new_rule = pd.DataFrame([{"Year":rule_year,"Month":rule_month,"Needs_Pct":e_needs,"Wants_Pct":e_wants,"Savings_Pct":e_savings}])
                    upd = rules_df[~((rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month))] if not rules_df.empty else pd.DataFrame(columns=["Year","Month","Needs_Pct","Wants_Pct","Savings_Pct"])
                    save_budget_rules(pd.concat([upd,new_rule],ignore_index=True))
                    st.success(f"✅ Saved {rule_month} {rule_year}: {e_needs}-{e_wants}-{e_savings}"); st.rerun()
        with bt2:
            if rule_exists and st.button(f"🗑️ Delete rule for {rule_month} {rule_year}", use_container_width=True):
                save_budget_rules(rules_df[~((rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month))])
                st.success("Rule deleted"); st.rerun()

    with prev_col:
        yr_sal = int(setup_df[setup_df["Year"]==rule_year]["Salary"].values[0]) if not setup_df[setup_df["Year"]==rule_year].empty else 50000
        fig_pv = go.Figure(go.Pie(labels=[f"Needs {e_needs}%",f"Wants {e_wants}%",f"Savings {e_savings}%"],
                                   values=[max(yr_sal*e_needs/100,1),max(yr_sal*e_wants/100,1),max(yr_sal*e_savings/100,1)],
                                   hole=0.55,marker_colors=["#3B82F6","#F59E0B","#10B981"],textinfo="label+percent",textfont_size=11))
        fig_pv.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=200,showlegend=False,
                             margin=dict(t=10,b=10,l=10,r=10),annotations=[dict(text=fmt_inr(yr_sal),x=0.5,y=0.5,font_size=14,font_color="white",showarrow=False)])
        st.plotly_chart(fig_pv, use_container_width=True, key="setup_pv")

    st.divider()
    st.markdown("### 📊 Yearly Budget Allocation Overview")
    yr_rules = rules_df[rules_df["Year"]==rule_year].copy() if not rules_df.empty else pd.DataFrame()
    if yr_rules.empty:
        st.info(f"No monthly rules saved for {rule_year} yet.")
    else:
        yr_rules = yr_rules.sort_values("Month",key=lambda x: x.map({m:i for i,m in enumerate(MONTH_NAMES)}))
        yb1,yb2 = st.columns([1.6,1])
        with yb1:
            fig_bl = go.Figure()
            for name,col,key in [("🏠 Needs","#3B82F6","Needs_Pct"),("🎉 Wants","#F59E0B","Wants_Pct"),("🏦 Savings","#10B981","Savings_Pct")]:
                fig_bl.add_trace(go.Bar(name=name,x=yr_rules["Month"],y=yr_rules[key],marker_color=col,marker_line_width=0,
                                        text=yr_rules[key].apply(lambda x:f"{x:.0f}%"),textposition="inside",textfont_color="white"))
            fig_bl.update_layout(barmode="stack",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
                                 legend=dict(orientation="h",y=1.12),margin=dict(t=20,b=10,l=10,r=10),
                                 yaxis=dict(range=[0,100],ticksuffix="%",gridcolor="rgba(255,255,255,0.05)"),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_bl, use_container_width=True)
        with yb2:
            n_avg,w_avg,s_avg = yr_rules["Needs_Pct"].mean(),yr_rules["Wants_Pct"].mean(),yr_rules["Savings_Pct"].mean()
            fig_av = go.Figure(go.Pie(labels=[f"Needs {n_avg:.1f}%",f"Wants {w_avg:.1f}%",f"Savings {s_avg:.1f}%"],
                                      values=[n_avg,w_avg,s_avg],hole=0.5,marker_colors=["#3B82F6","#F59E0B","#10B981"],
                                      textinfo="label+percent",textfont_size=11))
            fig_av.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=240,showlegend=False,margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig_av, use_container_width=True, key="yr_avg")
        disp_r = yr_rules[["Month","Needs_Pct","Wants_Pct","Savings_Pct"]].copy()
        disp_r.columns = ["Month","Needs %","Wants %","Savings %"]
        disp_r["Rule"] = disp_r.apply(lambda r: f"{r['Needs %']:.0f}-{r['Wants %']:.0f}-{r['Savings %']:.0f}",axis=1)
        st.dataframe(disp_r[["Month","Rule","Needs %","Wants %","Savings %"]],use_container_width=True,hide_index=True)

    st.divider()
    st.markdown("### 📅 Year-wise Salary & Weekly Limit")
    with st.form("setup_form"):
        edited_setup = st.data_editor(setup_df[["Year","Salary","Weekly_Limit"]],use_container_width=True,num_rows="dynamic",
            column_config={"Year":st.column_config.NumberColumn("Year",format="%d"),
                           "Salary":st.column_config.NumberColumn("Monthly Salary (₹)",format="₹%d"),
                           "Weekly_Limit":st.column_config.NumberColumn("Weekly Limit (₹)",format="₹%d")},hide_index=True)
        if st.form_submit_button("💾 Save Salary Table",use_container_width=True):
            edited_setup["Needs"]=(edited_setup["Salary"]*0.5).astype(int)
            edited_setup["Wants"]=(edited_setup["Salary"]*0.3).astype(int)
            edited_setup["Savings"]=(edited_setup["Salary"]*0.2).astype(int)
            save_setup(edited_setup); st.success("✅ Saved!"); st.rerun()

    st.divider()
    st.markdown("### 📂 Data Management")
    dm1,dm2 = st.columns(2)
    with dm1:
        st.markdown("**📥 Export Data**")
        ex1,ex2 = st.columns(2)
        with ex1: exp_yr = st.selectbox("Export Year",  ["All Years"]+[str(y) for y in available_years()], key="exp_yr")
        with ex2: exp_mo = st.selectbox("Export Month", ["All Months"]+MONTH_NAMES, key="exp_mo")
        exp_df = load_all_years() if exp_yr=="All Years" else load_year(int(exp_yr))
        if exp_mo != "All Months" and not exp_df.empty:
            exp_df = exp_df[exp_df["Date"].dt.month==MONTH_NAMES.index(exp_mo)+1]
        st.caption(f"{len(exp_df)} rows selected")
        st.download_button("📥 Download CSV",data=exp_df.to_csv(index=False),file_name=f"expenses_{exp_yr}_{exp_mo}.csv",mime="text/csv",use_container_width=True)
    with dm2:
        st.markdown("**📤 Import CSV**")
        uploaded = st.file_uploader("Upload expenses CSV",type="csv",key="import_csv")
        if uploaded:
            try:
                imp_df = pd.read_csv(uploaded,parse_dates=["Date"])
                st.caption(f"{len(imp_df)} rows in file")
                if st.button("✅ Confirm Import",use_container_width=True):
                    for yr,grp in imp_df.groupby(imp_df["Date"].dt.year):
                        existing = load_year(int(yr))
                        save_year(pd.concat([existing,grp]).drop_duplicates().reset_index(drop=True),int(yr))
                    st.success(f"Imported {len(imp_df)} rows!"); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

    st.divider()
    st.markdown("### 🗑️ Clear / Delete Data")
    st.markdown('<div class="budget-alert alert-danger" style="margin-bottom:12px;">⚠️ Deleted data cannot be recovered. Export a backup first.</div>', unsafe_allow_html=True)
    cl1,cl2,cl3 = st.columns(3)
    with cl1:
        del_scope = st.selectbox("Delete scope",["Select…","Specific Month","Full Year","All Data"],key="del_scope")
    with cl2:
        del_yr = st.selectbox("Year", [str(y) for y in available_years()], key="del_yr") if del_scope in ["Specific Month","Full Year"] else None
        del_mo = st.selectbox("Month", MONTH_NAMES, key="del_mo") if del_scope=="Specific Month" else None
    with cl3:
        st.markdown("&nbsp;",unsafe_allow_html=True)
        confirm_del = st.checkbox("☑️ I understand this is permanent",key="confirm_del")
        if del_scope!="Select…" and st.button("🗑️ Delete Now",type="secondary",use_container_width=True):
            if not confirm_del: st.error("Please tick the confirmation checkbox first.")
            elif del_scope=="Specific Month" and del_yr and del_mo:
                delete_month_data(int(del_yr),MONTH_NAMES.index(del_mo)+1); st.success(f"✅ Deleted {del_mo} {del_yr}"); st.rerun()
            elif del_scope=="Full Year" and del_yr:
                delete_year_data(int(del_yr)); st.success(f"✅ Deleted all data for {del_yr}"); st.rerun()
            elif del_scope=="All Data":
                for y in available_years(): delete_year_data(y)
                st.success("✅ All expense data deleted."); st.rerun()
                
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import os
# from datetime import datetime, date, timedelta
# import calendar
# import numpy as np

# st.set_page_config(page_title="Paisa Tracker 💰", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

# DATA_DIR    = "."
# SETUP_FILE  = "setup.csv"
# BUDGET_FILE = "budget_rules.csv"
# COLS        = ["Date","Description","Category","Amount","Payment Mode","Type","Notes"]

# CATEGORIES  = ["Life Infrastructure","Lifestyle Enjoyment","Performance & Growth","Relationships & Generosity","Future Me"]
# CATEGORY_TYPES = {"Life Infrastructure":"Need","Lifestyle Enjoyment":"Want","Performance & Growth":"Need","Relationships & Generosity":"Want","Future Me":"Saving"}
# PAYMENT_MODES  = ["UPI","Credit Card","Debit Card","Cash","Bank Transfer"]
# MONTH_NAMES    = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
# CAT_COLORS  = {"Life Infrastructure":"#3B82F6","Lifestyle Enjoyment":"#F59E0B","Performance & Growth":"#10B981","Relationships & Generosity":"#EC4899","Future Me":"#8B5CF6"}
# TYPE_COLORS = {"Need":"#3B82F6","Want":"#F59E0B","Saving":"#10B981"}

# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
# html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
# .stApp{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);}
# div[data-testid="metric-container"]{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:20px !important;backdrop-filter:blur(10px);}
# div[data-testid="metric-container"] label{font-size:12px !important;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.5) !important;}
# div[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif !important;font-size:28px !important;font-weight:700;color:#e2e8f0 !important;}
# section[data-testid="stSidebar"]{background:rgba(10,10,20,0.95) !important;border-right:1px solid rgba(255,255,255,0.06);}
# .stButton button{background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;color:white !important;border:none !important;border-radius:10px !important;font-weight:600 !important;}
# .stTabs [data-baseweb="tab-list"]{gap:6px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:6px 8px;margin-bottom:28px;}
# .stTabs [data-baseweb="tab"]{border-radius:12px !important;color:rgba(255,255,255,0.5) !important;font-weight:500 !important;font-size:14px !important;padding:10px 22px !important;border:none !important;background:transparent !important;}
# .stTabs [data-baseweb="tab"]:hover{color:rgba(255,255,255,0.85) !important;background:rgba(255,255,255,0.06) !important;}
# .stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(99,102,241,0.35),rgba(139,92,246,0.35)) !important;color:white !important;font-weight:600 !important;box-shadow:0 2px 12px rgba(99,102,241,0.25) !important;border:1px solid rgba(99,102,241,0.4) !important;}
# .stTabs [data-baseweb="tab-highlight"]{display:none !important;}
# .stTabs [data-baseweb="tab-border"]{display:none !important;}
# .section-header{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#e2e8f0;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid rgba(99,102,241,0.3);}
# .app-title{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;background:linear-gradient(135deg,#6366f1,#a78bfa,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
# .budget-alert{padding:12px 16px;border-radius:10px;margin:8px 0;font-size:14px;font-weight:500;}
# .alert-danger{background:rgba(239,68,68,0.15);border-left:3px solid #ef4444;color:#fca5a5;}
# .alert-warning{background:rgba(245,158,11,0.15);border-left:3px solid #f59e0b;color:#fcd34d;}
# .alert-success{background:rgba(16,185,129,0.15);border-left:3px solid #10b981;color:#6ee7b7;}
# /* Action icon buttons — minimal circle style */
# .icon-btn {
#     display:inline-flex; align-items:center; justify-content:center;
#     width:30px; height:30px; border-radius:50%;
#     border:none; cursor:pointer; transition:all 0.18s ease;
#     font-size:14px; line-height:1; padding:0;
# }
# .icon-btn-edit {
#     background:rgba(99,102,241,0.15);
#     color:#a78bfa;
#     border:1px solid rgba(99,102,241,0.3);
# }
# .icon-btn-edit:hover { background:rgba(99,102,241,0.3); border-color:#6366f1; }
# .icon-btn-delete {
#     background:rgba(239,68,68,0.12);
#     color:#f87171;
#     border:1px solid rgba(239,68,68,0.25);
# }
# .icon-btn-delete:hover { background:rgba(239,68,68,0.28); border-color:#ef4444; }
# /* Keep all other streamlit buttons clean */
# button[data-testid="baseButton-secondary"]{
#     padding:4px 10px !important; font-size:12px !important;
#     min-height:28px !important; height:28px !important;
#     border-radius:8px !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # ── Data helpers ───────────────────────────────────────────────────────────────
# def year_file(year): return os.path.join(DATA_DIR, f"expenses_{int(year)}.csv")

# def available_years():
#     yrs = []
#     for f in os.listdir(DATA_DIR):
#         if f.startswith("expenses_") and f.endswith(".csv"):
#             try: yrs.append(int(f.replace("expenses_","").replace(".csv","")))
#             except: pass
#     return sorted(yrs)

# @st.cache_data(ttl=1)
# def load_year(year):
#     fp = year_file(year)
#     if os.path.exists(fp):
#         df = pd.read_csv(fp, parse_dates=["Date"])
#         df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
#         return df
#     return pd.DataFrame(columns=COLS)

# def save_year(df, year):
#     df.to_csv(year_file(year), index=False)
#     load_year.clear()

# def load_all_years():
#     frames = [load_year(y) for y in available_years()]
#     return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)

# def delete_year_data(year):
#     fp = year_file(year)
#     if os.path.exists(fp): os.remove(fp)
#     load_year.clear()

# def delete_month_data(year, month_num):
#     df = load_year(year)
#     save_year(df[df["Date"].dt.month != month_num].reset_index(drop=True), year)

# def load_setup():
#     if os.path.exists(SETUP_FILE):
#         return pd.read_csv(SETUP_FILE)
#     return pd.DataFrame({"Year":[2026,2027,2028,2029,2030],"Salary":[50000,55000,60500,66550,73205],
#                           "Needs":[25000,27500,30250,33275,36602],"Wants":[15000,16500,18150,19965,21961],
#                           "Savings":[10000,11000,12100,13310,14641],"Weekly_Limit":[10000]*5})

# def save_setup(df): df.to_csv(SETUP_FILE, index=False)

# def load_budget_rules():
#     if os.path.exists(BUDGET_FILE):
#         return pd.read_csv(BUDGET_FILE)
#     return pd.DataFrame(columns=["Year","Month","Needs_Pct","Wants_Pct","Savings_Pct"])

# def save_budget_rules(df): df.to_csv(BUDGET_FILE, index=False)

# def get_budget_rule(year, month):
#     rules = load_budget_rules()
#     if rules.empty: return 50.0, 30.0, 20.0
#     if month == "All":
#         yr = rules[rules["Year"]==year]
#         if yr.empty: return 50.0, 30.0, 20.0
#         return float(yr["Needs_Pct"].mean()), float(yr["Wants_Pct"].mean()), float(yr["Savings_Pct"].mean())
#     r = rules[(rules["Year"]==year) & (rules["Month"]==month)]
#     if not r.empty:
#         row = r.iloc[0]
#         return float(row["Needs_Pct"]), float(row["Wants_Pct"]), float(row["Savings_Pct"])
#     # fall back to last saved month
#     mo_idx = MONTH_NAMES.index(month)
#     for i in range(mo_idx-1,-1,-1):
#         prev = rules[(rules["Year"]==year) & (rules["Month"]==MONTH_NAMES[i])]
#         if not prev.empty:
#             row = prev.iloc[0]
#             return float(row["Needs_Pct"]), float(row["Wants_Pct"]), float(row["Savings_Pct"])
#     return 50.0, 30.0, 20.0

# def fmt_inr(amount):
#     if amount >= 1_00_00_000: return f"₹{amount/1_00_00_000:.1f}Cr"
#     elif amount >= 1_00_000:  return f"₹{amount/1_00_000:.1f}L"
#     elif amount >= 1000:
#         s = f"{int(amount):,}"; parts = s.split(",")
#         return f"₹{','.join(parts[:-1])},{parts[-1]}" if len(parts)>1 else f"₹{s}"
#     return f"₹{int(amount)}"

# def score_calc(df_month, salary, needs_pct=50, wants_pct=30, savings_pct=20):
#     if df_month.empty or salary==0: return 5
#     needs   = df_month[df_month["Type"]=="Need"]["Amount"].sum()
#     wants   = df_month[df_month["Type"]=="Want"]["Amount"].sum()
#     savings = df_month[df_month["Type"]=="Saving"]["Amount"].sum()
#     score = 10
#     if needs/salary   > needs_pct/100:   score -= min(3,(needs/salary - needs_pct/100)*10)
#     if wants/salary   > wants_pct/100:   score -= min(3,(wants/salary - wants_pct/100)*10)
#     if savings/salary < savings_pct/100: score -= min(3,(savings_pct/100 - savings/salary)*10)
#     return max(1, min(10, round(score,1)))

# # ── Sidebar ────────────────────────────────────────────────────────────────────
# with st.sidebar:
#     st.markdown('<div class="app-title">💰 Paisa Tracker</div>', unsafe_allow_html=True)
#     st.caption("Your personal finance companion")
#     st.divider()
#     st.markdown("### 🗕 Quick Filter")
#     setup_df = load_setup()
#     _now = datetime.now()
#     current_year  = _now.year
#     current_month = MONTH_NAMES[_now.month-1]
#     years_available = sorted(set(setup_df["Year"].tolist()) | set(available_years()))
#     _yr_idx = years_available.index(current_year) if current_year in years_available else len(years_available)-1

#     # FIX 5: use explicit session_state keys so switching month always reacts immediately
#     if "sel_year" not in st.session_state:
#         st.session_state["sel_year"]  = years_available[_yr_idx]
#     if "sel_month" not in st.session_state:
#         st.session_state["sel_month"] = current_month

#     sel_year  = st.selectbox("Year",  years_available,
#                               index=years_available.index(st.session_state["sel_year"]) if st.session_state["sel_year"] in years_available else _yr_idx,
#                               key="sel_year")
#     sel_month = st.selectbox("Month", ["All"]+MONTH_NAMES,
#                               index=(["All"]+MONTH_NAMES).index(st.session_state["sel_month"]) if st.session_state["sel_month"] in ["All"]+MONTH_NAMES else 0,
#                               key="sel_month")

#     st.divider()
#     yr_row = setup_df[setup_df["Year"]==sel_year]
#     current_salary = int(yr_row["Salary"].values[0]) if not yr_row.empty else 50000
#     weekly_limit   = int(yr_row["Weekly_Limit"].values[0]) if not yr_row.empty and "Weekly_Limit" in yr_row.columns else 10000
#     _np, _wp, _sp  = get_budget_rule(sel_year, sel_month)

#     st.markdown(f"### 📊 Budget ({_np:.0f}-{_wp:.0f}-{_sp:.0f} Rule)")
#     st.markdown(f"""
# <div style="display:flex;flex-direction:column;gap:8px;margin-top:4px;">
#   <div style="background:linear-gradient(135deg,rgba(99,102,241,0.18),rgba(139,92,246,0.12));border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:12px 14px;">
#     <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:4px;">💼 Monthly Salary</div>
#     <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#c4b5fd;line-height:1;">{fmt_inr(current_salary)}</div>
#   </div>
#   <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:12px;padding:11px 14px;">
#     <div style="display:flex;justify-content:space-between;align-items:center;">
#       <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🏠 Needs</div>
#       <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#93c5fd;line-height:1;">{fmt_inr(current_salary*_np/100)}</div></div>
#       <div style="background:rgba(59,130,246,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#93c5fd;">{_np:.0f}%</div>
#     </div>
#     <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_np}%;height:100%;background:#3b82f6;border-radius:4px;"></div></div>
#   </div>
#   <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);border-radius:12px;padding:11px 14px;">
#     <div style="display:flex;justify-content:space-between;align-items:center;">
#       <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🎉 Wants</div>
#       <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fcd34d;line-height:1;">{fmt_inr(current_salary*_wp/100)}</div></div>
#       <div style="background:rgba(245,158,11,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#fcd34d;">{_wp:.0f}%</div>
#     </div>
#     <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_wp}%;height:100%;background:#f59e0b;border-radius:4px;"></div></div>
#   </div>
#   <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:11px 14px;">
#     <div style="display:flex;justify-content:space-between;align-items:center;">
#       <div><div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,0.45);margin-bottom:3px;">🏦 Savings</div>
#       <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#6ee7b7;line-height:1;">{fmt_inr(current_salary*_sp/100)}</div></div>
#       <div style="background:rgba(16,185,129,0.25);border-radius:8px;padding:4px 9px;font-size:12px;font-weight:700;color:#6ee7b7;">{_sp:.0f}%</div>
#     </div>
#     <div style="margin-top:8px;background:rgba(255,255,255,0.07);border-radius:4px;height:4px;"><div style="width:{_sp}%;height:100%;background:#10b981;border-radius:4px;"></div></div>
#   </div>
# </div>
# """, unsafe_allow_html=True)
#     st.divider()
#     st.caption("📁 Data stored as year-wise CSVs")
#     st.caption("Made with ❤️ for India")

# # ── Filtered data (FIX 5: always re-read from session_state keys) ──────────────
# def filter_data(year, month):
#     d = load_year(year).copy()
#     if not d.empty and month != "All":
#         d = d[d["Date"].dt.month == MONTH_NAMES.index(month)+1]
#     return d

# filtered_df = filter_data(sel_year, sel_month)

# # ── Tabs ───────────────────────────────────────────────────────────────────────
# tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
#     "🏠 Dashboard", "📝 Daily Tracker", "📅 Weekly Analysis",
#     "📆 Monthly Analysis", "🗓️ Yearly Calendar", "⚙️ Setup"])

# # ══════════════════════════════════════════════════════════════════════
# # TAB 1 — DASHBOARD
# # ══════════════════════════════════════════════════════════════════════
# with tab1:
#     st.markdown('<div class="section-header">📊 Financial Dashboard</div>', unsafe_allow_html=True)
#     if filtered_df.empty:
#         st.info("No expenses found for the selected period. Add expenses in the Daily Tracker tab!")
#     else:
#         total_spent   = filtered_df["Amount"].sum()
#         needs_spent   = filtered_df[filtered_df["Type"]=="Need"]["Amount"].sum()
#         wants_spent   = filtered_df[filtered_df["Type"]=="Want"]["Amount"].sum()
#         savings_spent = filtered_df[filtered_df["Type"]=="Saving"]["Amount"].sum()
#         budget_needs  = current_salary * _np / 100
#         budget_wants  = current_salary * _wp / 100
#         budget_savings= current_salary * _sp / 100
#         score = score_calc(filtered_df, current_salary, _np, _wp, _sp)

#         k1,k2,k3,k4,k5 = st.columns(5)
#         k1.metric("💸 Total Spent",  fmt_inr(total_spent),   delta=fmt_inr(current_salary-total_spent)+" left")
#         k2.metric("🏠 Needs",        fmt_inr(needs_spent),   delta=fmt_inr(budget_needs-needs_spent)+" left")
#         k3.metric("🎉 Wants",        fmt_inr(wants_spent),   delta=fmt_inr(budget_wants-wants_spent)+" left")
#         k4.metric("🏦 Savings",      fmt_inr(savings_spent), delta=fmt_inr(budget_savings-savings_spent)+" gap", delta_color="inverse")
#         k5.metric("⭐ Health Score",  f"{score}/10")
#         st.divider()

#         ac, _ = st.columns([2,1])
#         with ac:
#             if needs_spent  > budget_needs:  st.markdown(f'<div class="budget-alert alert-danger">⚠️ Needs over budget by {fmt_inr(needs_spent-budget_needs)}</div>', unsafe_allow_html=True)
#             if wants_spent  > budget_wants:  st.markdown(f'<div class="budget-alert alert-danger">⚠️ Wants over budget by {fmt_inr(wants_spent-budget_wants)}</div>', unsafe_allow_html=True)
#             if savings_spent< budget_savings:st.markdown(f'<div class="budget-alert alert-warning">💡 Invest {fmt_inr(budget_savings-savings_spent)} more to hit savings goal</div>', unsafe_allow_html=True)
#             if score >= 7:                   st.markdown(f'<div class="budget-alert alert-success">✅ Great financial health! Keep it up.</div>', unsafe_allow_html=True)
#         st.divider()

#         c1,c2,c3 = st.columns([1.2,1.2,1])
#         with c1:
#             st.markdown("**Spending by Category**")
#             cat_sum = filtered_df.groupby("Category")["Amount"].sum().reset_index()
#             fig = px.pie(cat_sum, values="Amount", names="Category", color="Category",
#                          color_discrete_map=CAT_COLORS, hole=0.45)
#             fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
#                               font_color="white", legend_font_size=11, height=320,
#                               margin=dict(t=10,b=10,l=10,r=10))
#             fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
#             st.plotly_chart(fig, use_container_width=True)
#         with c2:
#             st.markdown(f"**{_np:.0f}-{_wp:.0f}-{_sp:.0f} Budget vs Actual**")
#             bdf = pd.DataFrame({"Type":["Needs","Wants","Savings"],
#                                 "Budget":[budget_needs,budget_wants,budget_savings],
#                                 "Actual":[needs_spent,wants_spent,savings_spent]})
#             fig2 = go.Figure()
#             fig2.add_trace(go.Bar(name="Budget",x=bdf["Type"],y=bdf["Budget"],marker_color="rgba(99,102,241,0.4)",marker_line_width=0))
#             fig2.add_trace(go.Bar(name="Actual", x=bdf["Type"],y=bdf["Actual"], marker_color=["#3B82F6","#F59E0B","#10B981"],marker_line_width=0))
#             fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",barmode="group",height=320,
#                                legend=dict(orientation="h",y=1.1),margin=dict(t=30,b=10,l=10,r=10),
#                                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig2, use_container_width=True)
#         with c3:
#             st.markdown("**Payment Mode Split**")
#             pm = filtered_df.groupby("Payment Mode")["Amount"].sum().reset_index()
#             pm_col = {"UPI":"#6366f1","Credit Card":"#ec4899","Debit Card":"#3b82f6","Cash":"#f59e0b","Bank Transfer":"#10b981"}
#             fig3 = px.pie(pm, values="Amount", names="Payment Mode", color="Payment Mode",
#                           color_discrete_map=pm_col, hole=0.45)
#             fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
#                                font_color="white",legend_font_size=10,height=320,margin=dict(t=10,b=10,l=10,r=10))
#             fig3.update_traces(textposition="inside",textinfo="percent",textfont_size=10)
#             st.plotly_chart(fig3, use_container_width=True)
#         st.divider()

#         c4,c5 = st.columns([2,1])
#         with c4:
#             st.markdown("**Daily Spending Trend**")
#             daily = filtered_df.groupby(filtered_df["Date"].dt.date)["Amount"].sum().reset_index()
#             daily.columns = ["Date","Amount"]
#             daily["Date"] = pd.to_datetime(daily["Date"])
#             daily["7d_avg"] = daily["Amount"].rolling(7,min_periods=1).mean()
#             fig4 = go.Figure()
#             fig4.add_trace(go.Bar(x=daily["Date"],y=daily["Amount"],name="Daily",marker_color="rgba(99,102,241,0.5)",marker_line_width=0))
#             fig4.add_trace(go.Scatter(x=daily["Date"],y=daily["7d_avg"],name="7-day avg",line=dict(color="#ec4899",width=2.5)))
#             fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=280,
#                                legend=dict(orientation="h",y=1.1),margin=dict(t=30,b=10,l=10,r=10),
#                                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig4, use_container_width=True)
#         with c5:
#             st.markdown("**Top 5 Categories**")
#             top5 = filtered_df.groupby("Category")["Amount"].sum().nlargest(5).reset_index()
#             fig5 = px.bar(top5,x="Amount",y="Category",orientation="h",color="Category",color_discrete_map=CAT_COLORS)
#             fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=280,
#                                showlegend=False,margin=dict(t=10,b=10,l=10,r=10),
#                                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig5, use_container_width=True)
#         st.divider()
#         st.markdown("**🕐 Recent Transactions**")
#         recent = filtered_df.sort_values("Date",ascending=False).head(10).copy()
#         recent["Date"] = recent["Date"].dt.strftime("%d %b %Y")
#         recent["Amount"] = recent["Amount"].apply(fmt_inr)
#         st.dataframe(recent[["Date","Description","Category","Amount","Payment Mode","Type","Notes"]],
#                      use_container_width=True, hide_index=True)

# # ══════════════════════════════════════════════════════════════════════
# # TAB 2 — DAILY TRACKER
# # ══════════════════════════════════════════════════════════════════════
# with tab2:
#     st.markdown('<div class="section-header">📝 Daily Expense Tracker</div>', unsafe_allow_html=True)

#     with st.expander("➕ Add New Expense", expanded=True):
#         with st.form("add_expense_form", clear_on_submit=True):
#             fc1,fc2,fc3 = st.columns(3)
#             with fc1:
#                 exp_date   = st.date_input("Date", value=date.today())
#                 exp_amount = st.number_input("Amount (₹)", min_value=0, step=10, value=0)
#             with fc2:
#                 exp_desc     = st.text_input("Description", placeholder="e.g. Swiggy lunch, Uber ride")
#                 exp_category = st.selectbox("Category", CATEGORIES)
#             with fc3:
#                 exp_payment = st.selectbox("Payment Mode", PAYMENT_MODES)
#                 exp_type    = st.selectbox("Type", ["Need","Want","Saving"],
#                                            index=["Need","Want","Saving"].index(CATEGORY_TYPES.get(exp_category,"Want")))
#                 exp_notes   = st.text_input("Notes (optional)", placeholder="Optional remark")
#             submitted = st.form_submit_button("💾 Add Expense", use_container_width=True)
#             if submitted:
#                 if exp_amount <= 0:       st.error("Please enter a valid amount!")
#                 elif not exp_desc.strip(): st.error("Please enter a description!")
#                 else:
#                     df = load_year(exp_date.year)
#                     df = pd.concat([df, pd.DataFrame([{"Date":pd.Timestamp(exp_date),
#                         "Description":exp_desc.strip(),"Category":exp_category,"Amount":exp_amount,
#                         "Payment Mode":exp_payment,"Type":exp_type,"Notes":exp_notes.strip()}])], ignore_index=True)
#                     save_year(df, exp_date.year)
#                     st.success(f"✅ Added: {exp_desc} — {fmt_inr(exp_amount)}")
#                     st.rerun()

#     st.divider()
#     st.markdown("**🔍 Filter & Search**")
#     f1,f2,f3,f4 = st.columns(4)
#     with f1: filter_cat  = st.multiselect("Category",     CATEGORIES,              default=[])
#     with f2: filter_pay  = st.multiselect("Payment Mode", PAYMENT_MODES,           default=[])
#     with f3: filter_type = st.multiselect("Type",         ["Need","Want","Saving"], default=[])
#     with f4: search_text = st.text_input("Search Description", placeholder="Search...")

#     # FIX 4: load full year, stamp _file_idx BEFORE any filtering, then apply ALL filters
#     _full_yr = load_year(sel_year).copy()
#     _full_yr["_file_idx"] = _full_yr.index

#     display_df = _full_yr.copy()
#     # FIX 4+5: month filter applied here consistently
#     if sel_month != "All":
#         display_df = display_df[display_df["Date"].dt.month == MONTH_NAMES.index(sel_month)+1]
#     # Category / payment / type filters — FIX 4: these now work for "All" month too
#     if filter_cat:  display_df = display_df[display_df["Category"].isin(filter_cat)]
#     if filter_pay:  display_df = display_df[display_df["Payment Mode"].isin(filter_pay)]
#     if filter_type: display_df = display_df[display_df["Type"].isin(filter_type)]
#     if search_text: display_df = display_df[display_df["Description"].str.contains(search_text, case=False, na=False)]
#     display_df = display_df.sort_values("Date", ascending=False)  # preserve _file_idx

#     # Pagination controls
#     pg_col1, pg_col2, pg_col3 = st.columns([2,1,1])
#     with pg_col1:
#         st.markdown(f"**{len(display_df)} transactions · Total: {fmt_inr(display_df['Amount'].sum())}**")
#     with pg_col2:
#         page_size_opt = st.selectbox("Rows per page", [10,25,50,100,"All"], index=0, key="page_size")
#     with pg_col3:
#         if page_size_opt != "All" and len(display_df) > 0:
#             total_pages   = max(1, -(-len(display_df) // int(page_size_opt)))
#             if "tracker_page" not in st.session_state: st.session_state["tracker_page"] = 1
#             if st.session_state["tracker_page"] > total_pages: st.session_state["tracker_page"] = 1
#             current_page  = st.session_state["tracker_page"]
#             page_start    = (current_page-1)*int(page_size_opt)
#             page_df       = display_df.iloc[page_start : page_start+int(page_size_opt)]
#             st.markdown(f"<div style='padding:8px 0;font-size:13px;color:rgba(255,255,255,0.5);'>"
#                         f"Page {current_page}/{total_pages}</div>", unsafe_allow_html=True)
#         else:
#             page_df = display_df
#             total_pages, current_page = 1, 1

#     # Edit panel — appears above the table
#     if "edit_row" in st.session_state:
#         _efi   = st.session_state["edit_row"]
#         _eyear = st.session_state.get("edit_year", sel_year)
#         _fy    = load_year(_eyear)
#         if _efi < len(_fy):
#             er = _fy.iloc[_efi]
#             st.markdown(
#                 f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08));'
#                 f'border:1.5px solid rgba(99,102,241,0.4);border-radius:16px;padding:20px 24px;margin:12px 0 16px 0;">'
#                 f'<div style="font-family:Space Grotesk,sans-serif;font-size:15px;font-weight:700;'
#                 f'color:#a78bfa;margin-bottom:14px;">✏️ Editing — {er["Description"]}</div>',
#                 unsafe_allow_html=True)
#             with st.form("edit_form"):
#                 ef1,ef2,ef3,ef4 = st.columns([1.2,2,1.5,1.5])
#                 with ef1:
#                     new_date   = st.date_input("Date",        value=pd.Timestamp(er["Date"]).date())
#                     new_amount = st.number_input("Amount (₹)", min_value=0, step=10, value=int(er["Amount"]))
#                 with ef2:
#                     new_desc = st.text_input("Description", value=str(er["Description"]))
#                     new_cat  = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(er["Category"]) if er["Category"] in CATEGORIES else 0)
#                 with ef3:
#                     new_pay  = st.selectbox("Payment Mode", PAYMENT_MODES, index=PAYMENT_MODES.index(er["Payment Mode"]) if er["Payment Mode"] in PAYMENT_MODES else 0)
#                     new_type = st.selectbox("Type", ["Need","Want","Saving"], index=["Need","Want","Saving"].index(er["Type"]) if er["Type"] in ["Need","Want","Saving"] else 0)
#                 with ef4:
#                     new_notes = st.text_input("Notes", value=str(er["Notes"]) if pd.notna(er["Notes"]) else "")
#                     st.markdown(" ")
#                 sb1,sb2 = st.columns(2)
#                 save_edit   = sb1.form_submit_button("💾 Save Changes", use_container_width=True)
#                 cancel_edit = sb2.form_submit_button("✖ Cancel",        use_container_width=True)
#             st.markdown("</div>", unsafe_allow_html=True)
#             if save_edit:
#                 _fy.at[_efi,"Date"]         = pd.Timestamp(new_date)
#                 _fy.at[_efi,"Description"]  = new_desc.strip()
#                 _fy.at[_efi,"Category"]     = new_cat
#                 _fy.at[_efi,"Amount"]       = new_amount
#                 _fy.at[_efi,"Payment Mode"] = new_pay
#                 _fy.at[_efi,"Type"]         = new_type
#                 _fy.at[_efi,"Notes"]        = new_notes.strip()
#                 save_year(_fy, _eyear)
#                 del st.session_state["edit_row"]
#                 st.success("✅ Transaction updated!")
#                 st.rerun()
#             if cancel_edit:
#                 del st.session_state["edit_row"]
#                 st.rerun()

#     # ── Modern fixed-height dataframe table ──────────────────────────────────────
#     if page_df.empty:
#         st.info("No transactions found.")
#     else:
#         # Build display copy with colored Type column using emoji badges
#         tbl = page_df.copy()
#         tbl["Date"]  = pd.to_datetime(tbl["Date"]).dt.strftime("%d %b %Y")
#         tbl["₹ Amount"] = tbl["Amount"].apply(fmt_inr)
#         # Type badge: colored circle + label
#         type_badge = {"Need": "🔵 Need", "Want": "🟡 Want", "Saving": "🟢 Saving"}
#         tbl["Type"] = tbl["Type"].apply(lambda t: type_badge.get(t, t))
#         tbl["Notes"] = tbl["Notes"].fillna("").astype(str).replace("nan","")
#         tbl["#"] = tbl["_file_idx"].astype(int)

#         show_cols = ["#","Date","Description","Category","₹ Amount","Payment Mode","Type","Notes"]

#         st.dataframe(
#             tbl[show_cols],
#             use_container_width=True,
#             hide_index=True,
#             height=400,
#             column_config={
#                 "#":            st.column_config.NumberColumn("#",             width=45),
#                 "Date":         st.column_config.TextColumn("Date",           width=105),
#                 "Description":  st.column_config.TextColumn("Description",    width=180),
#                 "Category":     st.column_config.TextColumn("Category",       width=165),
#                 "₹ Amount":     st.column_config.TextColumn("Amount",         width=90),
#                 "Payment Mode": st.column_config.TextColumn("Payment Mode",   width=120),
#                 "Type":         st.column_config.TextColumn("Type",           width=105),
#                 "Notes":        st.column_config.TextColumn("Notes",          width=140),
#             }
#         )

#         # ── Row selector + Edit / Delete ──────────────────────────────────────
#         st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
#         sel_c1, sel_c2, sel_c3 = st.columns([2.2, 0.9, 0.9])
#         with sel_c1:
#             row_options = {
#                 f"#{int(r['_file_idx'])}  {str(r['Description'])[:30]}  ·  {fmt_inr(r['Amount'])}": int(r["_file_idx"])
#                 for _, r in page_df.iterrows()
#             }
#             sel_label = st.selectbox(
#                 "Select row", ["— select a row to edit or delete —"] + list(row_options.keys()),
#                 key="row_selector", label_visibility="collapsed"
#             )
#             sel_fidx = row_options.get(sel_label)

#         with sel_c2:
#             if st.button("✎  Edit", key="tbl_edit_btn", use_container_width=True,
#                          disabled=(sel_fidx is None)):
#                 st.session_state["edit_row"]  = sel_fidx
#                 st.session_state["edit_year"] = sel_year
#                 st.session_state.pop("confirm_del_idx", None)
#                 st.rerun()

#         with sel_c3:
#             if st.button("⌫  Delete", key="tbl_del_btn", use_container_width=True,
#                          disabled=(sel_fidx is None)):
#                 st.session_state["confirm_del_idx"]  = sel_fidx
#                 st.session_state["confirm_del_year"] = sel_year
#                 st.session_state.pop("edit_row", None)
#                 st.rerun()

#         # Delete confirmation
#         if "confirm_del_idx" in st.session_state:
#             _cdfi  = st.session_state["confirm_del_idx"]
#             _match = page_df[page_df["_file_idx"] == _cdfi]
#             if not _match.empty:
#                 _crow = _match.iloc[0]
#                 dc = st.columns([3.5, 1, 1])
#                 dc[0].markdown(
#                     f"<div style='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);"
#                     f"border-radius:10px;padding:9px 14px;font-size:13px;color:#fca5a5;margin-top:6px;'>"
#                     f"⚠️ Delete <b>{_crow['Description']}</b> ({fmt_inr(_crow['Amount'])})? Cannot be undone.</div>",
#                     unsafe_allow_html=True)
#                 if dc[1].button("✅ Yes", key="cy_confirm", use_container_width=True):
#                     _fy2 = load_year(sel_year)
#                     _fy2 = _fy2.drop(index=_cdfi).reset_index(drop=True)
#                     save_year(_fy2, sel_year)
#                     st.session_state.pop("confirm_del_idx", None)
#                     st.session_state.pop("confirm_del_year", None)
#                     st.session_state.pop("row_selector", None)
#                     st.success(f"Deleted: {_crow['Description']}")
#                     st.rerun()
#                 if dc[2].button("✖ No", key="cn_confirm", use_container_width=True):
#                     st.session_state.pop("confirm_del_idx", None)
#                     st.session_state.pop("confirm_del_year", None)
#                     st.rerun()

#         # Pagination footer
#         if page_size_opt != "All" and total_pages > 1:
#             st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
#             pf1,pf2,pf3,pf4,pf5 = st.columns([1,1,2,1,1])
#             if pf1.button("⏮ First", use_container_width=True, key="pg_first"): st.session_state["tracker_page"]=1; st.rerun()
#             if pf2.button("◀ Prev",  use_container_width=True, key="pg_prev"):  st.session_state["tracker_page"]=max(1,current_page-1); st.rerun()
#             pf3.markdown(f"<div style='text-align:center;padding:8px;font-size:13px;color:rgba(255,255,255,0.6);'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
#             if pf4.button("Next ▶",  use_container_width=True, key="pg_next"):  st.session_state["tracker_page"]=min(total_pages,current_page+1); st.rerun()
#             if pf5.button("Last ⏭",  use_container_width=True, key="pg_last"):  st.session_state["tracker_page"]=total_pages; st.rerun()

#     st.divider()
#     _ecols = [c for c in display_df.columns if c != "_file_idx"]
#     st.download_button("📥 Export to CSV", data=display_df[_ecols].to_csv(index=False),
#                        file_name=f"expenses_{sel_year}_{sel_month}.csv", mime="text/csv")

# # ══════════════════════════════════════════════════════════════════════
# # TAB 3 — WEEKLY ANALYSIS
# # ══════════════════════════════════════════════════════════════════════
# with tab3:
#     st.markdown('<div class="section-header">📅 Weekly Analysis</div>', unsafe_allow_html=True)
#     if filtered_df.empty:
#         st.info("No data for selected period.")
#     else:
#         df_w = filtered_df.copy()
#         df_w["Week_Start"] = df_w["Date"].apply(lambda x: x - timedelta(days=x.weekday()))
#         wt = df_w.groupby("Week_Start")["Amount"].sum().reset_index()
#         wt.columns = ["Week_Start","Total"]
#         wt["Week_Label"] = wt["Week_Start"].dt.strftime("W/S %d %b")
#         wt["Over"] = wt["Total"] > weekly_limit
#         wt["Ratio"] = (wt["Total"]/weekly_limit*100).round(1)

#         w1,w2,w3,w4 = st.columns(4)
#         w1.metric("Total Weeks", len(wt))
#         w2.metric("Avg Weekly Spend", fmt_inr(wt["Total"].mean()))
#         w3.metric("Weeks Over Limit", int(wt["Over"].sum()))
#         w4.metric("Weekly Limit", fmt_inr(weekly_limit))
#         st.divider()

#         colors = ["#EF4444" if o else "#6366f1" for o in wt["Over"]]
#         fig_w = go.Figure()
#         fig_w.add_trace(go.Bar(x=wt["Week_Label"],y=wt["Total"],marker_color=colors,marker_line_width=0,
#                                name="Weekly Spend",text=wt["Total"].apply(fmt_inr),textposition="outside",textfont=dict(color="white",size=11)))
#         fig_w.add_hline(y=weekly_limit,line_dash="dash",line_color="#F59E0B",
#                         annotation_text=f"Limit: {fmt_inr(weekly_limit)}",annotation_font_color="#F59E0B")
#         fig_w.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=380,
#                             margin=dict(t=40,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
#                             yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#         st.plotly_chart(fig_w, use_container_width=True)
#         st.divider()

#         wc1,wc2 = st.columns(2)
#         with wc1:
#             st.markdown("**Weekly Spending by Category**")
#             wcat = df_w.groupby(["Week_Start","Category"])["Amount"].sum().reset_index()
#             wcat["Week_Label"] = wcat["Week_Start"].dt.strftime("W/S %d %b")
#             fig_ws = px.bar(wcat,x="Week_Label",y="Amount",color="Category",color_discrete_map=CAT_COLORS,barmode="stack")
#             fig_ws.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
#                                  legend_font_size=10,margin=dict(t=10,b=10,l=10,r=10),
#                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_ws, use_container_width=True)
#         with wc2:
#             st.markdown("**Weekly Limit Performance (%)**")
#             fig_wr = go.Figure()
#             r_colors = ["#EF4444" if r>100 else "#F59E0B" if r>70 else "#10B981" for r in wt["Ratio"]]
#             fig_wr.add_trace(go.Bar(x=wt["Week_Label"],y=wt["Ratio"],marker_color=r_colors,marker_line_width=0,
#                                     text=[f"{r}%" for r in wt["Ratio"]],textposition="outside",textfont=dict(color="white",size=10)))
#             fig_wr.add_hline(y=100,line_dash="dash",line_color="#F59E0B")
#             fig_wr.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
#                                  yaxis_title="% of Limit",margin=dict(t=10,b=10,l=10,r=10),
#                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_wr, use_container_width=True)

#         st.markdown("**Weekly Summary Table**")
#         disp_w = wt.copy()
#         disp_w["Total"]  = disp_w["Total"].apply(fmt_inr)
#         disp_w["Status"] = disp_w["Over"].apply(lambda x: "🔴 Over" if x else "🟢 OK")
#         disp_w["Ratio"]  = disp_w["Ratio"].apply(lambda x: f"{x}%")
#         st.dataframe(disp_w[["Week_Label","Total","Ratio","Status"]].rename(columns={"Week_Label":"Week","Total":"Spent","Ratio":"% of Limit"}),
#                      use_container_width=True, hide_index=True)

# # ══════════════════════════════════════════════════════════════════════
# # TAB 4 — MONTHLY ANALYSIS
# # ══════════════════════════════════════════════════════════════════════
# with tab4:
#     st.markdown('<div class="section-header">📆 Monthly Analysis</div>', unsafe_allow_html=True)
#     year_df = filter_data(sel_year, "All")
#     if year_df.empty:
#         st.info("No data for selected year.")
#     else:
#         year_df["Month_Num"]  = year_df["Date"].dt.month
#         year_df["Month_Name"] = year_df["Date"].dt.strftime("%b")
#         monthly_total = year_df.groupby(["Month_Num","Month_Name"])["Amount"].sum().reset_index().sort_values("Month_Num")
#         monthly_type  = year_df.groupby(["Month_Num","Month_Name","Type"])["Amount"].sum().reset_index().sort_values("Month_Num")

#         monthly_scores = []
#         for mn in monthly_total["Month_Num"].tolist():
#             m_df = year_df[year_df["Month_Num"]==mn]
#             mn_name = MONTH_NAMES[mn-1]
#             mnp,mwp,msp = get_budget_rule(sel_year, mn_name)
#             monthly_scores.append(score_calc(m_df, current_salary, mnp, mwp, msp))
#         monthly_total["Score"] = monthly_scores

#         m1,m2,m3,m4 = st.columns(4)
#         m1.metric("Highest Month", monthly_total.loc[monthly_total["Amount"].idxmax(),"Month_Name"], fmt_inr(monthly_total["Amount"].max()))
#         m2.metric("Lowest Month",  monthly_total.loc[monthly_total["Amount"].idxmin(),"Month_Name"], fmt_inr(monthly_total["Amount"].min()))
#         m3.metric("Avg Monthly Spend", fmt_inr(monthly_total["Amount"].mean()))
#         m4.metric("Total Year Spend",  fmt_inr(year_df["Amount"].sum()))
#         st.divider()

#         mc1,mc2 = st.columns(2)
#         with mc1:
#             st.markdown("**Monthly Spending Trend**")
#             fig_mt = go.Figure()
#             fig_mt.add_trace(go.Bar(x=monthly_total["Month_Name"],y=monthly_total["Amount"],
#                                     marker_color="rgba(99,102,241,0.7)",name="Spent",marker_line_width=0))
#             fig_mt.add_hline(y=current_salary,line_dash="dot",line_color="#10b981",
#                              annotation_text="Salary",annotation_font_color="#10b981")
#             fig_mt.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
#                                  margin=dict(t=20,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
#                                  yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_mt, use_container_width=True)
#         with mc2:
#             st.markdown("**Need / Want / Saving by Month**")
#             fig_mtype = px.bar(monthly_type,x="Month_Name",y="Amount",color="Type",
#                                color_discrete_map=TYPE_COLORS,barmode="stack")
#             fig_mtype.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
#                                     margin=dict(t=20,b=10,l=10,r=10),xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
#                                     yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_mtype, use_container_width=True)

#         st.divider()
#         mc3,mc4 = st.columns(2)
#         with mc3:
#             st.markdown("**Monthly Health Score**")
#             sc_colors = ["#10B981" if s>=7 else "#F59E0B" if s>=5 else "#EF4444" for s in monthly_total["Score"]]
#             fig_sc = go.Figure(go.Bar(x=monthly_total["Month_Name"],y=monthly_total["Score"],
#                                       marker_color=sc_colors,marker_line_width=0,
#                                       text=monthly_total["Score"],textposition="outside",textfont=dict(color="white",size=11)))
#             fig_sc.add_hline(y=7,line_dash="dash",line_color="#10B981",annotation_text="Good (7+)")
#             fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",
#                                  height=280,yaxis_range=[0,11],margin=dict(t=20,b=10,l=10,r=10),
#                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_sc, use_container_width=True)

#         # FIX 3: Replace heatmap with Top-5 Spending Days of Month chart
#         with mc4:
#             st.markdown("**Top Spending Days (Day of Month)**")
#             year_df["Day"] = year_df["Date"].dt.day
#             day_spend = year_df.groupby("Day")["Amount"].sum().reset_index().sort_values("Amount", ascending=False).head(10)
#             fig_days = px.bar(day_spend, x="Day", y="Amount",
#                               color="Amount", color_continuous_scale="Purples",
#                               text=day_spend["Amount"].apply(fmt_inr))
#             fig_days.update_traces(textposition="outside", textfont=dict(color="white", size=10))
#             fig_days.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
#                                    font_color="white", height=280, showlegend=False,
#                                    coloraxis_showscale=False,
#                                    xaxis=dict(title="Day of Month", gridcolor="rgba(255,255,255,0.05)", dtick=1),
#                                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
#                                    margin=dict(t=20,b=10,l=10,r=10))
#             st.plotly_chart(fig_days, use_container_width=True)

#         st.divider()
#         st.markdown("**Payment Mode Usage by Month**")
#         pm_month = year_df.groupby(["Month_Name","Payment Mode"])["Amount"].sum().reset_index()
#         month_order_map = {m:i for i,m in enumerate(MONTH_NAMES)}
#         pm_month = pm_month.sort_values("Month_Name", key=lambda x: x.map(month_order_map))
#         pm_colors_map = {"UPI":"#6366f1","Credit Card":"#ec4899","Debit Card":"#3b82f6","Cash":"#f59e0b","Bank Transfer":"#10b981"}

#         # Keep raw amounts pivot (for hover tooltip) and pct pivot (for bar height)
#         pm_raw   = pm_month.pivot_table(index="Month_Name", columns="Payment Mode", values="Amount", fill_value=0)
#         pm_raw   = pm_raw.reindex([m for m in MONTH_NAMES if m in pm_raw.index])
#         pm_pivot = pm_raw.div(pm_raw.sum(axis=1), axis=0) * 100   # % share

#         fig_pmm = go.Figure()
#         for pm, color in pm_colors_map.items():
#             if pm in pm_pivot.columns:
#                 raw_vals = pm_raw[pm] if pm in pm_raw.columns else [0]*len(pm_pivot)
#                 fig_pmm.add_trace(go.Bar(
#                     name=pm,
#                     x=pm_pivot.index,
#                     y=pm_pivot[pm].round(1),
#                     marker_color=color,
#                     marker_line_width=0,
#                     # Show % label inside bar only if segment wide enough
#                     text=pm_pivot[pm].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""),
#                     textposition="inside",
#                     textfont=dict(color="white", size=10, family="DM Sans"),
#                     # Pass actual ₹ amounts as custom data for the tooltip
#                     customdata=list(raw_vals),
#                     hovertemplate=(
#                         "<b>%{x}</b><br>"
#                         "Payment Mode: <b>" + pm + "</b><br>"
#                         "Amount: <b>₹%{customdata:,.0f}</b><br>"
#                         "Share: %{y:.1f}%"
#                         "<extra></extra>"
#                     )
#                 ))
#         fig_pmm.update_layout(
#             barmode="stack",
#             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
#             font_color="white", height=260,
#             hoverlabel=dict(bgcolor="#1e1e2e", font_size=13, font_family="DM Sans",
#                             bordercolor="rgba(255,255,255,0.15)"),
#             legend=dict(orientation="h", y=-0.22, x=0, font_size=11,
#                         bgcolor="rgba(0,0,0,0)", borderwidth=0),
#             margin=dict(t=10, b=60, l=10, r=10),
#             xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=11)),
#             yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%", range=[0,100],
#                        tickfont=dict(size=10))
#         )
#         st.plotly_chart(fig_pmm, use_container_width=True)

#         st.markdown("**Monthly Summary Table**")
#         mt2 = monthly_total.copy()
#         mt2["Spent"]       = mt2["Amount"].apply(fmt_inr)
#         mt2["Health Score"]= mt2["Score"].apply(lambda s: f"{'⭐'*int(s//2)} {s}/10")
#         st.dataframe(mt2[["Month_Name","Spent","Health Score"]].rename(columns={"Month_Name":"Month"}),
#                      use_container_width=True, hide_index=True)

# # ══════════════════════════════════════════════════════════════════════
# # TAB 5 — YEARLY CALENDAR
# # ══════════════════════════════════════════════════════════════════════
# with tab5:
#     st.markdown('<div class="section-header">🗓️ Yearly Calendar View</div>', unsafe_allow_html=True)
#     year_df2 = filter_data(sel_year, "All")
#     if year_df2.empty:
#         st.info("No data for selected year.")
#     else:
#         st.markdown("**📅 Monthly Spending Bars**")
#         daily_spend = year_df2.groupby(year_df2["Date"].dt.date)["Amount"].sum()
#         month_cols  = st.columns(4)
#         for mi, month_idx in enumerate(range(1,13)):
#             col = month_cols[mi%4]
#             with col:
#                 days_in_month = calendar.monthrange(sel_year, month_idx)[1]
#                 month_dates   = [date(sel_year, month_idx, d) for d in range(1, days_in_month+1)]
#                 month_amounts = [daily_spend.get(d, 0) for d in month_dates]
#                 total_month   = sum(month_amounts)
#                 st.markdown(f"**{MONTH_NAMES[month_idx-1]}** — {fmt_inr(total_month)}")
#                 if total_month > 0:
#                     fig_m = go.Figure(go.Bar(
#                         x=list(range(1,days_in_month+1)), y=month_amounts, marker_line_width=0,
#                         marker_color=["#EF4444" if a>current_salary/20 else "#F59E0B" if a>current_salary/30 else "#6366f1" if a>0 else "#1f2937" for a in month_amounts]))
#                     fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
#                                         font_color="white",height=100,showlegend=False,
#                                         margin=dict(t=0,b=0,l=0,r=0),
#                                         xaxis=dict(showgrid=False,showticklabels=False),
#                                         yaxis=dict(showgrid=False,showticklabels=False))
#                     st.plotly_chart(fig_m, use_container_width=True, key=f"mb_{month_idx}")
#                 else:
#                     st.caption("No data")

#         st.divider()
#         yc1,yc2 = st.columns(2)
#         with yc1:
#             monthly_agg = year_df2.groupby(year_df2["Date"].dt.month)["Amount"].sum().reset_index()
#             monthly_agg.columns = ["Month_Num","Amount"]
#             monthly_agg["Month"] = monthly_agg["Month_Num"].apply(lambda x: MONTH_NAMES[x-1])
#             fig_yl = go.Figure()
#             fig_yl.add_trace(go.Scatter(x=monthly_agg["Month"],y=monthly_agg["Amount"],
#                                         mode="lines+markers+text",line=dict(color="#6366f1",width=3),
#                                         marker=dict(size=8,color="#a78bfa"),
#                                         text=monthly_agg["Amount"].apply(fmt_inr),
#                                         textposition="top center",textfont=dict(color="white",size=10)))
#             fig_yl.add_hline(y=current_salary,line_dash="dot",line_color="#10b981",annotation_text="Monthly Salary")
#             fig_yl.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
#                                  font_color="white",height=300,title="Monthly Spend vs Salary",
#                                  margin=dict(t=30,b=10,l=10,r=10),
#                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_yl, use_container_width=True)
#         with yc2:
#             cum = year_df2.sort_values("Date").groupby("Date")["Amount"].sum().cumsum().reset_index()
#             fig_cum = go.Figure(go.Scatter(x=cum["Date"],y=cum["Amount"],mode="lines",fill="tozeroy",
#                                            line=dict(color="#8b5cf6",width=2),fillcolor="rgba(139,92,246,0.15)"))
#             fig_cum.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
#                                   font_color="white",height=300,title="Cumulative Annual Spending",
#                                   margin=dict(t=30,b=10,l=10,r=10),
#                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_cum, use_container_width=True)

# # ══════════════════════════════════════════════════════════════════════
# # TAB 6 — SETUP
# # ══════════════════════════════════════════════════════════════════════
# with tab6:
#     st.markdown('<div class="section-header">⚙️ Setup & Configuration</div>', unsafe_allow_html=True)
#     setup_df  = load_setup()
#     rules_df  = load_budget_rules()

#     st.markdown("### 🗓️ Monthly Budget Rules")
#     st.markdown('<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:14px;padding:16px 20px;margin-bottom:20px;"><span style="font-family:\'Space Grotesk\',sans-serif;font-size:14px;font-weight:600;color:#a78bfa;">💡 How it works</span><br><span style="font-size:13px;color:rgba(255,255,255,0.55);line-height:1.7;">Each <b>Year + Month</b> can have its own budget rule. New months <b>auto-inherit</b> the last saved rule. The <b>Yearly View</b> shows a weighted blend.</span></div>', unsafe_allow_html=True)

#     rb1,rb2,rb3 = st.columns([1,1,2])
#     with rb1: rule_year  = st.selectbox("Year",  sorted(setup_df["Year"].tolist()), key="rule_yr")
#     with rb2: rule_month = st.selectbox("Month", MONTH_NAMES, key="rule_mo", index=datetime.now().month-1)

#     def get_last_rule_local(year, month_name):
#         if rules_df.empty: return 50.0,30.0,20.0
#         mo_idx = MONTH_NAMES.index(month_name)
#         for i in range(mo_idx-1,-1,-1):
#             prev = rules_df[(rules_df["Year"]==year)&(rules_df["Month"]==MONTH_NAMES[i])]
#             if not prev.empty:
#                 r = prev.iloc[0]; return float(r["Needs_Pct"]),float(r["Wants_Pct"]),float(r["Savings_Pct"])
#         for y in sorted(rules_df["Year"].unique(),reverse=True):
#             if y < year:
#                 yr_r = rules_df[rules_df["Year"]==y]
#                 if not yr_r.empty: r=yr_r.iloc[-1]; return float(r["Needs_Pct"]),float(r["Wants_Pct"]),float(r["Savings_Pct"])
#         return 50.0,30.0,20.0

#     existing_rule = rules_df[(rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month)] if not rules_df.empty else pd.DataFrame()
#     if not existing_rule.empty:
#         r0=existing_rule.iloc[0]; pre_n,pre_w,pre_s=float(r0["Needs_Pct"]),float(r0["Wants_Pct"]),float(r0["Savings_Pct"]); rule_exists=True
#     else:
#         pre_n,pre_w,pre_s=get_last_rule_local(rule_year,rule_month); rule_exists=False

#     with rb3:
#         if rule_exists: st.markdown(f'<div class="budget-alert alert-success" style="margin-top:28px;">✅ Rule saved for {rule_month} {rule_year}: {pre_n:.0f}-{pre_w:.0f}-{pre_s:.0f}</div>', unsafe_allow_html=True)
#         else:           st.markdown(f'<div class="budget-alert alert-warning" style="margin-top:28px;">⚡ No rule for {rule_month} {rule_year} — pre-filled from last saved rule</div>', unsafe_allow_html=True)

#     sl_col,prev_col = st.columns([1.5,1])
#     with sl_col:
#         e_needs   = st.slider("🏠 Needs %",  10,80,int(pre_n),5,key="e_needs")
#         e_wants   = st.slider("🎉 Wants %",   5,70,int(pre_w),5,key="e_wants")
#         e_savings = max(0,100-e_needs-e_wants)
#         if e_needs+e_wants<=100: st.markdown(f'<div class="budget-alert alert-success">✅ Valid — Savings auto-set to <b>{e_savings}%</b> · Total=100%</div>', unsafe_allow_html=True)
#         else: st.markdown(f'<div class="budget-alert alert-danger">⚠️ Needs+Wants={e_needs+e_wants}% — exceeds 100%</div>', unsafe_allow_html=True)
#         bt1,bt2 = st.columns(2)
#         with bt1:
#             if st.button(f"💾 Save rule for {rule_month} {rule_year}", use_container_width=True):
#                 if e_needs+e_wants>100: st.error("Fix % split first")
#                 else:
#                     new_rule = pd.DataFrame([{"Year":rule_year,"Month":rule_month,"Needs_Pct":e_needs,"Wants_Pct":e_wants,"Savings_Pct":e_savings}])
#                     upd = rules_df[~((rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month))] if not rules_df.empty else pd.DataFrame(columns=["Year","Month","Needs_Pct","Wants_Pct","Savings_Pct"])
#                     save_budget_rules(pd.concat([upd,new_rule],ignore_index=True))
#                     st.success(f"✅ Saved {rule_month} {rule_year}: {e_needs}-{e_wants}-{e_savings}"); st.rerun()
#         with bt2:
#             if rule_exists and st.button(f"🗑️ Delete rule for {rule_month} {rule_year}", use_container_width=True):
#                 save_budget_rules(rules_df[~((rules_df["Year"]==rule_year)&(rules_df["Month"]==rule_month))])
#                 st.success("Rule deleted"); st.rerun()

#     with prev_col:
#         yr_sal = int(setup_df[setup_df["Year"]==rule_year]["Salary"].values[0]) if not setup_df[setup_df["Year"]==rule_year].empty else 50000
#         fig_pv = go.Figure(go.Pie(labels=[f"Needs {e_needs}%",f"Wants {e_wants}%",f"Savings {e_savings}%"],
#                                    values=[max(yr_sal*e_needs/100,1),max(yr_sal*e_wants/100,1),max(yr_sal*e_savings/100,1)],
#                                    hole=0.55,marker_colors=["#3B82F6","#F59E0B","#10B981"],textinfo="label+percent",textfont_size=11))
#         fig_pv.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=200,showlegend=False,
#                              margin=dict(t=10,b=10,l=10,r=10),annotations=[dict(text=fmt_inr(yr_sal),x=0.5,y=0.5,font_size=14,font_color="white",showarrow=False)])
#         st.plotly_chart(fig_pv, use_container_width=True, key="setup_pv")

#     st.divider()
#     st.markdown("### 📊 Yearly Budget Allocation Overview")
#     yr_rules = rules_df[rules_df["Year"]==rule_year].copy() if not rules_df.empty else pd.DataFrame()
#     if yr_rules.empty:
#         st.info(f"No monthly rules saved for {rule_year} yet.")
#     else:
#         yr_rules = yr_rules.sort_values("Month",key=lambda x: x.map({m:i for i,m in enumerate(MONTH_NAMES)}))
#         yb1,yb2 = st.columns([1.6,1])
#         with yb1:
#             fig_bl = go.Figure()
#             for name,col,key in [("🏠 Needs","#3B82F6","Needs_Pct"),("🎉 Wants","#F59E0B","Wants_Pct"),("🏦 Savings","#10B981","Savings_Pct")]:
#                 fig_bl.add_trace(go.Bar(name=name,x=yr_rules["Month"],y=yr_rules[key],marker_color=col,marker_line_width=0,
#                                         text=yr_rules[key].apply(lambda x:f"{x:.0f}%"),textposition="inside",textfont_color="white"))
#             fig_bl.update_layout(barmode="stack",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=300,
#                                  legend=dict(orientation="h",y=1.12),margin=dict(t=20,b=10,l=10,r=10),
#                                  yaxis=dict(range=[0,100],ticksuffix="%",gridcolor="rgba(255,255,255,0.05)"),
#                                  xaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
#             st.plotly_chart(fig_bl, use_container_width=True)
#         with yb2:
#             n_avg,w_avg,s_avg = yr_rules["Needs_Pct"].mean(),yr_rules["Wants_Pct"].mean(),yr_rules["Savings_Pct"].mean()
#             fig_av = go.Figure(go.Pie(labels=[f"Needs {n_avg:.1f}%",f"Wants {w_avg:.1f}%",f"Savings {s_avg:.1f}%"],
#                                       values=[n_avg,w_avg,s_avg],hole=0.5,marker_colors=["#3B82F6","#F59E0B","#10B981"],
#                                       textinfo="label+percent",textfont_size=11))
#             fig_av.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="white",height=240,showlegend=False,margin=dict(t=10,b=10,l=10,r=10))
#             st.plotly_chart(fig_av, use_container_width=True, key="yr_avg")
#         disp_r = yr_rules[["Month","Needs_Pct","Wants_Pct","Savings_Pct"]].copy()
#         disp_r.columns = ["Month","Needs %","Wants %","Savings %"]
#         disp_r["Rule"] = disp_r.apply(lambda r: f"{r['Needs %']:.0f}-{r['Wants %']:.0f}-{r['Savings %']:.0f}",axis=1)
#         st.dataframe(disp_r[["Month","Rule","Needs %","Wants %","Savings %"]],use_container_width=True,hide_index=True)

#     st.divider()
#     st.markdown("### 📅 Year-wise Salary & Weekly Limit")
#     with st.form("setup_form"):
#         edited_setup = st.data_editor(setup_df[["Year","Salary","Weekly_Limit"]],use_container_width=True,num_rows="dynamic",
#             column_config={"Year":st.column_config.NumberColumn("Year",format="%d"),
#                            "Salary":st.column_config.NumberColumn("Monthly Salary (₹)",format="₹%d"),
#                            "Weekly_Limit":st.column_config.NumberColumn("Weekly Limit (₹)",format="₹%d")},hide_index=True)
#         if st.form_submit_button("💾 Save Salary Table",use_container_width=True):
#             edited_setup["Needs"]=(edited_setup["Salary"]*0.5).astype(int)
#             edited_setup["Wants"]=(edited_setup["Salary"]*0.3).astype(int)
#             edited_setup["Savings"]=(edited_setup["Salary"]*0.2).astype(int)
#             save_setup(edited_setup); st.success("✅ Saved!"); st.rerun()

#     st.divider()
#     st.markdown("### 📂 Data Management")
#     dm1,dm2 = st.columns(2)
#     with dm1:
#         st.markdown("**📥 Export Data**")
#         ex1,ex2 = st.columns(2)
#         with ex1: exp_yr = st.selectbox("Export Year",  ["All Years"]+[str(y) for y in available_years()], key="exp_yr")
#         with ex2: exp_mo = st.selectbox("Export Month", ["All Months"]+MONTH_NAMES, key="exp_mo")
#         exp_df = load_all_years() if exp_yr=="All Years" else load_year(int(exp_yr))
#         if exp_mo != "All Months" and not exp_df.empty:
#             exp_df = exp_df[exp_df["Date"].dt.month==MONTH_NAMES.index(exp_mo)+1]
#         st.caption(f"{len(exp_df)} rows selected")
#         st.download_button("📥 Download CSV",data=exp_df.to_csv(index=False),file_name=f"expenses_{exp_yr}_{exp_mo}.csv",mime="text/csv",use_container_width=True)
#     with dm2:
#         st.markdown("**📤 Import CSV**")
#         uploaded = st.file_uploader("Upload expenses CSV",type="csv",key="import_csv")
#         if uploaded:
#             try:
#                 imp_df = pd.read_csv(uploaded,parse_dates=["Date"])
#                 st.caption(f"{len(imp_df)} rows in file")
#                 if st.button("✅ Confirm Import",use_container_width=True):
#                     for yr,grp in imp_df.groupby(imp_df["Date"].dt.year):
#                         existing = load_year(int(yr))
#                         save_year(pd.concat([existing,grp]).drop_duplicates().reset_index(drop=True),int(yr))
#                     st.success(f"Imported {len(imp_df)} rows!"); st.rerun()
#             except Exception as e: st.error(f"Error: {e}")

#     st.divider()
#     st.markdown("### 🗑️ Clear / Delete Data")
#     st.markdown('<div class="budget-alert alert-danger" style="margin-bottom:12px;">⚠️ Deleted data cannot be recovered. Export a backup first.</div>', unsafe_allow_html=True)
#     cl1,cl2,cl3 = st.columns(3)
#     with cl1:
#         del_scope = st.selectbox("Delete scope",["Select…","Specific Month","Full Year","All Data"],key="del_scope")
#     with cl2:
#         del_yr = st.selectbox("Year", [str(y) for y in available_years()], key="del_yr") if del_scope in ["Specific Month","Full Year"] else None
#         del_mo = st.selectbox("Month", MONTH_NAMES, key="del_mo") if del_scope=="Specific Month" else None
#     with cl3:
#         st.markdown("&nbsp;",unsafe_allow_html=True)
#         confirm_del = st.checkbox("☑️ I understand this is permanent",key="confirm_del")
#         if del_scope!="Select…" and st.button("🗑️ Delete Now",type="secondary",use_container_width=True):
#             if not confirm_del: st.error("Please tick the confirmation checkbox first.")
#             elif del_scope=="Specific Month" and del_yr and del_mo:
#                 delete_month_data(int(del_yr),MONTH_NAMES.index(del_mo)+1); st.success(f"✅ Deleted {del_mo} {del_yr}"); st.rerun()
#             elif del_scope=="Full Year" and del_yr:
#                 delete_year_data(int(del_yr)); st.success(f"✅ Deleted all data for {del_yr}"); st.rerun()
#             elif del_scope=="All Data":
#                 for y in available_years(): delete_year_data(y)
#                 st.success("✅ All expense data deleted."); st.rerun()
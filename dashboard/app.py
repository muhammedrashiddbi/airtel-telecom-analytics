import base64
import os
from contextlib import contextmanager
import sqlite3

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Airtel Revenue Dashboard", layout="wide", initial_sidebar_state="expanded")
DB_PATH = "airtel.db"  # change to your database file name
RED = "#E40000"

import base64

def set_background(path="C:\\Users\\muham\\Documents\\airtel-telecom-analytics\\dashboard\\bg.jpg"):
    if not os.path.exists(path):
        return
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    st.markdown(f"""<style>
    .stApp {{background: linear-gradient(rgba(0,0,0,.35), rgba(0,0,0,.35)),
             url(data:image/jpeg;base64,{b64}) center / cover no-repeat fixed;}}
    [data-testid="stSidebar"] {{background: rgba(0,0,0,.6);}}
    [data-testid="stVerticalBlockBorderWrapper"] {{background: rgba(0,0,0,.45); border-radius: 14px;}}
    .box {{background: rgba(0,0,0,.45);}}
    </style>""", unsafe_allow_html=True)

set_background()

def logo_html(h):
    if not os.path.exists("C:\\Users\\muham\\Documents\\airtel-telecom-analytics\\dashboard\\logo.jpg"):
        return "<span class='logo'>airtel</span>"
    b64 = base64.b64encode(open("C:\\Users\\muham\\Documents\\airtel-telecom-analytics\\dashboard\\logo.jpg", "rb").read()).decode()
    return f"<img src='data:image/jpeg;base64,{b64}' style='height:{h}px'>"

# ---------------------------------------------------------------- data
def demo_data():
    """Synthetic data with the same columns as the ER diagram (used only if no DB found)."""
    rng = np.random.default_rng(7)
    circles = pd.DataFrame({
        "circle_id": range(1, 9),
        "circle_name": ["Kerala", "Karnataka", "Delhi", "Mumbai", "Punjab", "Kolkata", "Tamil Nadu", "UP East"],
        "region": ["South", "South", "North", "West", "North", "East", "South", "North"]})
    plans = pd.DataFrame({
        "plan_id": range(1, 9),
        "plan_name": ["Smart 199", "Smart 299", "Unlimited 479", "Unlimited 719",
                      "Black 499", "Black 799", "Family 999", "Platinum 1499"],
        "plan_type": ["Prepaid"] * 4 + ["Postpaid"] * 4,
        "price_inr": [199, 299, 479, 719, 499, 799, 999, 1499]})
    n = 4000
    cust = pd.DataFrame({
        "customer_id": range(1, n + 1),
        "circle_id": rng.integers(1, 9, n),
        "current_plan_id": rng.integers(1, 9, n)})
    cust = cust.merge(plans[["plan_id", "plan_type"]], left_on="current_plan_id", right_on="plan_id")
    cust["connection_type"] = cust.pop("plan_type")
    cust["arpu_inr"] = cust["current_plan_id"].map(plans.set_index("plan_id")["price_inr"])
    cust["is_churned"] = rng.random(n) < 0.08
    rows = []
    for c in cust.itertuples():
        for m in range(6):
            if rng.random() < 0.8:
                rows.append((c.customer_id, pd.Timestamp(2025, 1 + m, int(rng.integers(1, 28))),
                             c.arpu_inr * (1 + 0.03 * m) * rng.uniform(0.8, 1.2), c.current_plan_id,
                             rng.choice(["App", "Retail", "UPI", "Website", "Partner"]),
                             rng.choice(["New", "Renewal", "Top-up"], p=[.15, .6, .25])))
    rech = pd.DataFrame(rows, columns=["customer_id", "recharge_date", "amount_inr", "plan_id", "channel", "txn_type"])
    rech.insert(0, "recharge_id", range(1, len(rech) + 1))
    return {"circles": circles, "plans": plans, "customers": cust, "recharges": rech}


@st.cache_data
def load():
    if os.path.exists(DB_PATH):
        con = sqlite3.connect(DB_PATH)
        t = {n: pd.read_sql(f"SELECT * FROM {n}", con) for n in ["circles", "plans", "customers", "recharges"]}
        con.close()
    else:
        t = demo_data()
    r = t["recharges"].copy()
    r["recharge_date"] = pd.to_datetime(r["recharge_date"])
    cu = t["customers"][["customer_id", "circle_id", "connection_type", "is_churned"]]
    r = r.merge(cu, on="customer_id").merge(t["circles"], on="circle_id", how="left")
    r = r.merge(t["plans"][["plan_id", "plan_name", "plan_type"]], on="plan_id", how="left")
    r["plan_type"] = r["plan_type"].fillna("Unknown")
    r["month"] = r["recharge_date"].dt.to_period("M").dt.to_timestamp()
    r["rev_m"] = r["amount_inr"] / 1e6
    return r, t["customers"]


rev, customers = load()


def set_background(path="background.jpg"):
    """Landscape background image + semi-transparent panels so text stays readable."""
    if not os.path.exists(path):
        return
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    st.markdown(f"""<style>
    .stApp {{background: linear-gradient(rgba(0,0,0,.35), rgba(0,0,0,.35)),
             url(data:image/jpeg;base64,{b64}) center / cover no-repeat fixed;}}
    [data-testid="stSidebar"] {{background: rgba(0,0,0,.6);}}
    [data-testid="stVerticalBlockBorderWrapper"] {{background: rgba(0,0,0,.45); border-radius: 14px;}}
    .box {{background: rgba(0,0,0,.45);}}
    </style>""", unsafe_allow_html=True)


set_background()

st.markdown("""<style>
footer {display:none}
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] {
    display:flex !important; visibility:visible !important; z-index:999999;}
.block-container {padding:0.5rem 1rem 0 1rem; max-width:100%}
[data-testid="stVerticalBlock"] {gap:0.35rem}
.box {border:2px solid rgba(128,128,128,.7); border-radius:14px; text-align:center}
.title {display:flex; align-items:center; gap:24px; padding:4px 24px; border-radius:30px}
.logo {color:#E40000; font-weight:800; font-size:26px; font-style:italic}
.title h2 {margin:0; font-size:24px; font-weight:500}
.banner {padding:5px; font-size:15px; margin-bottom:6px}
.cards {display:flex; gap:12px; margin-bottom:4px}
.card {flex:1; padding:6px 0}
.card .t {font-size:14px; opacity:.75} .card .v {font-size:28px; font-weight:700; line-height:1.2}
.card .s {font-size:12px; opacity:.75}
.ptitle {text-align:center; font-weight:600; font-size:15px; margin:0}
[data-testid="stSidebar"] .logo {font-size:34px; text-align:center; margin-top:40px}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Filters")
    conn = st.selectbox("Connection Type (Overview)", ["All"] + sorted(rev["connection_type"].dropna().unique()))
    reg = st.selectbox("Region", ["All"] + sorted(rev["region"].dropna().unique()))
    dmin, dmax = rev["recharge_date"].min().date(), rev["recharge_date"].max().date()
    dr = st.date_input("Date Range", (dmin, dmax), min_value=dmin, max_value=dmax)
    st.markdown(f"<div style='text-align:center;margin-top:30px'>{logo_html(120)}</div>", unsafe_allow_html=True)

if isinstance(dr, (tuple, list)) and len(dr) == 2:
    rev = rev[(rev["recharge_date"].dt.date >= dr[0]) & (rev["recharge_date"].dt.date <= dr[1])]
if rev.empty:
    st.warning("No data in this date range.")
    st.stop()

d_reg = rev if reg == "All" else rev[rev["region"] == reg]
d = d_reg if conn == "All" else d_reg[d_reg["connection_type"] == conn]

st.markdown(f"<div class='box title'>{logo_html(52)}"
            "<h2>Airtel Telecom Analytics - Domain B: Revenue</h2></div>", unsafe_allow_html=True)


def cards(items):
    html = "".join(f"<div class='box card'><div class='t'>{t}</div><div class='v'>{v}</div>"
                   f"<div class='s'>{s}</div></div>" for t, v, s in items)
    st.markdown(f"<div class='cards'>{html}</div>", unsafe_allow_html=True)


def banner(text):
    st.markdown(f"<div class='box banner'>{text}</div>", unsafe_allow_html=True)


def chf(df, col, label, key):
    """Dropdown placed inside each chart box; filters only that chart."""
    opts = [f"All {label}"] + sorted(df[col].dropna().astype(str).unique())
    pick = st.selectbox(label, opts, key=key, label_visibility="collapsed")
    return df if pick == opts[0] else df[df[col].astype(str) == pick]


@contextmanager
def box(col, title, df, fcol, flabel, key):
    col = st.container() if col is st else col
    with col, st.container(border=True):
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"<p class='ptitle' style='text-align:left;padding-top:6px'>{title}</p>", unsafe_allow_html=True)
        with c2:
            out = chf(df, fcol, flabel, key)
        yield out


def ok(x):
    if x.empty:
        st.info("No data for this filter.")
    return not x.empty


def draw(fig, h=170, legend=False):
    fig.update_layout(height=h, margin=dict(l=5, r=5, t=5, b=5), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(size=11), showlegend=legend,
                      legend=dict(orientation="h", y=1.18))
    st.plotly_chart(fig, use_container_width=True)


def monthly(df):
    return df.groupby("month", as_index=False)["rev_m"].sum().sort_values("month")


def trend_fig(m):
    f = go.Figure(go.Scatter(x=m["month"].dt.strftime("%b"), y=m["rev_m"], mode="lines+markers+text",
                             text=m["rev_m"].round(1), textposition="top center", fill="tozeroy",
                             line=dict(color=RED), fillcolor="rgba(228,0,0,0.12)"))
    f.update_layout(yaxis=dict(title="Revenue (₹M)", rangemode="tozero"))
    return f


def t5_pvalue(df):
    """One-tailed paired t-test: is later-period revenue per customer higher than earlier period?"""
    from scipy import stats
    p = df.pivot_table(index="customer_id", columns="month", values="amount_inr", aggfunc="sum").fillna(0)
    ms = sorted(p.columns)
    if len(ms) < 2 or len(p) < 3:
        return None
    h = len(ms) // 2
    return stats.ttest_rel(p[ms[h:]].mean(axis=1), p[ms[:h]].mean(axis=1), alternative="greater").pvalue



# approximate centre point of each Airtel circle (lat, lon) for the India map
COORDS = {
    "andhra pradesh": (15.9, 79.7), "assam": (26.2, 92.9), "bihar": (25.1, 85.3), "delhi": (28.6, 77.2),
    "gujarat": (22.3, 71.7), "haryana": (29.0, 76.1), "himachal pradesh": (31.9, 77.2),
    "jammu and kashmir": (33.8, 76.6), "j and k": (33.8, 76.6), "karnataka": (15.3, 75.7), "kerala": (10.5, 76.3),
    "kolkata": (22.6, 88.4), "madhya pradesh": (23.5, 78.0), "maharashtra": (19.5, 75.7), "mumbai": (19.1, 72.9),
    "north east": (26.0, 94.0), "odisha": (20.5, 84.5), "orissa": (20.5, 84.5), "punjab": (31.1, 75.3),
    "rajasthan": (26.6, 73.8), "tamil nadu": (11.1, 78.7), "chennai": (13.1, 80.3), "up east": (26.8, 82.2),
    "up west": (28.0, 78.5), "uttar pradesh": (26.8, 80.9), "west bengal": (23.0, 87.8), "telangana": (17.9, 79.1),
    "uttarakhand": (30.1, 79.3), "jharkhand": (23.6, 85.3), "chhattisgarh": (21.3, 81.6), "goa": (15.3, 74.1)}

tab1, tab2 = st.tabs(["Overview", "Detail"])

# ============================================================ OVERVIEW
with tab1:
    banner("This dashboard helps Head of Finance understand received revenue, revenue patterns and revenue comparisons.")
    if d.empty:
        st.warning("No data for this filter.")
    else:
        m = monthly(d)
        pv = t5_pvalue(d)
        arpu = d["amount_inr"].sum() / d["customer_id"].nunique() / max(len(m), 1)
        cards([("Total Revenue", f"₹{d['rev_m'].sum():,.1f}M", "Fixed period"),
               ("T5 Test Result", "n/a" if pv is None else f"p = {pv:.3f}",
                "one-tailed | Direction: " + ("increase" if pv is not None and pv < 0.05 else "no significant increase")),
               ("ARPU (per month)", f"₹{arpu:,.0f}", "Received revenue per subscriber")])

        with box(st, "Revenue Trend", d, "channel", "Channels", "f_trend") as x:
            if ok(x):
                draw(trend_fig(monthly(x)), 160)

        b1, b2 = st.columns(2)
        with box(b1, "Subscribers vs Revenue by Circle (Bubble)", d_reg, "connection_type", "Connection Types", "f_subs") as x:
            if ok(x):
                g = x.groupby("circle_name").agg(subs=("customer_id", "nunique"), rev=("rev_m", "sum")).reset_index()
                g["arpu"] = g["rev"] * 1e6 / g["subs"] / max(x["month"].nunique(), 1)
                f = px.scatter(g, x="subs", y="rev", size="arpu", hover_name="circle_name", text="circle_name",
                               size_max=22, color_discrete_sequence=[RED])
                f.update_traces(textposition="top center", textfont_size=9, marker=dict(opacity=0.8))
                f.update_layout(xaxis=dict(title="Subscribers"), yaxis=dict(title="Revenue (₹M)"))
                draw(f, 160)

        with box(b2, "Revenue Share by Decile (Pareto)", d, "channel", "Channels", "f_dec") as x:
            if ok(x):
                c = x.groupby("customer_id")["amount_inr"].sum().sort_values()
                dec = pd.qcut(c.rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)])
                sh = c.groupby(dec, observed=True).sum()
                sh = sh / sh.sum() * 100
                f = go.Figure([go.Bar(x=sh.index, y=sh.values, marker_color=RED, name="Share",
                                      text=sh.round(0).astype(int).astype(str) + "%"),
                               go.Scatter(x=sh.index, y=sh.cumsum().values, mode="lines+markers", yaxis="y2",
                                          line=dict(color="#aaa"), name="Cumulative")])
                f.update_layout(yaxis=dict(title="Revenue share (%)"),
                                yaxis2=dict(overlaying="y", side="right", range=[0, 100],
                                            tickvals=[0, 25, 50, 75, 100], title="Cumulative (%)"))
                draw(f, 160, True)

# ============================================================ DETAIL
with tab2:
    plan = st.selectbox("Plan:", sorted(rev["connection_type"].dropna().unique()), key="plan_sel")
    banner(f"{plan} Plan - Revenue Details")
    dp = d_reg[d_reg["connection_type"] == plan]
    if dp.empty:
        st.warning("No data for this filter.")
    else:
        mp = monthly(dp)
        cards([("Subscribers", f"{dp['customer_id'].nunique():,}", "(Selected Plan)"),
               ("Received Revenue", f"₹{dp['rev_m'].sum():,.1f}M", f"(Last {len(mp)} months)"),
               ("ARPU", f"₹{dp['amount_inr'].sum() / dp['customer_id'].nunique() / max(len(mp), 1):,.0f}", f"({plan})")])

        r1, r2 = st.columns(2)
        with box(r1, f"Revenue Trend - {plan}", dp, "circle_name", "Circles", "f_dtrend") as x:
            if ok(x):
                draw(trend_fig(monthly(x)), 120)

        with box(r2, "Revenue Flow: Plan Type to Channel (Sankey)", d_reg, "circle_name", "Circles", "f_dcmp") as x:
            if ok(x):
                sk = x.groupby(["connection_type", "channel"], as_index=False)["rev_m"].sum()
                nodes = list(sk["connection_type"].unique()) + list(sk["channel"].unique())
                ix = {n: i for i, n in enumerate(nodes)}
                f = go.Figure(go.Sankey(
                    node=dict(label=nodes, pad=10, thickness=14,
                              color=[RED if n == plan else "#888" for n in nodes]),
                    link=dict(source=sk["connection_type"].map(ix), target=sk["channel"].map(ix),
                              value=sk["rev_m"], color="rgba(228,0,0,0.3)")))
                draw(f, 120)

        r3, r4 = st.columns(2)
        with box(r3, f"{plan} Revenue by Plan (Treemap)", dp, "txn_type", "Txn Types", "f_dtree") as x:
            if ok(x):
                tr = x.groupby("plan_name", as_index=False)["rev_m"].sum()
                draw(px.treemap(tr, path=["plan_name"], values="rev_m",
                                color_discrete_sequence=[RED, "#B30000", "#FF4D4D"]), 130)

        with box(r4, f"{plan} Revenue by Circle (India Map)", dp, "channel", "Channels", "f_map") as x:
            if ok(x):
                g = x.groupby("circle_name").agg(rev=("rev_m", "sum"), subs=("customer_id", "nunique")).reset_index()
                g["arpu"] = g["rev"] * 1e6 / g["subs"] / max(x["month"].nunique(), 1)
                key = g["circle_name"].astype(str).str.lower().str.replace("&", "and").str.strip()
                g["lat"] = key.map(lambda k: COORDS.get(k, (None, None))[0])
                g["lon"] = key.map(lambda k: COORDS.get(k, (None, None))[1])
                miss = g[g["lat"].isna()]["circle_name"].tolist()
                g = g.dropna(subset=["lat"])
                if g.empty:
                    st.info("Circle names not found in the coordinate list.")
                else:
                    f = px.scatter_geo(g, lat="lat", lon="lon", size="rev", color="rev", hover_name="circle_name",
                                       color_continuous_scale="Reds", size_max=14,
                                       hover_data={"rev": ":.2f", "subs": True, "arpu": ":.0f",
                                                   "lat": False, "lon": False})
                    f.update_geos(scope="asia", lonaxis_range=[67, 98], lataxis_range=[6, 37], showcountries=True,
                                  countrycolor="#999", showland=True, landcolor="rgba(60,60,60,0.6)",
                                  showocean=False, bgcolor="rgba(0,0,0,0)")
                    f.update_layout(coloraxis_showscale=False)
                    draw(f, 150)
                    if miss:
                        st.caption("Not shown: " + ", ".join(map(str, miss)))

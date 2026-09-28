import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

from config import CSV_PATH, USE_MYSQL
from src.database import get_engine, read_sql, table_count
from src.analytics import (
    kpis, yearly_counts, magnitude_distribution, depth_distribution,
    top_countries, strongest, top_deep, regional_summary, yoy_growth,
    hour_counts, network_counts, quality_extremes, activity_zones,
    seismic_story
)

st.set_page_config(page_title="SeismoInsight", page_icon="🌍", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 80% 0%,rgba(91,76,255,.12),transparent 32%),#07111f;color:#f4f7fb}
[data-testid="stSidebar"]{background:#050c16;border-right:1px solid rgba(255,255,255,.08)}
.block-container{padding-top:2rem;max-width:1500px}
.hero{padding:24px 28px;border-radius:22px;background:linear-gradient(135deg,rgba(73,94,255,.18),rgba(29,220,213,.07));border:1px solid rgba(255,255,255,.08);margin-bottom:20px}
.insight{border-left:4px solid #8b6cff;background:#0c1829;padding:13px 16px;border-radius:8px;margin-bottom:8px}
.warning{border-left:4px solid #ffae57;background:#211a0e;padding:13px 16px;border-radius:8px}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=900)
def load_csv_data():
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    for col in ["time", "updated"]:
        if col in df:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df

@st.cache_resource
def mysql_engine():
    return get_engine()

@st.cache_data(ttl=900)
def load_mysql_data():
    return read_sql(mysql_engine(), "SELECT * FROM earthquakes ORDER BY time DESC")

def get_data():
    if USE_MYSQL:
        try:
            engine = mysql_engine()
            if table_count(engine) > 0:
                return load_mysql_data(), "MySQL"
        except Exception:
            pass
    return load_csv_data(), "CSV"

def apply_filters(df):
    if df.empty:
        return df
    st.sidebar.markdown("### Global Filters")

    years = sorted(df["year"].dropna().unique().astype(int))
    if years:
        yr = st.sidebar.slider("Year range", min(years), max(years), (min(years), max(years)))
        df = df[df["year"].between(yr[0], yr[1])]

    if df["mag"].notna().any() and df["mag"].min() < df["mag"].max():
        lo, hi = st.sidebar.slider(
            "Magnitude",
            float(df["mag"].min()), float(df["mag"].max()),
            (float(df["mag"].min()), float(df["mag"].max())), step=0.1
        )
        df = df[df["mag"].between(lo, hi)]

    countries = sorted([x for x in df["country"].dropna().unique() if x != "Unknown"])
    selected = st.sidebar.multiselect("Countries", countries)
    if selected:
        df = df[df["country"].isin(selected)]

    depths = st.sidebar.multiselect("Depth category", ["Shallow","Moderate","Intermediate","Deep"])
    if depths:
        df = df[df["depth_category"].isin(depths)]

    tsunami = st.sidebar.radio("Tsunami indicator", ["All","Yes","No"])
    if tsunami == "Yes":
        df = df[df["tsunami"] == 1]
    elif tsunami == "No":
        df = df[df["tsunami"] == 0]

    return df

def plot_map(df, height=620):
    d = df.dropna(subset=["latitude","longitude","mag"]).copy()
    if len(d) > 15000:
        d = d.nlargest(15000, "mag")

    fig = px.scatter_geo(
        d, lat="latitude", lon="longitude", color="mag", size="mag",
        hover_name="place",
        hover_data={"mag":":.1f","depth_km":":.1f","country":True,"tsunami":True,
                    "status":True,"quality_score":":.1f","latitude":False,"longitude":False},
        color_continuous_scale=["#35a7ff","#ffd54f","#ff7a45","#ff3d5a"],
        projection="natural earth"
    )
    fig.update_geos(bgcolor="#07111f", landcolor="#18273a", oceancolor="#07111f",
                    showocean=True, showcountries=True, countrycolor="#31435c")
    fig.update_layout(height=height, margin=dict(l=0,r=0,t=0,b=0),
                      paper_bgcolor="#0d1a2b", plot_bgcolor="#0d1a2b",
                      font_color="#f4f7fb", coloraxis_colorbar_title="Magnitude")
    return fig

def style_fig(fig):
    fig.update_layout(paper_bgcolor="#0d1a2b", plot_bgcolor="#0d1a2b",
                      font_color="#f4f7fb", margin=dict(l=10,r=10,t=50,b=10))
    return fig

df, source = get_data()

with st.sidebar:
    st.markdown("# 🌍 SeismoInsight")
    st.caption("Global Seismic Intelligence")
    st.divider()
    page = st.radio("Navigate", [
        "Dashboard","Global Map","Trends & Analysis","Seismic Activity Zones",
        "Earthquake Explorer","Regional Comparison","Data Quality","Reports"
    ])
    st.divider()
    if st.button("↻ Refresh Data", use_container_width=True):
        load_csv_data.clear()
        load_mysql_data.clear()
        st.rerun()
    st.caption("Source: USGS Earthquake API")
    st.caption("Analytics only — not an emergency warning system.")

st.markdown("""
<div class="hero">
<h1 style="margin:0">Global Seismic Trends</h1>
<p style="font-size:1.1rem;margin:6px 0 0;color:#b6c4d8">
SeismoInsight — explore earthquake activity, patterns, depth, magnitude and measurement quality.
</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("No processed dataset found.")
    st.info("Run `python scripts/fetch_data.py --years 5 --min-magnitude 2.5` or `python scripts/generate_demo_data.py`.")
    st.stop()

filtered = apply_filters(df)
k = kpis(filtered)
st.caption(f"Data source: **{source}** · {len(filtered):,} events in current selection")

if page == "Dashboard":
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Events", f"{k['events']:,}")
    c2.metric("Highest Magnitude", f"{k['max_mag']:.1f}" if k["max_mag"] else "—")
    c3.metric("Average Magnitude", f"{k['avg_mag']:.2f}" if k["avg_mag"] else "—")
    c4.metric("Tsunami Events", f"{k['tsunami_events']:,}")
    c5.metric("Countries", f"{k['countries']:,}")

    st.markdown("### 🌎 Global Earthquake Activity")
    st.plotly_chart(plot_map(filtered), use_container_width=True)

    a,b = st.columns([1.4,1])
    with a:
        st.plotly_chart(style_fig(px.line(yearly_counts(filtered), x="year", y="events", markers=True,
                                          title="Earthquake Activity by Year")), use_container_width=True)
    with b:
        st.plotly_chart(style_fig(px.pie(magnitude_distribution(filtered), names="category", values="events",
                                         hole=.58, title="Magnitude Distribution")), use_container_width=True)

    a,b,c = st.columns(3)
    with a:
        st.plotly_chart(style_fig(px.bar(depth_distribution(filtered), x="category", y="events",
                                         title="Depth Profile")), use_container_width=True)
    with b:
        countries = top_countries(filtered,7)
        st.plotly_chart(style_fig(px.bar(countries.sort_values("events"), x="events", y="country",
                                         orientation="h", title="Most Active Countries")), use_container_width=True)
    with c:
        st.markdown("### 🔎 Seismic Story")
        for fact in seismic_story(filtered):
            st.markdown(f'<div class="insight">{fact}</div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Recent Major Events")
    st.dataframe(filtered.sort_values("time", ascending=False).head(8)[
        ["time","mag","depth_km","place","tsunami","status","quality_score"]
    ], use_container_width=True, hide_index=True)

elif page == "Global Map":
    st.markdown("## 🌎 Global Map")
    st.plotly_chart(plot_map(filtered,720), use_container_width=True)
    st.info("Hover over events to inspect magnitude, depth, country, tsunami indicator, status and measurement quality.")
    st.dataframe(filtered.sort_values("time", ascending=False).head(1000)[
        ["id","time","mag","depth_km","latitude","longitude","country","tsunami","quality_score"]
    ], use_container_width=True, hide_index=True)

elif page == "Trends & Analysis":
    st.markdown("## 📈 Trends & Analysis")
    tabs = st.tabs(["Frequency","Magnitude","Depth","Time","Tsunami","Networks"])

    with tabs[0]:
        y = yearly_counts(filtered)
        st.plotly_chart(style_fig(px.line(y,x="year",y="events",markers=True,title="Yearly Earthquake Frequency")), use_container_width=True)
        st.dataframe(y, use_container_width=True, hide_index=True)
        st.plotly_chart(style_fig(px.line(yoy_growth(filtered),x="year",y="yoy_growth_pct",markers=True,title="Year-over-Year Growth (%)")), use_container_width=True)

    with tabs[1]:
        st.plotly_chart(style_fig(px.bar(magnitude_distribution(filtered),x="category",y="events",title="Magnitude Categories")), use_container_width=True)
        st.markdown("### Top 10 Strongest Earthquakes")
        st.dataframe(strongest(filtered),use_container_width=True,hide_index=True)

    with tabs[2]:
        st.plotly_chart(style_fig(px.bar(depth_distribution(filtered),x="category",y="events",title="Depth Categories")), use_container_width=True)
        st.markdown("### Top 10 Deepest Events")
        st.dataframe(top_deep(filtered),use_container_width=True,hide_index=True)

    with tabs[3]:
        h=hour_counts(filtered)
        st.plotly_chart(style_fig(px.area(h,x="hour",y="events",title="Events by Hour of Day")),use_container_width=True)
        dow=filtered["day_of_week"].value_counts().rename_axis("day").reset_index(name="events")
        st.plotly_chart(style_fig(px.bar(dow,x="day",y="events",title="Events by Day of Week")),use_container_width=True)

    with tabs[4]:
        ts=filtered.groupby("year",as_index=False)["tsunami"].sum().rename(columns={"tsunami":"tsunami_events"})
        st.plotly_chart(style_fig(px.line(ts,x="year",y="tsunami_events",markers=True,title="Tsunami-Flagged Events by Year")),use_container_width=True)

    with tabs[5]:
        net=network_counts(filtered,15)
        st.plotly_chart(style_fig(px.bar(net.sort_values("events"),x="events",y="network",orientation="h",title="Reporting Networks")),use_container_width=True)

elif page == "Seismic Activity Zones":
    st.markdown("## 🗺️ Seismic Activity Zones")
    st.markdown('<div class="warning"><b>Interpretation:</b> Historical observed-activity categories derived from event frequency and average magnitude. Not official hazard maps or predictions.</div>', unsafe_allow_html=True)
    zones=activity_zones(filtered)
    if zones.empty:
        st.info("No country-level activity data available.")
    else:
        counts=zones["activity_zone"].value_counts().reindex(
            ["High Activity","Moderate Activity","Lower Observed Activity"],fill_value=0)
        a,b,c=st.columns(3)
        a.metric("High Activity Regions",int(counts["High Activity"]))
        b.metric("Moderate Activity Regions",int(counts["Moderate Activity"]))
        c.metric("Lower Observed Activity",int(counts["Lower Observed Activity"]))
        fig=px.scatter(zones.head(100),x="events",y="avg_magnitude",size="events",
                       color="activity_zone",hover_name="country",
                       title="Observed Activity: Frequency vs Average Magnitude")
        st.plotly_chart(style_fig(fig),use_container_width=True)
        st.dataframe(zones[["country","events","avg_magnitude","avg_depth_km",
                            "tsunami_events","activity_index","activity_zone"]].head(100),
                     use_container_width=True,hide_index=True)

elif page == "Earthquake Explorer":
    st.markdown("## 🔎 Earthquake Explorer")
    search=st.text_input("Search by earthquake ID, place, country or network")
    result=filtered.copy()
    if search:
        q=search.lower().strip()
        mask=(result["id"].fillna("").astype(str).str.lower().str.contains(q,regex=False) |
              result["place"].fillna("").astype(str).str.lower().str.contains(q,regex=False) |
              result["country"].fillna("").astype(str).str.lower().str.contains(q,regex=False) |
              result["net"].fillna("").astype(str).str.lower().str.contains(q,regex=False))
        result=result[mask]
    st.caption(f"{len(result):,} matching events")
    st.dataframe(result.sort_values("time",ascending=False).head(2000)[
        ["id","time","mag","depth_km","place","country","tsunami","status","quality_score"]
    ],use_container_width=True,hide_index=True)

    event_id=st.text_input("Enter an event ID for full detail")
    if event_id:
        match=result[result["id"].astype(str)==event_id]
        if match.empty:
            st.warning("Event ID not found in the current filtered dataset.")
        else:
            event=match.iloc[0]
            a,b,c,d=st.columns(4)
            a.metric("Magnitude",f"{event['mag']:.1f}")
            b.metric("Depth",f"{event['depth_km']:.1f} km")
            c.metric("Quality",f"{event['quality_score']:.1f}%")
            d.metric("Tsunami","Yes" if event["tsunami"]==1 else "No")
            st.markdown(f"**Location:** {event['place']}")
            detail_cols=["id","time","updated","latitude","longitude","magType","status","sig",
                         "net","nst","dmin","rms","gap","magError","depthError","magNst",
                         "locationSource","magSource","types","sources","type"]
            st.dataframe(pd.DataFrame({"Field":detail_cols,"Value":[event.get(c) for c in detail_cols]}),
                         use_container_width=True,hide_index=True)

elif page == "Regional Comparison":
    st.markdown("## 🌐 Regional Comparison")
    countries=sorted([x for x in filtered["country"].dropna().unique() if x!="Unknown"])
    selected=st.multiselect("Choose 2–5 countries",countries,default=countries[:2] if len(countries)>=2 else countries)
    if len(selected)<2:
        st.info("Select at least two countries.")
    else:
        reg=regional_summary(filtered)
        reg=reg[reg["country"].isin(selected)]
        st.dataframe(reg[["country","events","avg_magnitude","avg_depth_km",
                          "tsunami_events","max_magnitude","avg_quality"]],
                     use_container_width=True,hide_index=True)
        a,b=st.columns(2)
        with a:
            st.plotly_chart(style_fig(px.bar(reg,x="country",y="events",title="Event Frequency")),use_container_width=True)
        with b:
            st.plotly_chart(style_fig(px.bar(reg,x="country",y="avg_magnitude",title="Average Magnitude")),use_container_width=True)
        st.plotly_chart(style_fig(px.bar(reg,x="country",y="avg_depth_km",title="Average Depth (km)")),use_container_width=True)

elif page == "Data Quality":
    st.markdown("## 🧪 Data Quality Center")
    a,b,c,d=st.columns(4)
    a.metric("Average Quality Index",f"{filtered['quality_score'].mean():.1f}%")
    b.metric("Avg Station Count",f"{filtered['nst'].mean():.1f}")
    c.metric("Avg RMS",f"{filtered['rms'].mean():.2f}")
    d.metric("Avg Gap",f"{filtered['gap'].mean():.1f}°")
    st.plotly_chart(style_fig(px.histogram(filtered,x="quality_score",nbins=30,title="Measurement Quality Distribution")),use_container_width=True)
    st.markdown("### Lowest Quality Events")
    st.dataframe(quality_extremes(filtered,30),use_container_width=True,hide_index=True)

elif page == "Reports":
    st.markdown("## 📄 Seismic Intelligence Report")
    lines=[
        "# SeismoInsight — Seismic Intelligence Report",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
        f"Events in selection: {len(filtered):,}",
        "",
        "## Executive Summary",
    ]
    lines += [f"- {x}" for x in seismic_story(filtered)]
    lines += ["","## Strongest Events"]
    for _,row in strongest(filtered,10).iterrows():
        lines.append(f"- M{row['mag']:.1f} | {row['place']} | Depth {row['depth_km']:.1f} km | {row['time']}")
    lines += ["","## Top Countries"]
    for _,row in top_countries(filtered,10).iterrows():
        lines.append(f"- {row['country']}: {int(row['events']):,} events; average magnitude {row['avg_magnitude']:.2f}")
    report="\n".join(lines)
    st.text_area("Report preview",report,height=500)
    st.download_button("⬇ Download Report",report,"seismoinsight_report.md","text/markdown",use_container_width=True)
    st.download_button("⬇ Download Filtered Dataset",filtered.to_csv(index=False).encode("utf-8"),
                       "seismoinsight_filtered_events.csv","text/csv",use_container_width=True)

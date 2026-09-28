import numpy as np
import pandas as pd


def kpis(df):
    if df.empty:
        return {"events": 0, "max_mag": None, "avg_mag": None, "tsunami_events": 0, "countries": 0, "deep_events": 0}
    return {
        "events": len(df),
        "max_mag": float(df["mag"].max()),
        "avg_mag": float(df["mag"].mean()),
        "tsunami_events": int(df["tsunami"].sum()),
        "countries": int(df.loc[df["country"] != "Unknown", "country"].nunique()),
        "deep_events": int(df["deep_focus_flag"].sum()),
    }


def yearly_counts(df):
    return df.groupby("year", as_index=False).size().rename(columns={"size": "events"}).sort_values("year")


def magnitude_distribution(df):
    order = ["Minor (<4)", "Light (4–4.9)", "Moderate (5–5.9)", "Strong (6–6.9)", "Major (7+)"]
    return df["magnitude_category"].value_counts().reindex(order, fill_value=0).rename_axis("category").reset_index(name="events")


def depth_distribution(df):
    order = ["Shallow", "Moderate", "Intermediate", "Deep"]
    return df["depth_category"].value_counts().reindex(order, fill_value=0).rename_axis("category").reset_index(name="events")


def top_countries(df, n=10):
    return (
        df[df["country"] != "Unknown"]
        .groupby("country")
        .agg(events=("id", "count"), avg_magnitude=("mag", "mean"))
        .sort_values("events", ascending=False).head(n).reset_index()
    )


def strongest(df, n=10):
    cols = ["id", "time", "place", "mag", "depth_km", "tsunami", "status", "quality_score"]
    return df.sort_values("mag", ascending=False)[cols].head(n)


def top_deep(df, n=10):
    cols = ["id", "time", "place", "mag", "depth_km", "status", "quality_score"]
    return df.sort_values("depth_km", ascending=False)[cols].head(n)


def regional_summary(df):
    return (
        df[df["country"] != "Unknown"]
        .groupby("country")
        .agg(
            events=("id", "count"),
            avg_magnitude=("mag", "mean"),
            avg_depth_km=("depth_km", "mean"),
            tsunami_events=("tsunami", "sum"),
            max_magnitude=("mag", "max"),
            avg_quality=("quality_score", "mean"),
        )
        .reset_index().sort_values("events", ascending=False)
    )


def yoy_growth(df):
    y = yearly_counts(df).copy()
    y["yoy_growth_pct"] = y["events"].pct_change() * 100
    return y


def hour_counts(df):
    return df.groupby("hour", as_index=False).size().rename(columns={"size": "events"}).sort_values("hour")


def network_counts(df, n=10):
    return df["net"].fillna("unknown").value_counts().head(n).rename_axis("network").reset_index(name="events")


def quality_extremes(df, n=10):
    cols = ["id", "time", "place", "mag", "gap", "rms", "nst", "magError", "depthError", "quality_score"]
    return df.sort_values("quality_score", ascending=True)[cols].head(n)


def activity_zones(df):
    region = regional_summary(df)
    if region.empty:
        return region

    region["frequency_score"] = region["events"].rank(pct=True)
    region["magnitude_score"] = region["avg_magnitude"].rank(pct=True)
    region["activity_index"] = 0.65 * region["frequency_score"] + 0.35 * region["magnitude_score"]

    region["activity_zone"] = pd.cut(
        region["activity_index"],
        bins=[-np.inf, 0.33, 0.66, np.inf],
        labels=["Lower Observed Activity", "Moderate Activity", "High Activity"]
    )
    return region.sort_values("activity_index", ascending=False)


def seismic_story(df):
    if df.empty:
        return ["No earthquake records match the current filters."]

    facts = []
    years = yearly_counts(df)
    countries = top_countries(df, 1)
    strongest_event = df.loc[df["mag"].idxmax()]
    tsunami_pct = df["tsunami"].mean() * 100
    deep_pct = df["deep_focus_flag"].mean() * 100

    if len(years) >= 2:
        first = years.iloc[0]["events"]
        last = years.iloc[-1]["events"]
        if first:
            growth = (last - first) / first * 100
            direction = "increased" if growth >= 0 else "decreased"
            facts.append(f"Observed event count {direction} by {abs(growth):.1f}% between {int(years.iloc[0]['year'])} and {int(years.iloc[-1]['year'])}.")

    if not countries.empty:
        facts.append(f"{countries.iloc[0]['country']} has the highest observed event count in the current selection, with {int(countries.iloc[0]['events']):,} events.")

    facts.append(f"The strongest observed event has magnitude {strongest_event['mag']:.1f} near {strongest_event['place']}.")
    facts.append(f"{tsunami_pct:.2f}% of selected events have the USGS tsunami indicator set to 1.")
    facts.append(f"{deep_pct:.2f}% of selected events are deeper than 300 km.")
    return facts

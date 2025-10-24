from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from datetime import datetime, timedelta

def _palette(mode: str):
    if str(mode).lower() == "light":
        return {
            "fig": "#ffffff",
            "axes": "#ffffff",
            "grid": (0, 0, 0, 0.10),
            "label": "#0f172a",
            "line": "#7C5CFF",
            "happy": "#22c55e",
            "neutral": "#64748b",
            "sad": "#ef4444",
            "markeredge": "#ffffff",
        }
    return {
        "fig": "#0f1422",
        "axes": "#151B2B",
        "grid": (1, 1, 1, 0.18),
        "label": "#E6E9F2",
        "line": "#9b7bff",
        "happy": "#34d399",
        "neutral": "#9aa3b2",
        "sad": "#fb7185",
        "markeredge": "#0f1422",
    }

def mood_line_chart(df: pd.DataFrame, mode: str = "dark") -> Figure | None:
    if df is None or df.empty:
        return None
    df = df.sort_values("timestamp")
    P = _palette(mode)
    fig = plt.Figure(figsize=(8.8, 4.8), dpi=120)
    fig.patch.set_facecolor(P["fig"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(P["axes"])

    ax.plot(df["timestamp"], df["mood"], marker="o", linewidth=2.4, color=P["line"],
            markerfacecolor=P["line"], markeredgecolor=P["markeredge"])
    ax.set_ylim(0.8, 5.2)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Mood (1–5)", color=P["label"])
    ax.set_title("Mood over time", color=P["label"])
    ax.tick_params(colors=P["label"])
    for spine in ax.spines.values():
        spine.set_color(P["label"])
    ax.grid(True, linestyle=":", color=P["grid"])
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

def weekly_mood_bar(df: pd.DataFrame, mode: str = "dark") -> Figure | None:
    """Grouped bars by weekday: Happy (4–5), Neutral (3), Sad (1–2). Uses current week (Mon–Sun)."""
    from datetime import date
    P = _palette(mode)
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    if df is None or df.empty:
        wk = [start + timedelta(days=i) for i in range(7)]
        counts = {"Happy": [0]*7, "Neutral": [0]*7, "Sad": [0]*7}
    else:
        d = df.copy()
        d["date"] = pd.to_datetime(d["timestamp"], errors="coerce").dt.date
        d = d[(d["date"] >= start) & (d["date"] <= end)]
        d["bin"] = d["mood"].apply(lambda m: "Happy" if m >= 4 else ("Neutral" if m == 3 else "Sad"))
        wk = [start + timedelta(days=i) for i in range(7)]
        counts = {"Happy": [], "Neutral": [], "Sad": []}
        for day in wk:
            day_df = d[d["date"] == day]
            counts["Happy"].append((day_df["bin"] == "Happy").sum())
            counts["Neutral"].append((day_df["bin"] == "Neutral").sum())
            counts["Sad"].append((day_df["bin"] == "Sad").sum())

    import numpy as np
    x = np.arange(7); width = 0.25

    fig = plt.Figure(figsize=(9.5, 3.8), dpi=120)
    fig.patch.set_facecolor(P["fig"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(P["axes"])

    ax.bar(x - width, counts["Happy"], width, label="Happy", color=P["happy"])
    ax.bar(x,         counts["Neutral"], width, label="Neutral", color=P["neutral"])
    ax.bar(x + width, counts["Sad"], width, label="Sad", color=P["sad"])

    ax.set_xticks(x)
    ax.set_xticklabels([d.strftime("%a") for d in wk], color=P["label"])
    ax.set_ylabel("Count", color=P["label"])
    ax.set_title("Your Week", color=P["label"])
    ax.tick_params(colors=P["label"])
    for spine in ax.spines.values():
        spine.set_color(P["label"])
    ax.grid(True, linestyle=":", axis="y", color=P["grid"])
    ax.legend(frameon=False, labelcolor=P["label"])
    fig.tight_layout()
    return fig

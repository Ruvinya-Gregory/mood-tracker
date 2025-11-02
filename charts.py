from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from datetime import datetime, timedelta, date
import numpy as np


def _palette(mode: str):
    if str(mode).lower() == "light":
        return {
            "fig": "#ffffff",
            "axes": "#ffffff",
            "grid": (0, 0, 0, 0.10),
            "label": "#0f172a",
            "line": "#7C5CFF",
            "happy": "#16a34a",
            "neutral": "#475569",
            "sad": "#e11d48",
            "markeredge": "#ffffff",
        }
    return {
        "fig": "#0f1422",
        "axes": "#151B2B",
        "grid": (1, 1, 1, 0.18),
        "label": "#E6E9F2",
        "line": "#9b7bff",
        "happy": "#22c55e",
        "neutral": "#94a3b8",
        "sad": "#fb7185",
        "markeredge": "#0f1422",
    }


def mood_line_chart(df: pd.DataFrame, mode: str = "dark") -> Figure | None:
    if df is None or df.empty:
        return None
    tmp = df.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp = tmp.dropna(subset=["timestamp"]).sort_values("timestamp")
    P = _palette(mode)

    fig = plt.Figure(figsize=(8.8, 4.8), dpi=120)
    fig.patch.set_facecolor(P["fig"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(P["axes"])

    ax.plot(tmp["timestamp"], tmp["mood"], marker="o", linewidth=2.4, color=P["line"],
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
    """
    Grouped bars by weekday for the current week (Mon–Sun).
    Bins: Happy (4–5), Neutral (3), Sad (1–2).
    """
    P = _palette(mode)
    today: date = date.today()
    start = today - timedelta(days=today.weekday())   
    end = start + timedelta(days=6)                   

    wk = [start + timedelta(days=i) for i in range(7)]
    x = np.arange(7)
    width = 0.25

    fig = plt.Figure(figsize=(9.5, 3.8), dpi=120)
    fig.patch.set_facecolor(P["fig"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(P["axes"])

    if df is None or df.empty:
        counts = {"Happy": [0]*7, "Neutral": [0]*7, "Sad": [0]*7}
    else:
        tmp = df.copy()
        tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
        tmp = tmp.dropna(subset=["timestamp"])
        tmp["date"] = tmp["timestamp"].dt.date


        tmp = tmp[(tmp["timestamp"] >= pd.Timestamp(start)) &
              (tmp["timestamp"] <= pd.Timestamp(end) + pd.Timedelta(days=1))]

        tmp["mood"] = pd.to_numeric(tmp["mood"], errors="coerce").fillna(3).astype(int)


        # Bin
        def mood_bin(m: int) -> str:
            if m <= 2:
                return "Sad"
            if m == 3:
                return "Neutral"
            return "Happy"

        tmp["bin"] = tmp["mood"].map(mood_bin)

        counts = {"Happy": [], "Neutral": [], "Sad": []}
        for day in wk:
            day_df = tmp[tmp["date"] == day]
            counts["Happy"].append(int((day_df["bin"] == "Happy").sum()))
            counts["Neutral"].append(int((day_df["bin"] == "Neutral").sum()))
            counts["Sad"].append(int((day_df["bin"] == "Sad").sum()))

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

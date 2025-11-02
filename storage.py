"""
storage.py — CSV data layer (robust timestamp parsing)
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

COLUMNS = ["timestamp", "mood", "note", "tags"]


def ensure_data_store(csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(csv_path, index=False)


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    ensure_data_store(csv_path)
    df = pd.read_csv(csv_path)
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    df["mood"] = pd.to_numeric(df.get("mood"), errors="coerce")

    def parse_tags(x):
        if pd.isna(x) or x == "":
            return []
        try:
            return json.loads(x)
        except Exception:
            return [t.strip() for t in str(x).split(";") if t.strip()]

    df["tags"] = df.get("tags", pd.Series([], dtype="object")).apply(parse_tags)
    return df


def append_entry(csv_path: Path, mood: int, note: str = "", tags: list[str] | None = None) -> None:
    ensure_data_store(csv_path)
    tags = tags or []

    ts = datetime.now().replace(microsecond=0).isoformat() 
    row = {
        "timestamp": ts,
        "mood": int(mood),
        "note": (note or "").strip(),
        "tags": json.dumps(tags, ensure_ascii=False),
    }
    df = load_dataframe(csv_path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(csv_path, index=False)

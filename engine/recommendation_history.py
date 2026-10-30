
from datetime import datetime
from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = PROJECT_ROOT / "reports"
HISTORY_FILE = HISTORY_DIR / "recommendation_history.json"


def save_recommendations(recommendations, context=None):
    """Append a recommendation run to persistent JSON history."""

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    history = []

    if HISTORY_FILE.exists():
        try:
            with HISTORY_FILE.open("r", encoding="utf-8") as file:
                history = json.load(file)

            if not isinstance(history, list):
                history = []

        except (json.JSONDecodeError, OSError):
            history = []

    run = {
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "context": context or {},
        "recommendations": recommendations,
    }

    history.append(run)

    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, indent=2, ensure_ascii=False)

    return run


def load_history():
    """Load previous recommendation runs."""

    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            history = json.load(file)

        return history if isinstance(history, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def history_to_dataframe():
    """Convert recommendation history into a flat table."""

    records = []

    for run in load_history():
        for recommendation in run.get("recommendations", []):
            records.append({
                "Run ID": run.get("run_id", ""),
                "Generated At": run.get("generated_at", ""),
                "Priority": recommendation.get("priority", ""),
                "Category": recommendation.get("category", ""),
                "Finding": recommendation.get("finding", ""),
                "Suggested Action": recommendation.get("action", ""),
            })

    return pd.DataFrame(
        records,
        columns=[
            "Run ID",
            "Generated At",
            "Priority",
            "Category",
            "Finding",
            "Suggested Action",
        ],
    )


def compare_latest_runs():
    """Compare recommendation categories in the two latest runs."""

    history = load_history()

    if len(history) < 2:
        return {
            "new": [],
            "repeated": [],
            "resolved": [],
        }

    previous = history[-2].get("recommendations", [])
    latest = history[-1].get("recommendations", [])

    # Compare by category + finding text.
    previous_keys = {
        (item.get("category", ""), item.get("finding", ""))
        for item in previous
    }

    latest_keys = {
        (item.get("category", ""), item.get("finding", ""))
        for item in latest
    }

    return {
        "new": sorted(latest_keys - previous_keys),
        "repeated": sorted(latest_keys & previous_keys),
        "resolved": sorted(previous_keys - latest_keys),
    }


import json

import pandas as pd

from engine import recommendation_history as rh


def test_save_recommendations_creates_history_file(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(rh, "HISTORY_FILE", tmp_path / "history.json")

    recommendations = [{
        "priority": "High",
        "category": "Revenue trend",
        "finding": "Revenue declined.",
        "action": "Investigate sales.",
    }]

    saved = rh.save_recommendations(recommendations)

    assert rh.HISTORY_FILE.exists()
    assert saved["recommendations"] == recommendations


def test_load_history_returns_empty_list_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "HISTORY_FILE", tmp_path / "missing.json")

    assert rh.load_history() == []


def test_history_to_dataframe_returns_expected_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(rh, "HISTORY_FILE", tmp_path / "history.json")

    rh.save_recommendations([{
        "priority": "Medium",
        "category": "Data quality",
        "finding": "Descriptions are missing.",
        "action": "Review product records.",
    }])

    df = rh.history_to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "Priority" in df.columns
    assert "Finding" in df.columns


def test_compare_latest_runs_identifies_new_repeated_and_resolved(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(rh, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(rh, "HISTORY_FILE", tmp_path / "history.json")

    previous = [
        {"category": "Revenue", "finding": "Revenue declined."},
        {"category": "Quality", "finding": "Missing descriptions."},
    ]

    latest = [
        {"category": "Revenue", "finding": "Revenue declined."},
        {"category": "Country", "finding": "High country concentration."},
    ]

    rh.save_recommendations(previous)
    rh.save_recommendations(latest)

    result = rh.compare_latest_runs()

    assert len(result["new"]) == 1
    assert len(result["repeated"]) == 1
    assert len(result["resolved"]) == 1

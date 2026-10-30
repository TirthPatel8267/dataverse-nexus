
import pandas as pd

from engine.business_recommendations import generate_recommendations


def test_empty_dataframe_returns_data_availability_warning():
    df = pd.DataFrame(
        columns=["InvoiceTimestamp", "Country", "Description", "Revenue"]
    )

    result = generate_recommendations(df)

    assert len(result) == 1
    assert result[0]["priority"] == "High"
    assert result[0]["category"] == "Data availability"


def test_revenue_decline_generates_high_priority_recommendation():
    df = pd.DataFrame({
        "InvoiceTimestamp": [
            "2026-01-10", "2026-01-15",
            "2026-02-10", "2026-02-15",
        ],
        "Country": ["UK", "UK", "UK", "UK"],
        "Description": ["Product A"] * 4,
        "Revenue": [100, 100, 80, 80],
    })

    result = generate_recommendations(df)

    revenue_alerts = [
        item for item in result
        if item["category"] == "Revenue trend"
    ]

    assert len(revenue_alerts) == 1
    assert revenue_alerts[0]["priority"] == "High"
    assert "declined" in revenue_alerts[0]["finding"]


def test_missing_descriptions_generate_data_quality_recommendation():
    df = pd.DataFrame({
        "InvoiceTimestamp": ["2026-01-10"] * 100,
        "Country": ["UK"] * 100,
        "Description": [None] * 5 + ["Product A"] * 95,
        "Revenue": [10.0] * 100,
    })

    result = generate_recommendations(df)

    quality_alerts = [
        item for item in result
        if item["category"] == "Data quality"
    ]

    assert len(quality_alerts) == 1
    assert quality_alerts[0]["priority"] == "Medium"

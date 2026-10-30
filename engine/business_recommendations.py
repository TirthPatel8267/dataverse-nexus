
from datetime import datetime

import pandas as pd


def generate_recommendations(
    sales_df: pd.DataFrame,
) -> list[dict]:
    """
    Generate rule-based business recommendations from
    the currently filtered sales DataFrame.

    Expected columns:
    InvoiceTimestamp, Country, Description, Revenue
    """

    recommendations = []

    if sales_df.empty:
        return [{
            "priority": "High",
            "category": "Data availability",
            "finding": "No eligible sales data is available.",
            "action": (
                "Adjust the selected date range or country filters "
                "before interpreting business performance."
            ),
        }]

    data = sales_df.copy()

    data["Revenue"] = pd.to_numeric(
        data["Revenue"], errors="coerce"
    )

    data = data.dropna(subset=["Revenue"])

    # --------------------------------------------------
    # 1. MONTHLY REVENUE TREND
    # --------------------------------------------------

    if "InvoiceTimestamp" in data.columns:
        data["InvoiceTimestamp"] = pd.to_datetime(
            data["InvoiceTimestamp"], errors="coerce"
        )

        dated = data.dropna(subset=["InvoiceTimestamp"]).copy()

        if not dated.empty:
            dated["Month"] = (
                dated["InvoiceTimestamp"].dt.to_period("M")
            )

            monthly = (
                dated.groupby("Month")["Revenue"]
                .sum()
                .sort_index()
            )

            if len(monthly) >= 2:
                previous = float(monthly.iloc[-2])
                latest = float(monthly.iloc[-1])

                if previous != 0:
                    change_pct = (
                        (latest - previous) / abs(previous) * 100
                    )

                    if change_pct <= -10:
                        recommendations.append({
                            "priority": "High",
                            "category": "Revenue trend",
                            "finding": (
                                f"Monthly revenue declined by "
                                f"{abs(change_pct):.1f}% in "
                                f"{monthly.index[-1]} compared "
                                f"with {monthly.index[-2]}."
                            ),
                            "action": (
                                "Investigate changes in order volume, "
                                "product mix, returns, and customer "
                                "activity before deciding on corrective action."
                            ),
                        })

                    elif change_pct >= 10:
                        recommendations.append({
                            "priority": "Medium",
                            "category": "Revenue trend",
                            "finding": (
                                f"Monthly revenue increased by "
                                f"{change_pct:.1f}% in "
                                f"{monthly.index[-1]}."
                            ),
                            "action": (
                                "Check which products and countries "
                                "contributed most to the increase and "
                                "whether the pattern continues."
                            ),
                        })

    # --------------------------------------------------
    # 2. COUNTRY REVENUE CONCENTRATION
    # --------------------------------------------------

    if "Country" in data.columns:
        country_sales = (
            data.groupby("Country")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        total_revenue = float(country_sales.sum())

        if len(country_sales) >= 2 and total_revenue > 0:
            leading_country = country_sales.index[0]
            leading_revenue = float(country_sales.iloc[0])
            share = leading_revenue / total_revenue * 100

            if share >= 70:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Country concentration",
                    "finding": (
                        f"{leading_country} contributes "
                        f"{share:.1f}% of eligible revenue."
                    ),
                    "action": (
                        "Review dependence on this market and compare "
                        "growth opportunities in other countries."
                    ),
                })

            low_contribution = country_sales[
                country_sales > 0
            ]

            if len(low_contribution) >= 2:
                smallest_country = low_contribution.index[-1]
                smallest_revenue = float(
                    low_contribution.iloc[-1]
                )

                recommendations.append({
                    "priority": "Low",
                    "category": "Country comparison",
                    "finding": (
                        f"{smallest_country} has the lowest positive "
                        f"revenue among selected countries "
                        f"(£{smallest_revenue:,.2f})."
                    ),
                    "action": (
                        "Review its sales history and transaction volume "
                        "before deciding whether additional marketing "
                        "or market research is appropriate."
                    ),
                })

    # --------------------------------------------------
    # 3. PRODUCT REVENUE CONCENTRATION
    # --------------------------------------------------

    if "Description" in data.columns:
        products = data[
            data["Description"].notna()
            & data["Description"].astype(str).str.strip().ne("")
        ].copy()

        products = products[
            ~products["Description"].astype(str)
            .str.upper().str.contains("POSTAGE", regex=False)
        ]

        product_sales = (
            products.groupby("Description")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        merchandise_revenue = float(product_sales.sum())

        if not product_sales.empty and merchandise_revenue > 0:
            top_product = product_sales.index[0]
            top_revenue = float(product_sales.iloc[0])
            top_share = top_revenue / merchandise_revenue * 100

            if top_share >= 10:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Product concentration",
                    "finding": (
                        f"{top_product} contributes "
                        f"{top_share:.1f}% of merchandise revenue."
                    ),
                    "action": (
                        "Review stock availability and the stability "
                        "of demand for this product. Consider the "
                        "risk of relying heavily on one item."
                    ),
                })

            top_five_revenue = float(
                product_sales.head(5).sum()
            )

            top_five_share = (
                top_five_revenue / merchandise_revenue * 100
            )

            if top_five_share >= 40:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Product portfolio",
                    "finding": (
                        f"The top five products contribute "
                        f"{top_five_share:.1f}% of merchandise revenue."
                    ),
                    "action": (
                        "Monitor these products while examining "
                        "whether other products offer opportunities "
                        "to broaden the revenue mix."
                    ),
                })

    # --------------------------------------------------
    # 4. DATA QUALITY
    # --------------------------------------------------

    missing_descriptions = (
        data["Description"].isna().sum()
        if "Description" in data.columns
        else 0
    )

    if len(data) > 0:
        missing_pct = missing_descriptions / len(data) * 100

        if missing_pct > 1:
            recommendations.append({
                "priority": "Medium",
                "category": "Data quality",
                "finding": (
                    f"{missing_pct:.2f}% of selected records "
                    "have missing product descriptions."
                ),
                "action": (
                    "Review product-description completeness before "
                    "using product-level findings for decisions."
                ),
            })

    # --------------------------------------------------
    # 5. DEFAULT MESSAGE
    # --------------------------------------------------

    if not recommendations:
        recommendations.append({
            "priority": "Informational",
            "category": "Monitoring",
            "finding": (
                "No recommendation rules were triggered "
                "by the current data and thresholds."
            ),
            "action": (
                "Continue monitoring sales trends, product mix, "
                "country contribution, and data quality."
            ),
        })

    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
        "Informational": 3,
    }

    recommendations.sort(
        key=lambda item: priority_order.get(
            item["priority"], 4
        )
    )

    return recommendations

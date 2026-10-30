import io
from datetime import datetime
import matplotlib.pyplot as plt
from engine.business_recommendations import generate_recommendations
from engine.recommendation_history import (
    save_recommendations,
    load_history,
    history_to_dataframe,
    compare_latest_runs,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="DATAVERSE NEXUS",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "online_retail_parquet"
)


# =========================================================
# 3. DASHBOARD DESIGN
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1020;
        color: #f1f5f9;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    div[data-testid="stMetric"] {
        background-color: #172033;
        border: 1px solid #26344d;
        padding: 18px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 4. LOAD PROCESSED DATA
# =========================================================

@st.cache_data(show_spinner="Loading processed retail data...")
def load_data(data_path):
    df = pd.read_parquet(data_path)

    # Convert timestamp to pandas datetime
    df["InvoiceTimestamp"] = pd.to_datetime(
        df["InvoiceTimestamp"],
        errors="coerce",
    )

    # Ensure numeric columns are numeric
    df["Quantity"] = pd.to_numeric(
        df["Quantity"], errors="coerce"
    )

    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"], errors="coerce"
    )

    df["Revenue"] = pd.to_numeric(
        df["Revenue"], errors="coerce"
    )

    return df


def generate_executive_pdf(
    total_revenue,
    total_invoices,
    total_customers,
    total_units,
    monthly_sales,
    country_sales,
    product_sales,
    quality_report,
    anomaly_summary,
    date_start,
    date_end,
):
    """Create a downloadable DATAVERSE NEXUS PDF report."""

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="DATAVERSE NEXUS Executive Report",
        author="DATAVERSE NEXUS",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=23,
            leading=28,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
        )
    )

    
    story = []

    generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # -----------------------------------------------------
    # PROFESSIONAL COVER PAGE
    # -----------------------------------------------------

    cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=30,
        leading=36,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=18,
    )

    cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#334155"),
        spaceAfter=18,
    )

    story.append(Spacer(1, 1.3 * inch))
    story.append(Paragraph("DATAVERSE NEXUS", cover_title))
    story.append(
        Paragraph(
            "INTELLIGENT BIG DATA DISCOVERY PLATFORM",
            cover_subtitle,
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    cover_table = Table(
        [
            ["EXECUTIVE BUSINESS INTELLIGENCE REPORT"],
            [f"Reporting period: {date_start} to {date_end}"],
            [f"Generated on: {generated_at}"],
            [f"Total eligible revenue: £{total_revenue:,.2f}"],
            [f"Unique invoices: {total_invoices:,}"],
        ],
        colWidths=[5.8 * inch],
    )

    cover_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#17365D"),
            ),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F1F5F9")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#172033")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ])
    )

    story.append(cover_table)
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            "Prepared using Python, PySpark, Pandas, Streamlit, "
            "Plotly and Parquet.",
            ParagraphStyle(
                "CoverFooter",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#64748B"),
            ),
        )
    )

    story.append(PageBreak())

    # -----------------------------------------------------
    # EXECUTIVE SUMMARY
    # -----------------------------------------------------

    story.append(
        Paragraph("Executive Summary", styles["SectionTitle"])
    )

    story.append(
        Paragraph(
            "This report summarizes eligible retail sales, monthly "
            "revenue trends, leading countries and products, detected "
            "daily revenue anomalies, and data-quality findings.",
            styles["BodyText"],
        )
    )

    # -----------------------------------------------------
    # KPI TABLE
    # -----------------------------------------------------

    story.append(
        Paragraph("Key Performance Indicators", styles["SectionTitle"])
    )

    kpi_data = [
        ["Metric", "Value"],
        ["Eligible Sales Revenue", f"£{total_revenue:,.2f}"],
        ["Unique Invoices", f"{total_invoices:,}"],
        ["Unique Customers", f"{total_customers:,}"],
        ["Units Sold", f"{total_units:,.0f}"],
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[3.2 * inch, 2.4 * inch],
    )

    kpi_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F1F5F9")),
            ("PADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(kpi_table)

    # -----------------------------------------------------
    # MONTHLY REVENUE CHART
    # -----------------------------------------------------

    story.append(
        Paragraph("Monthly Revenue Trend", styles["SectionTitle"])
    )

    if not monthly_sales.empty:
        fig, ax = plt.subplots(figsize=(8, 3.4))

        ax.plot(
            monthly_sales["Month"],
            monthly_sales["Revenue"],
            marker="o",
        )

        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue (£)")
        ax.set_title("Monthly Revenue")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()

        chart_buffer = io.BytesIO()
        fig.savefig(
            chart_buffer,
            format="png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(fig)
        chart_buffer.seek(0)

        story.append(
            Image(
                chart_buffer,
                width=6.8 * inch,
                height=2.8 * inch,
            )
        )

        
   
       
    # -----------------------------------------------------
    # DAILY REVENUE ANOMALY SUMMARY
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Daily Revenue Anomaly Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            "Potential anomalies are identified using the "
            "interquartile range (IQR) rule. These are unusual "
            "revenue observations, not confirmed errors or fraud.",
            styles["BodyText"],
        )
    )

    if anomaly_summary.empty:
        story.append(
            Paragraph(
                "Not enough daily sales data was available to "
                "calculate revenue anomalies.",
                styles["BodyText"],
            )
        )
    else:
        unusual_days = anomaly_summary[
            anomaly_summary["Alert"] == "Unusual"
        ].copy()

        total_days_analyzed = len(anomaly_summary)
        total_unusual_days = len(unusual_days)

        summary_text = (
            f"<b>Total days analyzed:</b> "
            f"{total_days_analyzed:,} &nbsp;&nbsp;&nbsp; "
            f"<b>Unusual days detected:</b> "
            f"{total_unusual_days:,}"
        )

        story.append(
            Paragraph(summary_text, styles["BodyText"])
        )

        if unusual_days.empty:
            story.append(
                Paragraph(
                    "No unusual revenue days were detected "
                    "in the selected reporting period.",
                    styles["BodyText"],
                )
            )
        else:
            anomaly_data = [
                ["Date", "Revenue (£)", "Invoices", "Status"]
            ]

            for _, row in unusual_days.iterrows():
                anomaly_data.append([
                    str(row["Sale_Date"]),
                    f"£{row['Revenue']:,.2f}",
                    f"{int(row['Invoice_Count']):,}",
                    "Unusual",
                ])

            anomaly_table = Table(
                anomaly_data,
                colWidths=[
                    1.35 * inch,
                    1.65 * inch,
                    1.15 * inch,
                    1.35 * inch,
                ],
                repeatRows=1,
            )

            anomaly_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0), (-1, 0),
                        colors.HexColor("#17365D"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    (
                        "BACKGROUND",
                        (0, 1), (-1, -1),
                        colors.HexColor("#F1F5F9"),
                    ),
                ])
            )

            story.append(anomaly_table)




    # -----------------------------------------------------
    # COUNTRY PERFORMANCE
    # -----------------------------------------------------

    story.append(
        Paragraph("Top Countries by Revenue", styles["SectionTitle"])
    )

    country_data = [["Country", "Revenue (£)"]]

    for _, row in country_sales.head(10).iterrows():
        country_data.append([
            str(row["Country"]),
            f"{row['Revenue']:,.2f}",
        ])

    country_table = Table(
        country_data,
        colWidths=[3.2 * inch, 2.4 * inch],
        repeatRows=1,
    )

    country_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(country_table)

    # -----------------------------------------------------
    # PRODUCT PERFORMANCE
    # -----------------------------------------------------

    story.append(
        Paragraph("Top Merchandise Products", styles["SectionTitle"])
    )

    product_data = [["Product", "Revenue (£)"]]

    for _, row in product_sales.head(10).iterrows():
        product_name = str(row["Description"])

        if len(product_name) > 55:
            product_name = product_name[:52] + "..."

        product_data.append([
            product_name,
            f"{row['Revenue']:,.2f}",
        ])

    product_table = Table(
        product_data,
        colWidths=[3.8 * inch, 1.8 * inch],
        repeatRows=1,
    )

    product_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 5),
        ])
    )

    story.append(product_table)

   
    # -----------------------------------------------------
    # DATA QUALITY SUMMARY WITH PERCENTAGES
    # -----------------------------------------------------

    story.append(
        Paragraph("Data Quality Summary", styles["SectionTitle"])
    )

    # Denominator: records remaining after duplicate removal
    total_quality_rows = int(
        quality_report.get("final_rows", 0) or 0
    )

    quality_fields = [
        ("Missing descriptions", "missing_description"),
        ("Missing customer IDs", "missing_customer_id"),
        ("Invalid invoice dates", "invalid_invoice_date"),
        ("Negative quantity rows", "negative_quantity_rows"),
        ("Negative unit price rows", "negative_unit_price_rows"),
        ("Missing critical fields", "missing_critical_fields"),
    ]

    quality_data = [
        ["Quality Check", "Affected Rows", "Affected (%)"]
    ]

    for label, key in quality_fields:
        affected = int(quality_report.get(key, 0) or 0)

        percentage = (
            affected / total_quality_rows * 100
            if total_quality_rows > 0
            else None
        )

        quality_data.append([
            label,
            f"{affected:,}",
            f"{percentage:.2f}%"
            if percentage is not None
            else "N/A",
        ])

    quality_table = Table(
        quality_data,
        colWidths=[2.8 * inch, 1.4 * inch, 1.4 * inch],
        repeatRows=1,
    )

    quality_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0), (-1, 0),
                colors.HexColor("#17365D"),
            ),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            (
                "BACKGROUND",
                (0, 1), (-1, -1),
                colors.HexColor("#F1F5F9"),
            ),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(quality_table)

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            f"Denominator: {total_quality_rows:,} records after "
            "exact duplicate removal. Quality categories can overlap, "
            "so their percentages should not be added together.",
            styles["Italic"],
        )
    )

    
    def add_page_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))

        canvas.drawString(
            42,
            25,
            f"DATAVERSE NEXUS | Generated: {generated_at}",
        )

        canvas.drawRightString(
    A4[0] - 42,
    25,
    f"Page {doc.page}",
)
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_footer,
        onLaterPages=add_page_footer,
    )


    buffer.seek(0)
    return buffer.getvalue()

# =========================================================
# 5. SIDEBAR
# =========================================================

st.sidebar.title("🌌 DATAVERSE NEXUS")
st.sidebar.caption("Intelligent Big Data Discovery Platform")
st.sidebar.divider()

st.sidebar.subheader("Navigation")


page = st.sidebar.radio(
    "Choose a dashboard",
    [
        "Overview",
        "Sales Analysis",
        "Product Analysis",
        "Country Analysis",
        "Data Quality",
        "Performance Analytics",
        "Intelligence & Alerts",
        "Business Recommendations",
        "Recommendation History",
        "Architecture & Metrics",
        "PDF Executive Report",
    ],
)


st.sidebar.divider()
st.sidebar.caption("Powered by PySpark, Pandas, and Plotly")


# =========================================================
# 6. LOAD DATA SAFELY
# =========================================================

if not DATA_PATH.exists():
    st.error(
        "Processed dataset not found. "
        "Run `python -m engine.cleaning` first."
    )
    st.stop()

try:
    df = load_data(str(DATA_PATH))
except Exception as error:
    st.error(f"Could not load the Parquet dataset: {error}")
    st.stop()


# =========================================================
# 7. HEADER AND FILTERS
# =========================================================

st.title("🌌 DATAVERSE NEXUS")
st.markdown(
    "### The Intelligent Big Data Discovery Platform"
)

st.caption(
    "Explore retail transactions, sales patterns, "
    "products, countries, and data quality."
)

valid_dates = df["InvoiceTimestamp"].dropna()

if valid_dates.empty:
    st.error(
        "No valid invoice timestamps were found. "
        "Check the processed dataset."
    )
    st.stop()

min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

st.sidebar.subheader("Global Filters")

date_range = st.sidebar.date_input(
    "Invoice date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

countries = sorted(
    df["Country"].dropna().astype(str).unique().tolist()
)

selected_countries = st.sidebar.multiselect(
    "Countries",
    options=countries,
    default=countries,
)

# Handle incomplete date selection
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Please select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range

if start_date > end_date:
    st.warning("Start date cannot be after end date.")
    st.stop()

# Apply global filters
filtered_df = df[
    (df["InvoiceTimestamp"].dt.date >= start_date)
    & (df["InvoiceTimestamp"].dt.date <= end_date)
    & (df["Country"].astype(str).isin(selected_countries))
].copy()

# Exclude cancelled invoices from sales KPIs.
# Invoice numbers beginning with C commonly identify cancellations.
sales_df = filtered_df[
    ~filtered_df["InvoiceNo"].astype(str).str.startswith("C")
    & (filtered_df["Quantity"] > 0)
    & (filtered_df["UnitPrice"] >= 0)
].copy()


# =========================================================
# 8. CALCULATE KEY PERFORMANCE INDICATORS
# =========================================================

total_revenue = sales_df["Revenue"].sum()

total_invoices = sales_df["InvoiceNo"].nunique()

total_customers = sales_df["CustomerID"].nunique()

total_units = sales_df["Quantity"].sum()

total_products = sales_df["StockCode"].nunique()


# =========================================================
# 9. OVERVIEW PAGE
# =========================================================

if page == "Overview":

    st.subheader("Business Overview")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Total Revenue",
        f"£{total_revenue:,.2f}",
    )

    metric2.metric(
        "Invoices",
        f"{total_invoices:,}",
    )

    metric3.metric(
        "Unique Customers",
        f"{total_customers:,}",
    )

    metric4.metric(
        "Units Sold",
        f"{total_units:,.0f}",
    )

    st.divider()

    # Revenue trend
    trend_df = sales_df.dropna(
        subset=["InvoiceTimestamp"]
    ).copy()

    trend_df["Month"] = (
        trend_df["InvoiceTimestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_sales = (
        trend_df.groupby("Month", as_index=False)["Revenue"]
        .sum()
        .sort_values("Month")
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Revenue")

        fig = px.line(
            monthly_sales,
            x="Month",
            y="Revenue",
            markers=True,
            title="Revenue Trend",
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Month",
            yaxis_title="Revenue (£)",
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Top 10 Countries")

        country_sales = (
            sales_df.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .nlargest(10, "Revenue")
            .sort_values("Revenue")
        )

        fig = px.bar(
            country_sales,
            x="Revenue",
            y="Country",
            orientation="h",
            title="Revenue by Country",
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Revenue (£)",
            yaxis_title="Country",
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Products")

    product_sales = (
        sales_df.groupby("Description", as_index=False)["Revenue"]
        .sum()
        .nlargest(10, "Revenue")
        .sort_values("Revenue")
    )

    fig = px.bar(
        product_sales,
        x="Revenue",
        y="Description",
        orientation="h",
        title="Top Products by Revenue",
    )

    fig.update_layout(
        template="plotly_dark",
        yaxis_title="Product",
        xaxis_title="Revenue (£)",
    )

    st.plotly_chart(fig, use_container_width=True)



    
    # =====================================================
    # 9A. EXECUTIVE INSIGHTS
    # =====================================================

    st.divider()
    st.subheader("Executive Insights")
    st.caption(
        "Automatically generated observations based on "
        "your selected date range and countries."
    )

    if sales_df.empty:
        st.info(
            "No eligible sales transactions are available "
            "for the current filters."
        )

    else:
        # ---------------------------------------------
        # A. REVENUE TREND INSIGHT
        # ---------------------------------------------

        insight_sales = sales_df.dropna(
            subset=["InvoiceTimestamp"]
        ).copy()

        insight_sales["Month"] = (
            insight_sales["InvoiceTimestamp"]
            .dt.to_period("M")
        )

        monthly_revenue = (
            insight_sales.groupby("Month")["Revenue"]
            .sum()
            .sort_index()
        )

        if len(monthly_revenue) >= 2:
            latest_month = monthly_revenue.index[-1]
            previous_month = monthly_revenue.index[-2]

            latest_revenue = float(
                monthly_revenue.iloc[-1]
            )

            previous_revenue = float(
                monthly_revenue.iloc[-2]
            )

            if previous_revenue != 0:
                monthly_change = (
                    (latest_revenue - previous_revenue)
                    / abs(previous_revenue)
                ) * 100
            else:
                monthly_change = None

            if monthly_change is not None:
                if monthly_change > 0:
                    trend_message = (
                        f"Revenue increased by "
                        f"{monthly_change:.1f}% from "
                        f"{previous_month.strftime('%b %Y')} "
                        f"to {latest_month.strftime('%b %Y')}."
                    )
                elif monthly_change < 0:
                    trend_message = (
                        f"Revenue decreased by "
                        f"{abs(monthly_change):.1f}% from "
                        f"{previous_month.strftime('%b %Y')} "
                        f"to {latest_month.strftime('%b %Y')}."
                    )
                else:
                    trend_message = (
                        "Revenue remained unchanged between "
                        "the latest two months."
                    )
            else:
                trend_message = (
                    "The previous month's revenue was zero, "
                    "so a percentage change cannot be calculated."
                )

        elif len(monthly_revenue) == 1:
            latest_month = monthly_revenue.index[-1]
            latest_revenue = float(monthly_revenue.iloc[-1])

            trend_message = (
                f"Only one month of sales is available: "
                f"{latest_month.strftime('%b %Y')}. "
                "More data is needed to compare monthly trends."
            )

        else:
            trend_message = (
                "There are not enough valid invoice dates "
                "to analyze the revenue trend."
            )

        # ---------------------------------------------
        # B. TOP COUNTRY INSIGHT
        # ---------------------------------------------

        country_summary = (
            sales_df.groupby("Country")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not country_summary.empty:
            top_country = str(country_summary.index[0])
            top_country_revenue = float(
                country_summary.iloc[0]
            )

            country_revenue_total = float(
                country_summary.sum()
            )

            country_share = (
                top_country_revenue / country_revenue_total * 100
                if country_revenue_total > 0
                else 0
            )

            country_message = (
                f"{top_country} is the leading country by "
                f"revenue, generating "
                f"£{top_country_revenue:,.2f} "
                f"({country_share:.1f}% of eligible sales revenue)."
            )
        else:
            country_message = (
                "No country-level sales information is available."
            )

        # ---------------------------------------------
        # C. TOP MERCHANDISE PRODUCT INSIGHT
        # ---------------------------------------------

        merchandise = sales_df[
            sales_df["Description"]
            .fillna("")
            .str.strip()
            .ne("")
            & ~sales_df["Description"]
            .fillna("")
            .str.upper()
            .str.contains("POSTAGE", regex=False)
        ].copy()

        if not merchandise.empty:
            product_summary = (
                merchandise.groupby("Description")["Revenue"]
                .sum()
                .sort_values(ascending=False)
            )

            top_product = str(product_summary.index[0])
            top_product_revenue = float(
                product_summary.iloc[0]
            )

            merchandise_revenue_total = float(
                product_summary.sum()
            )

            product_share = (
                top_product_revenue
                / merchandise_revenue_total * 100
                if merchandise_revenue_total > 0
                else 0
            )

            product_message = (
                f"{top_product} is the highest-revenue "
                f"merchandise product, generating "
                f"£{top_product_revenue:,.2f} "
                f"({product_share:.1f}% of merchandise revenue)."
            )
        else:
            product_message = (
                "No merchandise product information is available "
                "for the current filters."
            )

        # ---------------------------------------------
        # D. DISPLAY EXECUTIVE INSIGHT CARDS
        # ---------------------------------------------

        insight_col1, insight_col2 = st.columns(2)

        with insight_col1:
            st.markdown("#### 📈 Revenue Trend")
            st.info(trend_message)

            if len(monthly_revenue) >= 2:
                st.metric(
                    "Latest Month Revenue",
                    f"£{latest_revenue:,.2f}",
                    (
                        f"{monthly_change:+.1f}%"
                        if monthly_change is not None
                        else None
                    ),
                )

        with insight_col2:
            st.markdown("#### 🌍 Leading Country")
            st.success(country_message)

        st.markdown("#### 🏆 Leading Merchandise Product")
        st.info(product_message)

        # ---------------------------------------------
        # E. BUSINESS RECOMMENDATIONS
        # ---------------------------------------------

        st.markdown("#### 💡 Suggested Business Actions")

        st.markdown(
            "- **Revenue:** Investigate the months with the "
            "largest changes to understand possible sales drivers."
        )

        st.markdown(
            "- **Countries:** Review the leading country's "
            "sales contribution and compare it with other markets."
        )

        st.markdown(
            "- **Products:** Review the best-performing "
            "merchandise and check whether its performance "
            "is consistent across different months."
        )

        st.caption(
            "These are data-driven observations, not proof of "
            "causation. Country and product rankings follow the "
            "current filters and eligible-sales rules."
        )

        st.caption(
    "These are data-driven observations, not proof of "
    "causation. Country and product rankings follow the "
    "current filters and eligible-sales rules."
)


# =========================================================
# 10. SALES ANALYSIS PAGE
# =========================================================

elif page == "Sales Analysis":

    st.subheader("Sales Analysis")
    st.caption(
        "Explore revenue trends, invoice activity, "
        "and sales performance using your selected filters."
    )

    if sales_df.empty:
        st.warning(
            "No eligible sales transactions match the current filters. "
            "Adjust the date range or country selection."
        )

    else:
        # -------------------------------------------------
        # 1. SALES KPIs
        # -------------------------------------------------

        st.markdown("### Sales Performance Summary")

        sales_revenue = sales_df["Revenue"].sum()
        invoice_count = sales_df["InvoiceNo"].nunique()
        average_order_value = (
            sales_revenue / invoice_count
            if invoice_count > 0
            else 0
        )
        quantity_sold = sales_df["Quantity"].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Revenue",
            f"£{sales_revenue:,.2f}"
        )

        col2.metric(
            "Total Invoices",
            f"{invoice_count:,}"
        )

        col3.metric(
            "Average Order Value",
            f"£{average_order_value:,.2f}"
        )

        col4.metric(
            "Units Sold",
            f"{quantity_sold:,.0f}"
        )

        st.divider()

        # -------------------------------------------------
        # 2. MONTHLY REVENUE
        # -------------------------------------------------

        st.markdown("### Monthly Revenue Trend")

        sales_with_dates = sales_df.dropna(
            subset=["InvoiceTimestamp"]
        ).copy()

        sales_with_dates["Month"] = (
            sales_with_dates["InvoiceTimestamp"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_sales_analysis = (
            sales_with_dates
            .groupby("Month", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoices=("InvoiceNo", "nunique"),
                Units=("Quantity", "sum"),
            )
            .sort_values("Month")
        )

        if not monthly_sales_analysis.empty:

            fig = px.line(
                monthly_sales_analysis,
                x="Month",
                y="Revenue",
                markers=True,
                title="Monthly Revenue",
                hover_data=["Invoices", "Units"],
            )

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Month",
                yaxis_title="Revenue (£)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # Month-over-month comparison
            if len(monthly_sales_analysis) >= 2:

                latest_month = monthly_sales_analysis.iloc[-1]
                previous_month = monthly_sales_analysis.iloc[-2]

                previous_revenue = previous_month["Revenue"]
                latest_revenue = latest_month["Revenue"]

                growth = (
                    (
                        latest_revenue - previous_revenue
                    ) / abs(previous_revenue) * 100
                    if previous_revenue != 0
                    else None
                )

                st.markdown("#### Month-over-Month Comparison")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Previous Month",
                    f"£{previous_revenue:,.2f}"
                )

                col2.metric(
                    "Latest Month",
                    f"£{latest_revenue:,.2f}"
                )

                col3.metric(
                    "Revenue Change",
                    f"{growth:+.2f}%"
                    if growth is not None
                    else "N/A",
                )

            st.dataframe(
                monthly_sales_analysis,
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info(
                "No valid invoice dates are available for "
                "monthly sales analysis."
            )

        st.divider()

        # -------------------------------------------------
        # 3. TOP COUNTRIES BY SALES
        # -------------------------------------------------

        st.markdown("### Country Sales Performance")

        country_sales_analysis = (
            sales_df
            .groupby("Country", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoices=("InvoiceNo", "nunique"),
                Units=("Quantity", "sum"),
            )
            .sort_values("Revenue", ascending=False)
        )

        top_countries_analysis = (
            country_sales_analysis
            .head(10)
            .sort_values("Revenue")
        )

        fig = px.bar(
            top_countries_analysis,
            x="Revenue",
            y="Country",
            orientation="h",
            title="Top 10 Countries by Revenue",
            hover_data=["Invoices", "Units"],
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Revenue (£)",
            yaxis_title="Country",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------------------------------
        # 4. SALES TRANSACTION DETAILS
        # -------------------------------------------------

        st.divider()
        st.markdown("### Sales Transaction Details")

        sales_details = sales_df[
            [
                "InvoiceNo",
                "InvoiceTimestamp",
                "Description",
                "Quantity",
                "UnitPrice",
                "Revenue",
                "Country",
            ]
        ].copy()

        st.dataframe(
            sales_details.head(500),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Showing up to 500 of {len(sales_details):,} "
            "eligible sales transaction rows."
        )

        csv_bytes = sales_details.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Sales Analysis (CSV)",
            data=csv_bytes,
            file_name="dataverse_sales_analysis.csv",
            mime="text/csv",
        )



# =========================================================
# 11. PRODUCT ANALYSIS PAGE
# =========================================================

elif page == "Product Analysis":

    st.subheader("Product Performance")
    st.caption(
        "Analyze merchandise performance by revenue, "
        "quantity sold, and invoice count."
    )

    # Exclude postage-related charges from merchandise rankings
    merchandise_df = sales_df[
        ~sales_df["Description"]
        .fillna("")
        .str.upper()
        .str.contains("POSTAGE", regex=False)
    ].copy()

    # Remove rows without a product description
    merchandise_df = merchandise_df[
        merchandise_df["Description"].notna()
        & (merchandise_df["Description"].str.strip() != "")
    ]

    if merchandise_df.empty:
        st.warning("No merchandise data available for the selected filters.")

    else:
        # Summarize product performance
        product_summary = (
            merchandise_df.groupby(
                "Description",
                as_index=False
            )
            .agg(
                Total_Revenue=("Revenue", "sum"),
                Total_Quantity=("Quantity", "sum"),
                Invoice_Count=("InvoiceNo", "nunique"),
            )
            .sort_values(
                "Total_Revenue",
                ascending=False
            )
        )

        # KPI cards
        total_products = product_summary["Description"].nunique()
        merchandise_revenue = merchandise_df["Revenue"].sum()
        merchandise_units = merchandise_df["Quantity"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Unique Merchandise Products",
            f"{total_products:,}"
        )

        col2.metric(
            "Merchandise Revenue",
            f"£{merchandise_revenue:,.2f}"
        )

        col3.metric(
            "Merchandise Units Sold",
            f"{merchandise_units:,.0f}"
        )

        st.divider()

        # Select chart metric
        metric_choice = st.selectbox(
            "Rank products by",
            [
                "Revenue",
                "Quantity Sold",
                "Invoice Count"
            ]
        )

        metric_columns = {
            "Revenue": "Total_Revenue",
            "Quantity Sold": "Total_Quantity",
            "Invoice Count": "Invoice_Count"
        }

        selected_metric = metric_columns[metric_choice]

        # Top 10 products
        top_products = (
            product_summary
            .nlargest(10, selected_metric)
            .sort_values(selected_metric)
        )

        st.subheader(f"Top 10 Products by {metric_choice}")

        fig = px.bar(
            top_products,
            x=selected_metric,
            y="Description",
            orientation="h",
            text=selected_metric,
            title=f"Top 10 Merchandise Products — {metric_choice}",
            hover_data=[
                "Total_Revenue",
                "Total_Quantity",
                "Invoice_Count"
            ]
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title=metric_choice,
            yaxis_title="Product",
            yaxis=dict(
                categoryorder="total ascending"
            )
        )

        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Full product table
        st.subheader("Product Performance Details")

        st.dataframe(
            product_summary,
            use_container_width=True,
            hide_index=True
        )

        # Download report
        csv_data = product_summary.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Product Report (CSV)",
            data=csv_data,
            file_name="dataverse_product_analysis.csv",
            mime="text/csv"
        )



# =========================================================
# 12. COUNTRY ANALYSIS PAGE
# =========================================================

elif page == "Country Analysis":

    st.subheader("Country Performance")

    country_summary = (
        sales_df.groupby("Country", as_index=False)
        .agg(
            Total_Revenue=("Revenue", "sum"),
            Total_Orders=("InvoiceNo", "nunique"),
            Total_Customers=("CustomerID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .sort_values("Total_Revenue", ascending=False)
    )

    st.dataframe(
        country_summary,
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        country_summary.head(15).sort_values("Total_Revenue"),
        x="Total_Revenue",
        y="Country",
        orientation="h",
        title="Top 15 Countries by Revenue",
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)



# =========================================================
# 13. ADVANCED DATA QUALITY DASHBOARD
# =========================================================

elif page == "Data Quality":

    st.subheader("Data Quality Intelligence")
    st.caption(
        "Monitor data completeness, validity, and potential "
        "issues in the selected transactions."
    )

    # -----------------------------------------------------
    # 1. DEFINE QUALITY CHECKS
    # -----------------------------------------------------

    quality_checks = {
        "Missing Description": "MissingDescription",
        "Missing Customer ID": "MissingCustomerID",
        "Invalid Invoice Date": "InvalidInvoiceDate",
        "Negative Quantity": "NegativeQuantity",
        "Negative Unit Price": "NegativeUnitPrice",
        "Missing Critical Fields": "MissingCriticalFields",
    }

    total_rows = len(filtered_df)

    if total_rows == 0:
        st.warning(
            "No records match the current filters. "
            "Adjust the date range or country selection."
        )

    else:
        # -------------------------------------------------
        # 2. CALCULATE QUALITY STATISTICS
        # -------------------------------------------------

        quality_rows = []

        issue_masks = []

        for label, column in quality_checks.items():

            if column not in filtered_df.columns:
                continue

            mask = filtered_df[column].fillna(False).astype(bool)
            issue_masks.append(mask)

            affected = int(mask.sum())
            percentage = affected / total_rows * 100

            if percentage == 0:
                status = "Good"
            elif percentage < 1:
                status = "Low"
            elif percentage < 5:
                status = "Moderate"
            else:
                status = "High"

            quality_rows.append({
                "Quality Check": label,
                "Affected Rows": affected,
                "Affected (%)": round(percentage, 2),
                "Unaffected Rows": total_rows - affected,
                "Status": status,
            })

        quality_df = pd.DataFrame(quality_rows)

        # A row is affected if ANY selected quality check flags it.
        # This avoids double-counting rows with multiple issues.
        if issue_masks:
            any_issue = issue_masks[0].copy()

            for mask in issue_masks[1:]:
                any_issue = any_issue | mask

            affected_unique = int(any_issue.sum())
        else:
            any_issue = pd.Series(
                False,
                index=filtered_df.index
            )
            affected_unique = 0

        clean_rows = total_rows - affected_unique

        issue_percentage = (
            affected_unique / total_rows * 100
        )

        quality_score = (
            clean_rows / total_rows * 100
        )

        # -------------------------------------------------
        # 3. TOP KPI CARDS
        # -------------------------------------------------

        st.markdown("### Quality Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Records Analyzed",
            f"{total_rows:,}"
        )

        col2.metric(
            "Unique Affected Rows",
            f"{affected_unique:,}"
        )

        col3.metric(
            "Unaffected Rows",
            f"{clean_rows:,}"
        )

        col4.metric(
            "Quality Score",
            f"{quality_score:.2f}%"
        )

        st.progress(
            min(max(quality_score / 100, 0.0), 1.0),
            text=f"Unaffected-record score: {quality_score:.2f}%"
        )

        st.caption(
            "Quality score = percentage of rows with none of "
            "the selected quality flags. It is a project-specific "
            "indicator, not an official data-quality certification."
        )

        st.divider()

        # -------------------------------------------------
        # 4. QUALITY CHECK TABLE
        # -------------------------------------------------

        st.markdown("### Quality Check Details")

        st.dataframe(
            quality_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="Download Quality Summary (CSV)",
            data=quality_df.to_csv(index=False).encode("utf-8"),
            file_name="dataverse_quality_summary.csv",
            mime="text/csv"
        )

        st.divider()

        # -------------------------------------------------
        # 5. VISUALIZE AFFECTED ROWS
        # -------------------------------------------------

        left, right = st.columns(2)

        with left:
            st.markdown("### Records by Quality Check")

            chart_df = quality_df.sort_values(
                "Affected Rows",
                ascending=True
            )

            fig = px.bar(
                chart_df,
                x="Affected Rows",
                y="Quality Check",
                orientation="h",
                color="Status",
                hover_data=["Affected (%)"],
                title="Number of Affected Records"
            )

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Affected Rows",
                yaxis_title="",
                legend_title="Severity"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with right:
            st.markdown("### Affected vs Unaffected")

            comparison_df = pd.DataFrame({
                "Record Status": [
                    "Unaffected",
                    "Affected"
                ],
                "Rows": [
                    clean_rows,
                    affected_unique
                ]
            })

            fig = px.pie(
                comparison_df,
                names="Record Status",
                values="Rows",
                hole=0.55,
                title="Unique Record Quality"
            )

            fig.update_layout(
                template="plotly_dark"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()

        # -------------------------------------------------
        # 6. SHOW ACTIONABLE INSIGHTS
        # -------------------------------------------------

        st.markdown("### Recommended Actions")

        issues_found = quality_df[
            quality_df["Affected Rows"] > 0
        ].sort_values(
            "Affected (%)",
            ascending=False
        )

        if issues_found.empty:
            st.success(
                "No records were flagged by the selected quality checks."
            )

        else:
            for _, row in issues_found.iterrows():

                label = row["Quality Check"]
                count = int(row["Affected Rows"])
                pct = row["Affected (%)"]

                if label == "Missing Customer ID":
                    recommendation = (
                        "Keep these transactions for sales analysis, "
                        "but exclude unknown IDs from customer-specific "
                        "analysis where appropriate."
                    )

                elif label == "Missing Description":
                    recommendation = (
                        "Review missing product descriptions before "
                        "product-level reporting."
                    )

                elif label == "Invalid Invoice Date":
                    recommendation = (
                        "Inspect the original date values and parsing "
                        "rules before using time-based analysis."
                    )

                elif label == "Negative Quantity":
                    recommendation = (
                        "Review possible product returns or credit "
                        "transactions. Do not automatically delete them."
                    )

                elif label == "Negative Unit Price":
                    recommendation = (
                        "Inspect affected transactions to determine "
                        "whether prices are invalid or require special handling."
                    )

                else:
                    recommendation = (
                        "Inspect missing invoice numbers, stock codes, "
                        "quantities, or prices before relevant analyses."
                    )

                with st.expander(
                    f"{label}: {count:,} rows ({pct:.2f}%)"
                ):
                    st.write(recommendation)

        # -------------------------------------------------
        # 7. PREVIEW FLAGGED RECORDS
        # -------------------------------------------------

        st.markdown("### Flagged Record Preview")

        show_flagged = st.checkbox(
            "Show records with at least one quality issue"
        )

        if show_flagged:
            flagged_df = filtered_df.loc[any_issue].copy()

            st.dataframe(
                flagged_df.head(500),
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Showing up to 500 of {len(flagged_df):,} "
                "flagged records."
            )

            st.download_button(
                label="Download Flagged Records (CSV)",
                data=flagged_df.to_csv(index=False).encode("utf-8"),
                file_name="dataverse_flagged_records.csv",
                mime="text/csv"
            )

# =========================================================
# 14(a) PERFORMANCE ANALYTICS PAGE
# =========================================================

elif page == "Performance Analytics":

    st.subheader("Performance Analytics")
    st.caption(
        "Analyze sales growth, average order value, returns, "
        "and country/product performance."
    )

    # -----------------------------------------------------
    # 1. SALES GROWTH
    # -----------------------------------------------------

    st.markdown("### 1. Sales Growth")

    growth_df = sales_df.dropna(
        subset=["InvoiceTimestamp"]
    ).copy()

    if growth_df.empty:
        st.warning("No eligible sales data is available.")
    else:
        growth_df["Month"] = (
            growth_df["InvoiceTimestamp"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            growth_df.groupby("Month", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoices=("InvoiceNo", "nunique"),
            )
            .sort_values("Month")
        )

        monthly["Previous_Revenue"] = monthly["Revenue"].shift(1)

        monthly["Growth_Percent"] = (
            (
                monthly["Revenue"] - monthly["Previous_Revenue"]
            )
            / monthly["Previous_Revenue"].abs().replace(0, float("nan"))
        ) * 100

        if len(monthly) >= 2:
            latest = monthly.iloc[-1]
            previous = monthly.iloc[-2]

            change = latest["Growth_Percent"]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Latest Month Revenue",
                f"£{latest['Revenue']:,.2f}"
            )

            col2.metric(
                "Previous Month Revenue",
                f"£{previous['Revenue']:,.2f}"
            )

            col3.metric(
                "Month-over-Month Growth",
                (
                    f"{change:+.2f}%"
                    if pd.notna(change)
                    else "N/A"
                )
            )

        fig = px.line(
            monthly,
            x="Month",
            y="Revenue",
            markers=True,
            title="Monthly Revenue Growth",
            hover_data=["Invoices", "Growth_Percent"],
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Month",
            yaxis_title="Revenue (£)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            monthly,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # 2. AVERAGE ORDER VALUE
    # -----------------------------------------------------

    st.markdown("### 2. Average Order Value (AOV)")

    if sales_df.empty:
        st.info("No eligible sales transactions are available.")
    else:
        invoice_summary = (
            sales_df.groupby("InvoiceNo", as_index=False)
            .agg(
                Invoice_Revenue=("Revenue", "sum"),
                Units=("Quantity", "sum"),
            )
        )

        invoice_count = len(invoice_summary)

        total_invoice_revenue = invoice_summary[
            "Invoice_Revenue"
        ].sum()

        aov = (
            total_invoice_revenue / invoice_count
            if invoice_count > 0
            else 0
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average Order Value",
            f"£{aov:,.2f}"
        )

        col2.metric(
            "Unique Invoices",
            f"{invoice_count:,}"
        )

        col3.metric(
            "Average Units per Invoice",
            (
                f"{invoice_summary['Units'].mean():,.2f}"
                if invoice_count > 0
                else "0"
            )
        )

        invoice_summary["Order_Value_Band"] = pd.cut(
            invoice_summary["Invoice_Revenue"],
            bins=[-float("inf"), 50, 100, 250, 500, float("inf")],
            labels=[
                "Up to £50",
                "£50–£100",
                "£100–£250",
                "£250–£500",
                "Above £500",
            ],
        )

        order_bands = (
            invoice_summary["Order_Value_Band"]
            .value_counts(sort=False)
            .rename_axis("Order Value")
            .reset_index(name="Invoice Count")
        )

        fig = px.bar(
            order_bands,
            x="Order Value",
            y="Invoice Count",
            title="Distribution of Invoice Values",
        )

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.caption(
        "AOV is calculated as eligible sales revenue divided "
        "by the number of unique eligible invoices."
    )

    st.divider()

    # -----------------------------------------------------
    # 3. RETURN ANALYSIS
    # -----------------------------------------------------

    st.markdown("### 3. Return Analysis")

    # Use filtered_df, not sales_df, because sales_df excludes
    # negative-quantity transactions.
    return_df = filtered_df[
        pd.to_numeric(
            filtered_df["Quantity"],
            errors="coerce"
        ) < 0
    ].copy()

    return_df["Return_Value"] = (
        pd.to_numeric(
            return_df["Revenue"],
            errors="coerce"
        ).abs()
    )

    return_rows = len(return_df)

    return_invoices = return_df["InvoiceNo"].nunique()

    return_units = pd.to_numeric(
        return_df["Quantity"],
        errors="coerce"
    ).abs().sum()

    return_value = return_df["Return_Value"].sum()

    eligible_sales_value = sales_df["Revenue"].sum()

    return_rate = (
        return_value / eligible_sales_value * 100
        if eligible_sales_value > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Return Transaction Rows",
        f"{return_rows:,}"
    )

    col2.metric(
        "Return Invoices",
        f"{return_invoices:,}"
    )

    col3.metric(
        "Returned Units",
        f"{return_units:,.0f}"
    )

    col4.metric(
        "Absolute Return Value",
        f"£{return_value:,.2f}"
    )

    st.caption(
        f"Return value as a percentage of eligible sales revenue: "
        f"{return_rate:.2f}%. This is a value ratio, not a confirmed "
        "customer return rate; negative quantities may include "
        "credit transactions and may not be linked to original sales."
    )

    if not return_df.empty:
        return_df["Month"] = (
            return_df["InvoiceTimestamp"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_returns = (
            return_df.groupby("Month", as_index=False)
            .agg(
                Return_Value=("Return_Value", "sum"),
                Return_Rows=("InvoiceNo", "size"),
            )
            .sort_values("Month")
        )

        fig = px.bar(
            monthly_returns,
            x="Month",
            y="Return_Value",
            title="Monthly Absolute Return Value",
            hover_data=["Return_Rows"],
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Month",
            yaxis_title="Return Value (£)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            return_df[
                [
                    "InvoiceNo",
                    "InvoiceTimestamp",
                    "Description",
                    "Quantity",
                    "UnitPrice",
                    "Revenue",
                    "Return_Value",
                    "Country",
                ]
            ].head(500),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Return Transactions (CSV)",
            data=return_df.to_csv(index=False).encode("utf-8"),
            file_name="dataverse_return_analysis.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "No negative-quantity transactions match the current filters."
        )

    st.divider()

    # -----------------------------------------------------
    # 4. COUNTRY COMPARISON
    # -----------------------------------------------------

    st.markdown("### 4. Country Performance Comparison")

    if sales_df.empty:
        st.info("No eligible sales data is available.")
    else:
        country_perf = (
            sales_df.groupby("Country", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoices=("InvoiceNo", "nunique"),
                Customers=("CustomerID", "nunique"),
                Units=("Quantity", "sum"),
            )
            .sort_values("Revenue", ascending=False)
        )

        st.dataframe(
            country_perf,
            use_container_width=True,
            hide_index=True,
        )

        top_countries = country_perf.head(10).sort_values("Revenue")

        fig = px.bar(
            top_countries,
            x="Revenue",
            y="Country",
            orientation="h",
            title="Top 10 Countries by Revenue",
            hover_data=["Invoices", "Customers", "Units"],
        )

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # -----------------------------------------------------
    # 5. PRODUCT COMPARISON
    # -----------------------------------------------------

    st.markdown("### 5. Product Performance Comparison")

    merchandise_df = sales_df[
        sales_df["Description"]
        .fillna("")
        .str.strip()
        .ne("")
        & ~sales_df["Description"]
        .fillna("")
        .str.upper()
        .str.contains("POSTAGE", regex=False)
    ].copy()

    if merchandise_df.empty:
        st.info("No merchandise data is available.")
    else:
        product_perf = (
            merchandise_df.groupby("Description", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Units_Sold=("Quantity", "sum"),
                Invoices=("InvoiceNo", "nunique"),
            )
            .sort_values("Revenue", ascending=False)
        )

        metric = st.selectbox(
            "Compare products by",
            ["Revenue", "Units_Sold", "Invoices"],
            key="performance_product_metric",
        )

        top_products = (
            product_perf
            .nlargest(10, metric)
            .sort_values(metric)
        )

        fig = px.bar(
            top_products,
            x=metric,
            y="Description",
            orientation="h",
            title=f"Top 10 Products by {metric.replace('_', ' ')}",
            hover_data=["Revenue", "Units_Sold", "Invoices"],
        )

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            product_perf,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Product Performance (CSV)",
            data=product_perf.to_csv(index=False).encode("utf-8"),
            file_name="dataverse_product_performance.csv",
            mime="text/csv",

        )



# =========================================================
# 14 (b) INTELLIGENCE AND ALERTS PAGE
# =========================================================

elif page == "Intelligence & Alerts":

    st.subheader("Intelligent Sales Monitoring")
    st.caption(
        "Rule-based anomaly detection and business alerts "
        "based on the currently selected filters."
    )

    if sales_df.empty:
        st.warning(
            "No eligible sales transactions match the current filters."
        )

    else:
        # -------------------------------------------------
        # 1. DAILY REVENUE ANOMALIES
        # -------------------------------------------------

        st.markdown("### 1. Daily Revenue Anomaly Detection")

        daily_df = sales_df.dropna(
            subset=["InvoiceTimestamp"]
        ).copy()

        daily_df["Sale_Date"] = (
            daily_df["InvoiceTimestamp"].dt.date
        )

        daily_revenue = (
            daily_df.groupby("Sale_Date", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoice_Count=("InvoiceNo", "nunique"),
            )
            .sort_values("Sale_Date")
        )

        if len(daily_revenue) < 4:
            st.info(
                "At least four days of sales are needed for "
                "the initial anomaly analysis."
            )

        else:
            q1 = daily_revenue["Revenue"].quantile(0.25)
            q3 = daily_revenue["Revenue"].quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            daily_revenue["Anomaly"] = (
                (daily_revenue["Revenue"] < lower_bound)
                | (daily_revenue["Revenue"] > upper_bound)
            )

            daily_revenue["Alert"] = daily_revenue[
                "Anomaly"
            ].map({
                True: "Unusual",
                False: "Normal",
            })

            anomaly_count = int(
                daily_revenue["Anomaly"].sum()
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Days Analyzed",
                f"{len(daily_revenue):,}"
            )

            col2.metric(
                "Unusual Revenue Days",
                f"{anomaly_count:,}"
            )

            col3.metric(
                "Upper Revenue Threshold",
                f"£{upper_bound:,.2f}"
            )

            fig = px.scatter(
                daily_revenue,
                x="Sale_Date",
                y="Revenue",
                color="Alert",
                size="Invoice_Count",
                hover_data=["Invoice_Count"],
                title="Daily Revenue with Potential Anomalies",
            )

            fig.add_hline(
                y=upper_bound,
                line_dash="dash",
                annotation_text="Upper threshold",
            )

            fig.add_hline(
                y=lower_bound,
                line_dash="dash",
                annotation_text="Lower threshold",
            )

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Revenue (£)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            unusual_days = daily_revenue[
                daily_revenue["Anomaly"]
            ].sort_values(
                "Revenue",
                ascending=False
            )

            if unusual_days.empty:
                st.success(
                    "No daily revenue anomalies were detected "
                    "by the current IQR rule."
                )
            else:
                st.markdown("#### Unusual Revenue Days")

                st.dataframe(
                    unusual_days,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download Daily Anomaly Report (CSV)",
                    data=unusual_days.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="dataverse_daily_anomalies.csv",
                    mime="text/csv",
                )

        st.caption(
            "Method: the interquartile range (IQR) rule flags "
            "daily revenue outside Q1 − 1.5 × IQR and "
            "Q3 + 1.5 × IQR. These are statistical outliers, "
            "not confirmed errors or fraud."
        )

        st.divider()

        # -------------------------------------------------
        # 2. HIGH-VALUE INVOICE DETECTION
        # -------------------------------------------------

        st.markdown("### 2. High-Value Invoice Detection")

        invoice_data = (
            sales_df.groupby("InvoiceNo", as_index=False)
            .agg(
                Invoice_Revenue=("Revenue", "sum"),
                Units=("Quantity", "sum"),
                Country=("Country", "first"),
                CustomerID=("CustomerID", "first"),
            )
        )

        if len(invoice_data) < 4:
            st.info(
                "More invoices are needed to identify "
                "statistical high-value outliers."
            )

        else:
            invoice_q1 = invoice_data[
                "Invoice_Revenue"
            ].quantile(0.25)

            invoice_q3 = invoice_data[
                "Invoice_Revenue"
            ].quantile(0.75)

            invoice_iqr = invoice_q3 - invoice_q1

            invoice_threshold = (
                invoice_q3 + 1.5 * invoice_iqr
            )

            high_value = invoice_data[
                invoice_data["Invoice_Revenue"]
                > invoice_threshold
            ].sort_values(
                "Invoice_Revenue",
                ascending=False
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "High-Value Invoices",
                f"{len(high_value):,}"
            )

            col2.metric(
                "High-Value Threshold",
                f"£{invoice_threshold:,.2f}"
            )

            if high_value.empty:
                st.info(
                    "No high-value invoice outliers were detected."
                )
            else:
                st.dataframe(
                    high_value.head(100),
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download High-Value Invoices (CSV)",
                    data=high_value.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="dataverse_high_value_invoices.csv",
                    mime="text/csv",
                )

        st.caption(
            "High-value invoices are defined as invoice revenue "
            "above Q3 + 1.5 × IQR. They may be legitimate bulk "
            "orders and should be reviewed in context."
        )

        st.divider()

        # -------------------------------------------------
        # 3. PRODUCT REVENUE CONCENTRATION
        # -------------------------------------------------

        st.markdown("### 3. Revenue Concentration")

        merchandise = sales_df[
            sales_df["Description"]
            .fillna("")
            .str.strip()
            .ne("")
            & ~sales_df["Description"]
            .fillna("")
            .str.upper()
            .str.contains("POSTAGE", regex=False)
        ].copy()

        if merchandise.empty:
            st.info(
                "No merchandise records are available for analysis."
            )

        else:
            product_revenue = (
                merchandise.groupby("Description")["Revenue"]
                .sum()
                .sort_values(ascending=False)
            )

            merchandise_total = product_revenue.sum()

            top_n = st.slider(
                "Number of leading products",
                min_value=5,
                max_value=30,
                value=10,
                step=5,
                key="intelligence_top_products",
            )

            leading_products = product_revenue.head(top_n)

            top_share = (
                leading_products.sum() / merchandise_total * 100
                if merchandise_total > 0
                else 0
            )

            col1, col2 = st.columns(2)

            col1.metric(
                f"Top {top_n} Product Revenue",
                f"£{leading_products.sum():,.2f}"
            )

            col2.metric(
                f"Top {top_n} Revenue Share",
                f"{top_share:.2f}%"
            )

            concentration_df = (
                leading_products
                .rename("Revenue")
                .reset_index()
                .sort_values("Revenue")
            )

            fig = px.bar(
                concentration_df,
                x="Revenue",
                y="Description",
                orientation="h",
                title=f"Revenue from Top {top_n} Products",
            )

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Revenue (£)",
                yaxis_title="Product",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            concentration_table = (
                product_revenue
                .rename("Revenue")
                .reset_index()
                .sort_values("Revenue", ascending=False)
            )

            concentration_table["Revenue Share (%)"] = (
                concentration_table["Revenue"]
                / merchandise_total * 100
                if merchandise_total > 0
                else 0
            )

            concentration_table["Cumulative Share (%)"] = (
                concentration_table["Revenue Share (%)"].cumsum()
            )

            st.markdown("#### Product Contribution")

            st.dataframe(
                concentration_table.head(100),
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download Product Concentration (CSV)",
                data=concentration_table.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="dataverse_revenue_concentration.csv",
                mime="text/csv",
            )

        st.divider()

        # -------------------------------------------------
        # 4. AUTOMATED BUSINESS ALERTS
        # -------------------------------------------------

        st.markdown("### 4. Automated Business Alerts")

        alerts = []

        if len(daily_revenue) >= 4:
            if anomaly_count > 0:
                alerts.append(
                    f"Review {anomaly_count} unusual revenue day(s). "
                    "Check invoice mix and transaction details."
                )
            else:
                alerts.append(
                    "No daily revenue outliers were detected "
                    "using the current IQR rule."
                )

        if len(invoice_data) >= 4:
            alerts.append(
                f"{len(high_value):,} invoice(s) exceed the "
                "statistical high-value threshold."
            )

        if not merchandise.empty and merchandise_total > 0:
            alerts.append(
                f"The top {top_n} products contribute "
                f"{top_share:.1f}% of merchandise revenue."
            )

        for alert in alerts:
            st.info(alert)

        st.caption(
            "These alerts are generated from statistical rules "
            "and descriptive metrics. They do not establish "
            "fraud, causation, or business risk by themselves."
        )



# =========================================================
# BUSINESS RECOMMENDATIONS PAGE
# =========================================================

elif page == "Business Recommendations":

    st.subheader("Business Recommendations Engine")

    st.caption(
        "Automated, rule-based observations and suggested actions "
        "based on the current dashboard filters."
    )

    if sales_df.empty:
        st.warning(
            "No eligible sales data matches the selected filters. "
            "Adjust the date range or country selection."
        )

    else:
        recommendations = generate_recommendations(sales_df)

        # Summary metrics
        high_count = sum(
            item["priority"] == "High"
            for item in recommendations
        )

        medium_count = sum(
            item["priority"] == "Medium"
            for item in recommendations
        )

        low_count = sum(
            item["priority"] == "Low"
            for item in recommendations
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("High Priority", high_count)
        col2.metric("Medium Priority", medium_count)
        col3.metric("Low Priority", low_count)

        st.divider()

        # Display recommendations
        st.markdown("### Recommended Business Actions")

        for number, item in enumerate(recommendations, start=1):

            priority = item["priority"]

            if priority == "High":
                st.error(
                    f"🔴 {number}. {item['category']} — {priority}"
                )

            elif priority == "Medium":
                st.warning(
                    f"🟠 {number}. {item['category']} — {priority}"
                )

            elif priority == "Low":
                st.info(
                    f"🔵 {number}. {item['category']} — {priority}"
                )

            else:
                st.info(
                    f"{number}. {item['category']} — {priority}"
                )

            st.markdown(f"**Finding:** {item['finding']}")
            st.markdown(f"**Suggested action:** {item['action']}")

            st.divider()

        # Download recommendations
        recommendation_df = pd.DataFrame(recommendations)

        st.download_button(
            label="Download Business Recommendations (CSV)",
            data=recommendation_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="dataverse_business_recommendations.csv",
            mime="text/csv",
        )

        st.caption(
            "These recommendations are generated by predefined rules. "
            "They support investigation and decision-making but do not "
            "prove causation or guarantee business outcomes."
        )

        
# =========================================================
# RECOMMENDATION HISTORY PAGE
# =========================================================

elif page == "Recommendation History":

    st.subheader("Recommendation History")
    st.caption(
        "Save recommendation snapshots, review previous findings, "
        "and compare how business recommendations change over time."
    )

    # Generate recommendations using the current global filters
    if sales_df.empty:
        st.warning(
            "No eligible sales data matches the current filters. "
            "Adjust the date range or country selection."
        )
    else:
        current_recommendations = generate_recommendations(sales_df)

        st.markdown("### Current Recommendation Snapshot")
        st.write(
            f"Current recommendations: {len(current_recommendations)}"
        )

        if st.button("Save Current Recommendations"):
            saved_run = save_recommendations(
                current_recommendations,
                context={
                    "date_start": str(start_date),
                    "date_end": str(end_date),
                    "selected_countries": selected_countries,
                    "source": "dashboard",
                },
            )

            st.success(
                f"Saved successfully! Run ID: {saved_run['run_id']}"
            )

    st.divider()

    # -----------------------------------------------------
    # PREVIOUS RUNS
    # -----------------------------------------------------

    st.markdown("### Saved Recommendation Runs")

    history = load_history()
    history_df = history_to_dataframe()

    metric1, metric2 = st.columns(2)

    metric1.metric("Saved Runs", len(history))
    metric2.metric("Recorded Recommendations", len(history_df))

    if history_df.empty:
        st.info(
            "No recommendation history is available yet. "
            "Generate recommendations and save a snapshot."
        )
    else:
        st.dataframe(
            history_df.sort_values(
                "Generated At",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            label="Download Recommendation History (CSV)",
            data=history_df.to_csv(index=False).encode("utf-8"),
            file_name="dataverse_recommendation_history.csv",
            mime="text/csv",
        )

    st.divider()

    # -----------------------------------------------------
    # COMPARE LATEST TWO RUNS
    # -----------------------------------------------------

    st.markdown("### Compare the Two Latest Runs")

    comparison = compare_latest_runs()

    if len(history) < 2:
        st.info(
            "Save at least two recommendation snapshots to compare "
            "new, repeated, and resolved recommendations."
        )
    else:
        col1, col2, col3 = st.columns(3)

        col1.metric("New", len(comparison["new"]))
        col2.metric("Repeated", len(comparison["repeated"]))
        col3.metric("Resolved", len(comparison["resolved"]))

        comparison_labels = [
            ("New Recommendations", "new"),
            ("Repeated Recommendations", "repeated"),
            ("Resolved Recommendations", "resolved"),
        ]

        for heading, key in comparison_labels:
            st.markdown(f"#### {heading}")

            items = comparison[key]

            if items:
                comparison_df = pd.DataFrame(
                    items,
                    columns=["Category", "Finding"],
                )

                st.dataframe(
                    comparison_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("None in this category.")

    st.caption(
        "Comparisons use category and finding text. A changed finding "
        "may appear as resolved in one run and new in another. "
        "These are rule-based comparisons, not proof that a business "
        "issue has actually been resolved."
    )


# =========================================================
# 14. ARCHITECTURE AND PROJECT METRICS
# =========================================================

elif page == "Architecture & Metrics":

    st.subheader("System Architecture & Project Metrics")

    st.write(
        "DATAVERSE NEXUS processes retail transactions through "
        "a data profiling, cleaning, storage, and visualization "
        "pipeline."
    )

    # -----------------------------------------------------
    # A. SYSTEM ARCHITECTURE
    # -----------------------------------------------------

    st.markdown("### Data Processing Architecture")

    architecture = """
    digraph DATAVERSE_NEXUS {
        graph [bgcolor="transparent", rankdir=TB, nodesep=0.35, ranksep=0.5]
        node [shape=box, style="rounded,filled", fontname="Arial",
              fontsize=11, margin="0.18,0.12",
              color="#60A5FA", fillcolor="#172554",
              fontcolor="white"]
        edge [color="#60A5FA", arrowsize=0.8]

        A [label="Online Retail CSV\\n541,909 source rows"]
        B [label="Data Profiling\\nSchema, duplicates, missing values"]
        C [label="PySpark Cleaning\\nDate parsing, validation, revenue"]
        D [label="Parquet Storage\\nProcessed dataset"]
        E [label="Pandas Analysis\\nFiltering and aggregation"]
        F [label="Streamlit Dashboard\\nInteractive pages and KPIs"]
        G [label="Plotly Visualizations\\nCharts and executive insights"]
        H [label="Export Reports\\nCSV and text report"]

        A -> B -> C -> D -> E -> F
        F -> G
        F -> H
    }
    """

    st.graphviz_chart(
        architecture,
        use_container_width=True
    )

    st.caption(
        "The diagram represents the implemented project flow. "
        "The dashboard reads the cleaned Parquet dataset; "
        "PySpark performs the current cleaning stage."
    )

    st.divider()

    # -----------------------------------------------------
    # B. TECHNOLOGY STACK
    # -----------------------------------------------------

    st.markdown("### Technology Stack")

    technology_data = [
        {
            "Technology": "Python",
            "Purpose": "Core programming language",
        },
        {
            "Technology": "Apache Spark / PySpark",
            "Purpose": "Distributed-style data processing and cleaning",
        },
        {
            "Technology": "Parquet",
            "Purpose": "Columnar storage for processed data",
        },
        {
            "Technology": "Pandas",
            "Purpose": "Dashboard-side analysis and aggregation",
        },
        {
            "Technology": "Streamlit",
            "Purpose": "Interactive web application",
        },
        {
            "Technology": "Plotly",
            "Purpose": "Interactive charts",
        },
    ]

    st.dataframe(
        pd.DataFrame(technology_data),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # -----------------------------------------------------
    # C. VERIFIED PROJECT METRICS
    # -----------------------------------------------------

    st.markdown("### Data Pipeline Metrics")

    report_path = (
        PROJECT_ROOT
        / "reports"
        / "data_quality_report.json"
    )

    if report_path.exists():

        with report_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            pipeline_report = json.load(file)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Source Rows",
            f"{pipeline_report['original_rows']:,}"
        )

        col2.metric(
            "Rows After Cleaning",
            f"{pipeline_report['final_rows']:,}"
        )

        col3.metric(
            "Duplicates Removed",
            f"{pipeline_report['exact_duplicates_removed']:,}"
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Columns After Cleaning",
            f"{pipeline_report['columns_after_cleaning']}"
        )

        col5.metric(
            "Invalid Invoice Dates",
            f"{pipeline_report['invalid_invoice_date']:,}"
        )

        col6.metric(
            "Processing Time",
            f"{pipeline_report['processing_time_seconds']:.2f} sec"
        )

        st.caption(
            "These metrics come from the most recently saved "
            "data-cleaning report. Processing time can vary "
            "between runs."
        )

        st.download_button(
            label="Download Pipeline Metrics (JSON)",
            data=json.dumps(
                pipeline_report,
                indent=2
            ),
            file_name="DATAVERSE_NEXUS_Pipeline_Metrics.json",
            mime="application/json",
        )

    else:
        st.warning(
            "Pipeline report not found. Run "
            "`python -m engine.cleaning` first."
        )

    st.divider()

    # -----------------------------------------------------
    # D. PROJECT SUMMARY
    # -----------------------------------------------------

    st.markdown("### Project Summary")

    st.write(
        "**Objective:** Transform raw retail transaction data "
        "into a cleaned, reusable dataset and interactive "
        "business analytics dashboard."
    )

    st.write(
        "**Current capabilities:** Data profiling, duplicate "
        "removal, date parsing, data-quality flags, revenue "
        "calculation, interactive sales analysis, executive "
        "insights, and downloadable reports."
    )

    st.info(
        "This project runs locally. Although PySpark supports "
        "distributed processing, this configuration uses "
        "local mode (`local[*]`), not a multi-node cluster."
    )


# =====================================================
# 14A. PDF EXECUTIVE REPORT PAGE
# =====================================================

elif page == "PDF Executive Report":

    st.subheader("PDF Executive Report")

    st.write(
        "Generate a professional executive report containing "
        "business KPIs, revenue trends, country performance, "
        "product performance, daily anomalies, and data quality."
    )

    st.divider()

    if sales_df.empty:
        st.warning(
            "No eligible sales transactions are available "
            "for the selected filters."
        )

    else:
        # 1. Prepare monthly revenue
        pdf_sales = sales_df.dropna(
            subset=["InvoiceTimestamp"]
        ).copy()

        pdf_sales["Month"] = (
            pdf_sales["InvoiceTimestamp"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly_sales = (
            pdf_sales.groupby("Month", as_index=False)["Revenue"]
            .sum()
            .sort_values("Month")
        )

        # 2. Prepare country performance
        country_sales = (
            sales_df.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .sort_values("Revenue", ascending=False)
        )

        # 3. Prepare merchandise product performance
        merchandise_sales = sales_df[
            sales_df["Description"]
            .fillna("")
            .str.strip()
            .ne("")
            & ~sales_df["Description"]
            .fillna("")
            .str.upper()
            .str.contains("POSTAGE", regex=False)
        ]

        product_sales = (
            merchandise_sales
            .groupby("Description", as_index=False)["Revenue"]
            .sum()
            .sort_values("Revenue", ascending=False)
        )

        # 4. Prepare daily revenue anomaly summary
        pdf_daily = pdf_sales.copy()

        pdf_daily["Sale_Date"] = (
            pdf_daily["InvoiceTimestamp"].dt.date
        )

        anomaly_summary = (
            pdf_daily.groupby("Sale_Date", as_index=False)
            .agg(
                Revenue=("Revenue", "sum"),
                Invoice_Count=("InvoiceNo", "nunique"),
            )
            .sort_values("Sale_Date")
        )

        if len(anomaly_summary) >= 4:
            q1 = anomaly_summary["Revenue"].quantile(0.25)
            q3 = anomaly_summary["Revenue"].quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            anomaly_summary["Anomaly"] = (
                (anomaly_summary["Revenue"] < lower_bound)
                | (anomaly_summary["Revenue"] > upper_bound)
            )

            anomaly_summary["Alert"] = anomaly_summary[
                "Anomaly"
            ].map({
                True: "Unusual",
                False: "Normal",
            })

        else:
            anomaly_summary["Alert"] = "Normal"

        # 5. Load saved data quality report
        quality_report_path = (
            PROJECT_ROOT / "reports" / "data_quality_report.json"
        )

        if quality_report_path.exists():
            with quality_report_path.open(
                "r",
                encoding="utf-8"
            ) as file:
                saved_quality_report = json.load(file)
        else:
            saved_quality_report = {}

        st.markdown("### Report Preview")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Revenue", f"£{total_revenue:,.2f}")
        col2.metric("Total Invoices", f"{total_invoices:,}")
        col3.metric("Unique Customers", f"{total_customers:,}")

        st.info(
            "The PDF will use your currently selected date range "
            "and countries from the Global Filters."
        )

        # 6. Generate PDF
        if st.button(
            "Generate PDF Executive Report",
            type="primary",
            use_container_width=True
        ):
            try:
                pdf_bytes = generate_executive_pdf(
                    total_revenue=total_revenue,
                    total_invoices=total_invoices,
                    total_customers=total_customers,
                    total_units=total_units,
                    monthly_sales=monthly_sales,
                    country_sales=country_sales,
                    product_sales=product_sales,
                    quality_report=saved_quality_report,
                    anomaly_summary=anomaly_summary,
                    date_start=start_date,
                    date_end=end_date,
                )

                st.success("Your executive PDF report is ready!")

                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="DATAVERSE_NEXUS_Executive_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            except Exception as error:
                st.error(
                    f"Could not generate the PDF report: {error}"
                )


# =========================================================
# 15. FOOTER
# =========================================================

st.divider()

st.caption(
    "DATAVERSE NEXUS | Big Data Analytics Project | "
    "Built with PySpark, Streamlit, Pandas, and Plotly"
)

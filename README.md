# DATAVERSE NEXUS
### The Intelligent Big Data Discovery Platform

DATAVERSE NEXUS is an interactive Big Data Analytics platform built using PySpark, Python, Streamlit, Pandas, and Plotly. It processes retail transaction data, evaluates data quality, discovers business trends, and generates actionable business recommendations.

## Key Features

- **Big Data Profiling:** Analyze dataset size, schema, missing values, and duplicate records using PySpark.
- **Data Cleaning:** Remove exact duplicates, parse invoice dates, calculate revenue, and identify data-quality issues.
- **Parquet Storage:** Store processed datasets in columnar Parquet format.
- **Interactive Dashboard:** Explore business performance through interactive charts and filters.
- **Sales Analysis:** Investigate revenue trends and sales performance.
- **Product Analysis:** Identify top-performing products and product concentration.
- **Country Analysis:** Compare revenue contributions across countries.
- **Data Quality Monitoring:** Examine missing values, returns, invalid records, and other quality indicators.
- **Business Intelligence:** Generate rule-based recommendations from sales data.
- **Recommendation History:** Save, review, and compare recommendation snapshots.
- **PDF Executive Report:** Generate downloadable analytical reports.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming |
| PySpark | Distributed data processing |
| Pandas | Data manipulation |
| Streamlit | Dashboard interface |
| Plotly | Interactive visualizations |
| Matplotlib | PDF charts |
| ReportLab | PDF report generation |
| Parquet | Processed data storage |
| Pytest | Automated testing |

## Project Structure

```text
DATAVERSE_NEXUS/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/
│   │   └── Online Retail.csv
│   └── processed/
│       └── online_retail_parquet/
│
├── engine/
│   ├── cleaning.py
│   ├── pipeline.py
│   ├── business_recommendations.py
│   └── recommendation_history.py
│
├── reports/
│   ├── data_profile.json
│   ├── data_quality_report.json
│   └── recommendation_history.json
│
└── tests/
    ├── test_pipeline.py
    ├── test_cleaning.py
    ├── test_business_recommendations.py
    └── test_recommendation_history.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd DATAVERSE_NEXUS
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure Java and Hadoop on Windows

DATAVERSE NEXUS uses PySpark. Configure a compatible Java installation and Hadoop Windows utilities.

Example PowerShell configuration:

```powershell
$env:JAVA_HOME = "YOUR_JAVA_INSTALLATION_PATH"
$env:HADOOP_HOME = "C:\hadoop"
$env:Path = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;$env:Path"
```

Ensure `winutils.exe` and `hadoop.dll` are available inside `C:\hadoop\bin`.

### 5. Add the dataset

Place the Online Retail dataset at:

```text
data/raw/Online Retail.csv
```

### 6. Run data profiling

```powershell
python -m engine.pipeline
```

### 7. Run data cleaning

```powershell
python -m engine.cleaning
```

### 8. Launch the dashboard

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in your terminal.

## Automated Testing

Run all project tests:

```powershell
python -m pytest tests -v
```

Current test coverage includes:

- Business recommendation rules
- Recommendation history storage and comparison
- PySpark data cleaning
- PySpark dataset profiling

**Current verified result: 11 tests passed, 0 failed.**

## Dataset

The project uses the Online Retail transaction dataset, containing retail transaction records with invoice, product, quantity, price, customer, and country information.

## Project Objective

The objective is to demonstrate how big data processing, data quality analysis, interactive visualization, and rule-based business intelligence can be integrated into a single analytical platform.

## Disclaimer

Business recommendations are generated using predefined analytical rules and thresholds. They support investigation and decision-making but do not establish causation or guarantee business outcomes.
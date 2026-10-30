
from pathlib import Path
import json
import time

from pyspark.sql import SparkSession, functions as F


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "Online Retail.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "online_retail_parquet"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORT_DIR / "data_quality_report.json"


# ============================================================
# 2. CREATE SPARK SESSION
# ============================================================

def create_spark():
    return (
        SparkSession.builder
        .appName("DATAVERSE_NEXUS_Cleaning")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config(
            "spark.hadoop.fs.file.impl",
            "org.apache.hadoop.fs.RawLocalFileSystem"
        )
        .getOrCreate()
    )


# ============================================================
# 3. CLEAN AND PROCESS DATASET
# ============================================================

def clean_dataset(spark):

    start = time.perf_counter()

    # --------------------------------------------------------
    # STEP 1: READ RAW DATASET
    # --------------------------------------------------------

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .option("mode", "PERMISSIVE")
        .csv(str(INPUT_FILE))
    )

    original_rows = df.count()

    # --------------------------------------------------------
    # STEP 2: REMOVE EXACT DUPLICATES
    # --------------------------------------------------------

    df = df.dropDuplicates()

    rows_after_deduplication = df.count()

    duplicates_removed = original_rows - rows_after_deduplication

    # --------------------------------------------------------
    # STEP 3: CLEAN TEXT AND PARSE INVOICE DATE
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "InvoiceNo",
            F.trim(F.col("InvoiceNo").cast("string"))
        )
        .withColumn(
            "StockCode",
            F.trim(F.col("StockCode").cast("string"))
        )
        .withColumn(
            "Description",
            F.trim(F.col("Description").cast("string"))
        )
        .withColumn(
            "Country",
            F.trim(F.col("Country").cast("string"))
        )
        .withColumn(
            "InvoiceTimestamp",
            F.to_timestamp(
                F.col("InvoiceDate").cast("string"),
                "dd/MM/yy HH:mm"
            )
        )
    )

    # --------------------------------------------------------
    # STEP 4: CREATE BUSINESS AND DATA-QUALITY COLUMNS
    # --------------------------------------------------------

    df = (
        df
        .withColumn(
            "Revenue",
            F.col("Quantity").cast("double")
            * F.col("UnitPrice").cast("double")
        )
        .withColumn(
            "MissingDescription",
            F.col("Description").isNull()
            | (F.col("Description") == "")
        )
        .withColumn(
            "MissingCustomerID",
            F.col("CustomerID").isNull()
        )
        .withColumn(
            "InvalidInvoiceDate",
            F.col("InvoiceTimestamp").isNull()
        )
        .withColumn(
            "NegativeQuantity",
            F.col("Quantity") < 0
        )
        .withColumn(
            "NegativeUnitPrice",
            F.col("UnitPrice") < 0
        )
        .withColumn(
            "MissingCriticalFields",
            F.col("InvoiceNo").isNull()
            | (F.col("InvoiceNo") == "")
            | F.col("StockCode").isNull()
            | (F.col("StockCode") == "")
            | F.col("Quantity").isNull()
            | F.col("UnitPrice").isNull()
        )
    )

    # --------------------------------------------------------
    # STEP 5: CALCULATE DATA-QUALITY STATISTICS
    # --------------------------------------------------------

    total_rows = df.count()

    stats = df.agg(
        F.sum(
            F.col("MissingDescription").cast("long")
        ).alias("missing_description"),

        F.sum(
            F.col("MissingCustomerID").cast("long")
        ).alias("missing_customer_id"),

        F.sum(
            F.col("InvalidInvoiceDate").cast("long")
        ).alias("invalid_invoice_date"),

        F.sum(
            F.col("NegativeQuantity").cast("long")
        ).alias("negative_quantity"),

        F.sum(
            F.col("NegativeUnitPrice").cast("long")
        ).alias("negative_unit_price"),

        F.sum(
            F.col("MissingCriticalFields").cast("long")
        ).alias("missing_critical_fields"),

        F.sum(
            F.when(F.col("Revenue").isNull(), 1).otherwise(0)
        ).alias("null_revenue")
    ).first()

    # --------------------------------------------------------
    # STEP 6: BUILD QUALITY REPORT
    # --------------------------------------------------------

    quality_report = {
        "input_file": INPUT_FILE.name,
        "original_rows": original_rows,
        "rows_after_deduplication": rows_after_deduplication,
        "exact_duplicates_removed": duplicates_removed,
        "final_rows": total_rows,
        "columns_after_cleaning": len(df.columns),

        "missing_description": int(
            stats["missing_description"] or 0
        ),
        "missing_customer_id": int(
            stats["missing_customer_id"] or 0
        ),
        "invalid_invoice_date": int(
            stats["invalid_invoice_date"] or 0
        ),
        "negative_quantity_rows": int(
            stats["negative_quantity"] or 0
        ),
        "negative_unit_price_rows": int(
            stats["negative_unit_price"] or 0
        ),
        "missing_critical_fields": int(
            stats["missing_critical_fields"] or 0
        ),
        "null_revenue_rows": int(
            stats["null_revenue"] or 0
        ),

        "processing_time_seconds": round(
            time.perf_counter() - start, 2
        ),
        "output_format": "Parquet",
        "output_path": str(OUTPUT_DIR)
    }

    # --------------------------------------------------------
    # STEP 7: SAVE CLEANED DATA AS PARQUET
    # --------------------------------------------------------

    OUTPUT_DIR.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        df.write
        .mode("overwrite")
        .parquet(str(OUTPUT_DIR))
    )

    # --------------------------------------------------------
    # STEP 8: SAVE QUALITY REPORT AS JSON
    # --------------------------------------------------------

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            quality_report,
            file,
            indent=2
        )

    return quality_report


# ============================================================
# 4. MAIN FUNCTION
# ============================================================

def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    spark = create_spark()

    try:

        spark.sparkContext.setLogLevel("WARN")

        print("\nDATAVERSE NEXUS — DATA CLEANING")
        print("=" * 42)

        report = clean_dataset(spark)

        print(f"Original rows: {report['original_rows']:,}")

        print(
            "Exact duplicates removed: "
            f"{report['exact_duplicates_removed']:,}"
        )

        print(f"Final rows: {report['final_rows']:,}")

        print(
            "Columns after cleaning: "
            f"{report['columns_after_cleaning']}"
        )

        print(
            "Missing descriptions: "
            f"{report['missing_description']:,}"
        )

        print(
            "Missing Customer IDs: "
            f"{report['missing_customer_id']:,}"
        )

        print(
            "Invalid invoice dates: "
            f"{report['invalid_invoice_date']:,}"
        )

        print(
            "Negative quantity rows: "
            f"{report['negative_quantity_rows']:,}"
        )

        print(
            "Negative unit price rows: "
            f"{report['negative_unit_price_rows']:,}"
        )

        print(
            "Missing critical fields: "
            f"{report['missing_critical_fields']:,}"
        )

        print(
            "Null revenue rows: "
            f"{report['null_revenue_rows']:,}"
        )

        print(
            "Processing time: "
            f"{report['processing_time_seconds']} seconds"
        )

        print(f"\nParquet saved to:\n{OUTPUT_DIR}")
        print(f"Quality report saved to:\n{REPORT_FILE}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()


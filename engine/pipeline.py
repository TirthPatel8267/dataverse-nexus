
from pathlib import Path
import json
import time

from pyspark.sql import SparkSession, functions as F


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "Online Retail.csv"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORT_DIR / "data_profile.json"


def create_spark():
    return (
        SparkSession.builder
        .appName("DATAVERSE_NEXUS_Profiler")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def profile_dataset(spark, file_path):
    start = time.perf_counter()

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .option("mode", "PERMISSIVE")
        .csv(str(file_path))
    )

    row_count = df.count()
    column_names = df.columns

    missing_row = df.agg(
        *[
            F.sum(
                F.when(
                    F.col(column).isNull()
                    | (
                        F.trim(F.col(column).cast("string")) == ""
                    ),
                    1,
                ).otherwise(0)
            ).alias(f"missing_{index}")
            for index, column in enumerate(column_names)
        ]
    ).first()

    missing_values = {
        column: int(missing_row[f"missing_{index}"] or 0)
        for index, column in enumerate(column_names)
    }

    duplicate_count = row_count - df.dropDuplicates().count()

    elapsed_seconds = round(time.perf_counter() - start, 2)

    report = {
        "file_name": Path(file_path).name,
        "total_rows": row_count,
        "total_columns": len(column_names),
        "duplicate_rows": duplicate_count,
        "missing_values": missing_values,
        "schema": [
            {
                "column": field.name,
                "data_type": str(field.dataType),
            }
            for field in df.schema.fields
        ],
        "profiling_time_seconds": elapsed_seconds,
    }

    return df, report


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    spark = create_spark()

    try:
        spark.sparkContext.setLogLevel("WARN")

        print("\nDATAVERSE NEXUS — DATA PROFILER")
        print("=" * 40)

        df, report = profile_dataset(spark, INPUT_FILE)

        print(f"File: {report['file_name']}")
        print(f"Rows: {report['total_rows']:,}")
        print(f"Columns: {report['total_columns']}")
        print(f"Duplicate rows: {report['duplicate_rows']:,}")
        print(
            f"Profiling time: "
            f"{report['profiling_time_seconds']} seconds"
        )

        print("\nSCHEMA")
        df.printSchema()

        print("\nMISSING VALUES")
        for column, count in report["missing_values"].items():
            print(f"{column}: {count:,}")

        with REPORT_FILE.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)

        print(f"\nReport saved to: {REPORT_FILE}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

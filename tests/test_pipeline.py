
import pytest
from pyspark.sql import SparkSession

from engine.pipeline import profile_dataset


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("DATAVERSE_NEXUS_Profiler_Tests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    yield session
    session.stop()


def test_profile_dataset_calculates_correct_statistics(
    spark, tmp_path
):
    csv_file = tmp_path / "sample.csv"

    csv_file.write_text(
        "InvoiceNo,Description,Quantity\n"
        "1001,Product A,2\n"
        "1001,Product A,2\n"
        "1002,,1\n",
        encoding="utf-8",
    )

    df, report = profile_dataset(spark, csv_file)

    assert report["file_name"] == "sample.csv"
    assert report["total_rows"] == 3
    assert report["total_columns"] == 3
    assert report["duplicate_rows"] == 1

    assert report["missing_values"]["Description"] == 1
    assert report["missing_values"]["InvoiceNo"] == 0

    assert len(report["schema"]) == 3
    assert report["profiling_time_seconds"] >= 0

    assert df.count() == 3


def test_profile_dataset_detects_column_names(spark, tmp_path):
    csv_file = tmp_path / "columns.csv"

    csv_file.write_text(
        "Product,Price\n"
        "Phone,500\n"
        "Laptop,1000\n",
        encoding="utf-8",
    )

    df, report = profile_dataset(spark, csv_file)

    assert df.columns == ["Product", "Price"]
    assert report["total_columns"] == 2
    assert report["total_rows"] == 2
    assert report["duplicate_rows"] == 0

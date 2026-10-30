
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from engine import cleaning


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("DATAVERSE_NEXUS_Tests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")

    yield session
    session.stop()


def test_clean_dataset_removes_exact_duplicates(
    spark, tmp_path, monkeypatch
):
    input_file = tmp_path / "sample.csv"
    output_dir = tmp_path / "processed"
    report_dir = tmp_path / "reports"

    input_file.write_text(
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,"
        "UnitPrice,CustomerID,Country\n"
        "1001,A1,Product A,2,01/01/26 10:00,5.0,12345,UK\n"
        "1001,A1,Product A,2,01/01/26 10:00,5.0,12345,UK\n"
        "1002,B2,Product B,-1,02/01/26 11:00,10.0,,France\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cleaning, "INPUT_FILE", input_file)
    monkeypatch.setattr(cleaning, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        cleaning,
        "REPORT_DIR",
        report_dir,
    )
    monkeypatch.setattr(
        cleaning,
        "REPORT_FILE",
        report_dir / "quality.json",
    )

    report = cleaning.clean_dataset(spark)

    assert report["original_rows"] == 3
    assert report["exact_duplicates_removed"] == 1
    assert report["final_rows"] == 2
    assert report["negative_quantity_rows"] == 1
    assert report["missing_customer_id"] == 1
    assert output_dir.exists()
    assert (report_dir / "quality.json").exists()



def test_cleaned_parquet_can_be_read(spark, tmp_path, monkeypatch):
    input_file = tmp_path / "sample.csv"
    output_dir = tmp_path / "processed"
    report_dir = tmp_path / "reports"
    report_file = report_dir / "quality.json"

    input_file.write_text(
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,"
        "UnitPrice,CustomerID,Country\n"
        "2001,A1,Product A,3,01/01/26 10:00,4.0,12345,UK\n",
        encoding="utf-8",
    )

    # Redirect every output to the temporary test directory.
    monkeypatch.setattr(cleaning, "INPUT_FILE", input_file)
    monkeypatch.setattr(cleaning, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(cleaning, "REPORT_DIR", report_dir)
    monkeypatch.setattr(cleaning, "REPORT_FILE", report_file)

    cleaning.clean_dataset(spark)

    result = spark.read.parquet(str(output_dir))

    assert result.count() == 1
    assert "Revenue" in result.columns
    assert result.first()["Revenue"] == 12.0

    # Confirm that the test report was saved in the temporary directory.
    assert report_file.exists()


    result = spark.read.parquet(str(output_dir))

    assert result.count() == 1
    assert "Revenue" in result.columns
    assert result.first()["Revenue"] == 12.0

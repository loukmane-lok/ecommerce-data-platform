import os
import shutil

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, TimestampType, DateType
from orders_transformer import (
    validate_schema, cast_types, handle_nulls,
    filter_invalid_ranges, deduplicate, add_derived_columns
)

@pytest.fixture(scope="session")
def spark():
    java_bin = shutil.which("java")
    if java_bin:
        os.environ["JAVA_HOME"] = os.path.dirname(os.path.dirname(os.path.realpath(java_bin)))

    return (SparkSession.builder
            .master("local[1]")
            .appName("test_transformations")
            .getOrCreate())

def test_validate_schema_drops_unexpected_column(spark):
    df = spark.createDataFrame(
        [("ord-1", "u-1", "p-1", "electronics", "19.99",
          "2", "2024-01-15T14:30:00Z", "completed", "US", "EXTRA")],
        ["order_id", "user_id", "product_id", "category", "price",
         "quantity", "timestamp", "status", "country", "unexpected_field"]
    )
    EXPECTED = ["order_id", "user_id", "product_id", "category", "price",
                "quantity", "timestamp", "status", "country"]

    result = validate_schema(df, EXPECTED)

    assert "unexpected_field" not in result.columns

def test_validate_schema_raises_on_missing_required_column(spark):
    df = spark.createDataFrame(
        [("u-1", "p-1", "electronics")],
        ["user_id", "product_id", "category"]
    )
    EXPECTED = ["order_id", "user_id", "product_id", "category", "price",
                "quantity", "timestamp", "status", "country"]

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(df, EXPECTED)

def test_cast_types_price_is_double(spark):
    df = spark.createDataFrame(
        [("ord-1", "19.99", "2", "2024-01-15T14:30:00Z")],
        ["order_id", "price", "quantity", "timestamp"]
    )

    result = cast_types(df)

    assert result.schema["price"].dataType == DoubleType()

def test_cast_types_timestamp_is_timestamp(spark):
    df = spark.createDataFrame(
        [("ord-1", "19.99", "2", "2024-01-15T14:30:00Z")],
        ["order_id", "price", "quantity", "timestamp"]
    )

    result = cast_types(df)

    assert result.schema["timestamp"].dataType == TimestampType()


def test_handle_nulls_drops_null_order_id(spark):
    import pyspark.sql.functions as F

    df = spark.createDataFrame(
        [("ord-1", "2024-01-15T14:30:00Z", "completed", "US"),
         (None,    "2024-01-15T14:30:00Z", "completed", "UK"),
         ("ord-3", "2024-01-15T14:30:00Z", "completed", "DE")],
        ["order_id", "timestamp", "status", "country"]
    )

    result = handle_nulls(df)

    assert result.count() == 2
    
def test_handle_nulls_fills_null_status(spark):
    import pyspark.sql.functions as F

    df = spark.createDataFrame(
        [("ord-1", "2024-01-15T14:30:00Z", "completed", "US"),
         ("ord-2", "2024-01-15T14:30:00Z", None,        "UK"),
         ("ord-3", "2024-01-15T14:30:00Z", "pending",   "DE")],
        ["order_id", "timestamp", "status", "country"]
    )

    result = handle_nulls(df)

    assert result.count() == 3
    assert result.filter(F.col("status").isNull()).count() == 0
    assert result.filter(F.col("status") == "unknown").count() == 1
    
def test_filter_invalid_ranges_drops_negative_price(spark):
    df = spark.createDataFrame(
        [("ord-1", -5.0,  2),
         ("ord-2", 19.99, 2),
         ("ord-3", 49.99, 1)],
        ["order_id", "price", "quantity"]
    )

    result = filter_invalid_ranges(df)

    assert result.count() == 2

def test_deduplicate_keeps_earliest_timestamp(spark):
    from pyspark.sql.types import TimestampType
    import pyspark.sql.functions as F

    df = spark.createDataFrame(
        [("ord-1", "2024-01-15T14:30:00Z"),
         ("ord-1", "2024-01-15T15:00:00Z"),
         ("ord-2", "2024-01-15T16:00:00Z")],
        ["order_id", "timestamp"]
    )
    df = df.withColumn("timestamp", F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm:ss'Z'"))

    result = deduplicate(df)
    kept = result.filter(F.col("order_id") == "ord-1").collect()[0]

    assert result.count() == 2
    assert kept["timestamp"].hour == 14
    
def test_add_derived_columns_order_value(spark):
    import pyspark.sql.functions as F

    df = spark.createDataFrame(
        [("ord-1", 10.0, 3)],
        ["order_id", "price", "quantity"]
    )
    df = df.withColumn("timestamp", F.lit("2024-01-15T14:30:00Z"))
    df = df.withColumn("timestamp", F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm:ss'Z'"))

    result = add_derived_columns(df)
    row = result.collect()[0]

    assert row["order_value"] == 30.0
    
def test_add_derived_columns_order_date_type(spark):
    import pyspark.sql.functions as F

    df = spark.createDataFrame(
        [("ord-1", 10.0, 3)],
        ["order_id", "price", "quantity"]
    )
    df = df.withColumn("timestamp", F.lit("2024-01-15T14:30:00Z"))
    df = df.withColumn("timestamp", F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm:ss'Z'"))

    result = add_derived_columns(df)

    assert result.schema["order_date"].dataType == DateType()
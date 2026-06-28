from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, TimestampType
from pyspark.sql.window import Window

def log_count(df, step_name):
    """
    Counts rows in df, prints a labeled message, and returns the count.
    Call this after every transformation step.
    """
    count = df.count()
    print(f"STEP [{step_name}]: {count} rows")
    return count

def validate_schema(df, expected_columns):
    """
    Drops unexpected columns, raises ValueError if a required column is missing.
    """
    actual_columns = set(df.columns)
    expected_set = set(expected_columns)

    missing = expected_set - actual_columns
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    extra = actual_columns - expected_set
    if extra:
        print(f"WARNING: Dropping unexpected columns: {extra}")
        df = df.select(expected_columns)

    return df


def cast_types(df):
    """
    Casts price → Double, quantity → Integer, timestamp → Timestamp.
    All other columns remain StringType.
    """
    df = df.withColumn("price", F.col("price").cast(DoubleType()))
    df = df.withColumn("quantity", F.col("quantity").cast(IntegerType()))
    df = df.withColumn(
        "timestamp",
        F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX")
    )
    return df

def handle_nulls(df):
    """
    Drops rows with null order_id or timestamp (unrecoverable).
    Fills null status and country with 'unknown' (safe default).
    """
    df = df.filter(F.col("order_id").isNotNull())
    df = df.filter(F.col("timestamp").isNotNull())

    df = df.fillna({"status": "unknown", "country": "unknown"})

    return df

def filter_invalid_ranges(df):
    """
    Drops rows with price or quantity outside agreed business rule bounds.
    price: must be > 0.0 and <= 10000.0
    quantity: must be >= 1 and <= 10
    """
    df = df.filter(F.col("price") > 0.0)
    df = df.filter(F.col("price") <= 10000.0)
    df = df.filter(F.col("quantity") >= 1)
    df = df.filter(F.col("quantity") <= 10)

    return df


def deduplicate(df):
    """
    Keeps one row per order_id — the one with the earliest timestamp.
    Uses a Window function for deterministic, rule-based deduplication.
    """
    window_spec = (Window
        .partitionBy("order_id")
        .orderBy(F.col("timestamp").asc()))

    df = df.withColumn("row_num", F.row_number().over(window_spec))
    df = df.filter(F.col("row_num") == 1)
    df = df.drop("row_num")

    return df

def add_derived_columns(df):
    """
    Adds order_value (price * quantity) and order_date (date part of timestamp).
    Called last — operates on already-cleaned data only.
    """
    df = df.withColumn(
        "order_value",
        (F.col("price") * F.col("quantity")).cast(DoubleType())
    )
    df = df.withColumn(
        "order_date",
        F.to_date(F.col("timestamp"))
    )
    return df


def run_pipeline(df, logger=print):
    """
    Runs all transformation steps in order.
    Logs row counts after every step.
    Returns the final cleaned DataFrame.
    """
    EXPECTED_COLUMNS = [
        "order_id", "user_id", "product_id", "category",
        "price", "quantity", "timestamp", "status", "country"
    ]

    df = validate_schema(df, EXPECTED_COLUMNS)
    log_count(df, "validate_schema")

    df = cast_types(df)
    log_count(df, "cast_types")

    df = handle_nulls(df)
    log_count(df, "handle_nulls")

    df = filter_invalid_ranges(df)
    log_count(df, "filter_invalid_ranges")

    df = deduplicate(df)
    log_count(df, "deduplicate")

    df = add_derived_columns(df)
    log_count(df, "add_derived_columns")

    return df
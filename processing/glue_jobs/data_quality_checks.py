
import json
import logging
from datetime import datetime, timezone
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def completeness_check(df, column, threshold):
    total = df.count()
    non_null = df.filter(F.col(column).isNotNull()).count()
    value = round(non_null / total, 4) if total > 0 else 0.0
    result = "PASS" if value >= threshold else "FAIL"

    log_entry = {
        "check": "completeness",
        "column": column,
        "value": value,
        "threshold": threshold,
        "result": result
    }
    logger.info(json.dumps(log_entry))
    return result
def uniqueness_check(df, primary_key_column):
    total = df.count()
    distinct = df.select(primary_key_column).distinct().count()
    duplicates = total - distinct

    result = "PASS" if duplicates == 0 else "FAIL"

    log_entry = {
        "check": "uniqueness",
        "column": primary_key_column,
        "duplicates": duplicates,
        "result": result
    }
    logger.info(json.dumps(log_entry))
    return result

def freshness_check(df, timestamp_column, max_age_hours=24):
    max_ts = df.agg(F.max(F.col(timestamp_column))).collect()[0][0]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    age_hours = round((now - max_ts).total_seconds() / 3600, 2)

    result = "PASS" if age_hours <= max_age_hours else "FAIL"

    log_entry = {
        "check": "freshness",
        "column": timestamp_column,
        "max_age_hours": max_age_hours,
        "actual_age_hours": age_hours,
        "result": result
    }
    logger.info(json.dumps(log_entry))
    return result

def range_check(df, column, min_val, max_val):
    out_of_range = df.filter(
        (F.col(column) < min_val) | (F.col(column) > max_val)
    ).count()

    result = "PASS" if out_of_range == 0 else "FAIL"

    log_entry = {
        "check": "range",
        "column": column,
        "min": min_val,
        "max": max_val,
        "out_of_range_count": out_of_range,
        "result": result
    }
    logger.info(json.dumps(log_entry))
    return result

def run_all_checks(df):
    results = []

    results.append(completeness_check(df, "order_id", threshold=1.0))
    results.append(completeness_check(df, "country", threshold=0.95))
    results.append(uniqueness_check(df, "order_id"))
    results.append(freshness_check(df, "timestamp", max_age_hours=24))
    results.append(range_check(df, "price", min_val=0.01, max_val=10000.0))
    results.append(range_check(df, "quantity", min_val=1, max_val=10))

    passed = results.count("PASS")
    failed = results.count("FAIL")

    summary = {
        "total_checks": len(results),
        "passed": passed,
        "failed": failed
    }
    logger.info(json.dumps(summary))
    return results

if __name__ == "__main__":
    import sys
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
    from pyspark.context import SparkContext

    args = getResolvedOptions(sys.argv, ["JOB_NAME", "CURATED_PATH"])

    sc = SparkContext.getOrCreate()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args["JOB_NAME"], args)

    df = spark.read.parquet(args["CURATED_PATH"])
    run_all_checks(df)
    job.commit()
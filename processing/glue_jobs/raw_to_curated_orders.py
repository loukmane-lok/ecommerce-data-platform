import sys
import logging
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

from orders_transformer import run_pipeline

# ── Bootstrap ──────────────────────────────────────────────────────────────
args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_PATH", "CURATED_PATH"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ── Read ────────────────────────────────────────────────────────────────────
raw_dynamic_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": [args["RAW_PATH"]],
        "recurse": True
    },
    format="json",
    format_options={
        "multiline": False
    },
    transformation_ctx="raw_dynamic_frame"
)

# ── Convert ─────────────────────────────────────────────────────────────────
df = raw_dynamic_frame.toDF()

# ── Transform ────────────────────────────────────────────────────────────────
df_clean = run_pipeline(df, logger=logger.info)

# ── Write ────────────────────────────────────────────────────────────────────
(df_clean.write
    .mode("append")
    .partitionBy("order_date", "category")
    .parquet(args["CURATED_PATH"]))

# ── Commit ───────────────────────────────────────────────────────────────────
job.commit()
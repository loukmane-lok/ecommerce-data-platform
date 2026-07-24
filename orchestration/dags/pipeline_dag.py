from datetime import datetime, timedelta
import os
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator

from glue_helpers import (
    start_crawler,
    wait_for_crawler,
    start_glue_job,
    wait_for_glue_job,
    check_s3_prefix_has_data,
    log_pipeline_failure,
)

RAW_BUCKET = os.environ.get("RAW_BUCKET")
CURATED_BUCKET = os.environ.get("CURATED_BUCKET")
LAMBDA_URL = os.environ.get("LAMBDA_URL")
GLUE_CRAWLER_NAME = os.environ.get("GLUE_CRAWLER_NAME")
GLUE_ETL_JOB = os.environ.get("GLUE_ETL_JOB")
GLUE_DQ_JOB = os.environ.get("GLUE_DQ_JOB")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION")

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": log_pipeline_failure,
}

dag = DAG(
    dag_id="ecommerce_pipeline",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    dagrun_timeout=timedelta(hours=1),
    tags=["ecommerce", "production"],
)

def generate_and_ingest(**kwargs):
    import json
    import subprocess
    import sys

    script_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "ingestion", "local_generator", "generate_events.py"
        )
    )

    result = subprocess.run(
        [sys.executable, script_path, "--count", "100", "--type", "both"],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    response = requests.post(LAMBDA_URL, json=payload, timeout=60)

    print(f"Sent {len(payload.get('events', []))} events to Lambda")
    print(f"Lambda response status: {response.status_code}")
    response.raise_for_status()


def run_crawler(**kwargs):
    start_crawler(GLUE_CRAWLER_NAME, AWS_REGION)
    status = wait_for_crawler(GLUE_CRAWLER_NAME, AWS_REGION)
    print(f"Crawler final status: {status}")

def run_etl_job(**kwargs):
    job_run_id = start_glue_job(GLUE_ETL_JOB, AWS_REGION)
    status = wait_for_glue_job(GLUE_ETL_JOB, job_run_id, AWS_REGION)
    print(f"ETL job run_id: {job_run_id}, final status: {status}")
    
def run_dq_job(**kwargs):
    job_run_id = start_glue_job(GLUE_DQ_JOB, AWS_REGION)
    status = wait_for_glue_job(GLUE_DQ_JOB, job_run_id, AWS_REGION)
    print(f"DQ job run_id: {job_run_id}, final status: {status}")
    
def verify_output(**kwargs):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    prefix = f"orders/order_date={today}/"

    has_data = check_s3_prefix_has_data(CURATED_BUCKET, prefix, AWS_REGION)

    if not has_data:
        raise ValueError(
            "No curated data found for today — pipeline may have written to wrong path"
        )
    print(f"Verified curated data exists at s3://{CURATED_BUCKET}/{prefix}")
    
def log_success(**kwargs):
    execution_date = str(kwargs.get("execution_date"))
    summary = {
        "status": "SUCCESS",
        "dag_id": "ecommerce_pipeline",
        "execution_date": execution_date,
        "message": "Full pipeline completed",
    }
    print(summary)
    
generate_and_ingest_task = PythonOperator(
    task_id="generate_and_ingest",
    python_callable=generate_and_ingest,
    dag=dag,
)

run_crawler_task = PythonOperator(
    task_id="run_glue_crawler",
    python_callable=run_crawler,
    dag=dag,
)

run_etl_task = PythonOperator(
    task_id="run_glue_etl",
    python_callable=run_etl_job,
    dag=dag,
)

run_dq_task = PythonOperator(
    task_id="run_data_quality",
    python_callable=run_dq_job,
    dag=dag,
)

verify_task = PythonOperator(
    task_id="verify_curated_output",
    python_callable=verify_output,
    dag=dag,
)

success_task = PythonOperator(
    task_id="pipeline_success",
    python_callable=log_success,
    dag=dag,
)

generate_and_ingest_task >> run_crawler_task >> run_etl_task >> run_dq_task >> verify_task >> success_task
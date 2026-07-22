import os 
import time
import json
from datetime import datetime
import boto3

def get_boto3_client(service, region):
    return boto3.client(
        service, 
        region_name=region,
         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), 
         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )


def start_crawler(crawler_name, region):
    client = get_boto3_client("glue", region)
    try:
        client.start_crawler(Name=crawler_name)
        print(f"Successfully started crawler: {crawler_name}")
    except client.exceptions.CrawlerRunningException:   
        print(f"Warning:crawler {crawler_name} is already running.")


def wait_for_crawler(crawler_name, region, poll_interval_seconds=15):
    client = get_boto3_client("glue", region)

    while True:
        response = client.get_crawler(Name=crawler_name)
        state = response['Crawler']['State']
        if state != 'RUNNING':
            break
        print(f"Crawler status: RUNNING ... WAITING for {poll_interval_seconds} seconds")
        time.sleep(poll_interval_seconds)
        
    last_status = response['Crawler']['LastCrawl']['Status']
    if last_status == 'FAILED':
        raise RuntimeError(f"Crawler {crawler_name} failed to complete successfully.")
    return last_status

def start_glue_job(job_name, region, arguments={}):
    client = get_boto3_client("glue", region)
    response = client.start_job_run(JobName=job_name, Arguments=arguments)
    job_run_id = response['JobRunId']
    print(f"Started Glue job: {job_name} with JobRunId: {job_run_id}")
    return job_run_id


def wait_for_glue_job(job_name, job_run_id, region, poll_interval_seconds=20):
    client = get_boto3_client("glue", region)
    terminal_states = {"SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT", "ERROR"}
    
    while True:
        response = client.get_job_run(JobName=job_name, RunId=job_run_id)
        state = response['JobRun']['JobRunState']
        if state in terminal_states:
            break
        print(f"Glue job status: {state} ... WAITING for {poll_interval_seconds} seconds")
        time.sleep(poll_interval_seconds)
    
    if state != "SUCCEEDED":
        raise RuntimeError(f"Glue job {job_name} with JobRunId {job_run_id} failed with state: {state}")
    
    return state

def check_s3_prefix_has_data(bucket_name, prefix, region):
    client = get_boto3_client("s3", region)
    response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)

    return response.get('KeyCount', 0) > 0

def log_pipeline_failure(context):
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    execution_date = str(context["execution_date"])
    error_message = str(context.get("exception", "Unknown error"))
    
    record = {
        "dag_id": dag_id,
        "task_id": task_id,
        "execution_date": execution_date,
        "error_message": error_message,
    }
    
    os.makedirs("orchestration/logs", exist_ok=True)
    with open("orchestration/logs/pipeline_failures.log", "a") as f:
        f.write(json.dumps(record) + "\n")
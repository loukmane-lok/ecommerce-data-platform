import pytest
from datetime import datetime, timezone
from moto import mock_aws
import boto3
import json
import os

from handler import build_s3_key, write_to_s3, lambda_handler

def test_build_s3_key_format():
    now = datetime(2024, 6, 27, 14, 30, 0, tzinfo=timezone.utc)
    key = build_s3_key("orders", now)
    assert key.startswith("orders/year=2024/month=06/day=27/hour=14/")
    assert key.endswith(".jsonl")
    assert "batch_" in key
    
@mock_aws
def test_write_to_s3_creates_file():
    # Create the fake bucket first — moto starts blank every time
    boto3.client("s3", region_name="us-east-1").create_bucket(
        Bucket="test-bucket"
    )

    now = datetime(2024, 6, 27, 14, 30, 0, tzinfo=timezone.utc)
    key = build_s3_key("orders", now)
    events = [{"order_id": "abc", "price": 9.99}]

    count = write_to_s3("test-bucket", key, events)

    # Assert the object exists in the fake bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    response = s3.get_object(Bucket="test-bucket", Key=key)
    assert count == 1
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    
@mock_aws
def test_lambda_handler_returns_200():
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
    os.environ["RAW_BUCKET_NAME"] = "test-bucket"

    payload = {
        "event_type": "orders",
        "events": [{"order_id": "abc", "price": 9.99}]
    }
    event = {"body": json.dumps(payload)}

    response = lambda_handler(event, context=None)
    assert response["statusCode"] == 200
    assert response["body"]["written"] == 1
    
@mock_aws
def test_lambda_handler_writes_jsonl():
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
    os.environ["RAW_BUCKET_NAME"] = "test-bucket"

    events = [
        {"order_id": "abc", "price": 9.99},
        {"order_id": "def", "price": 4.50}
    ]
    payload = {"event_type": "orders", "events": events}
    event = {"body": json.dumps(payload)}

    response = lambda_handler(event, context=None)
    s3_path = response["body"]["path"]
    key = s3_path.replace("s3://test-bucket/", "")

    s3 = boto3.client("s3", region_name="us-east-1")
    body = s3.get_object(Bucket="test-bucket", Key=key)["Body"].read().decode("utf-8")

    lines = body.strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)   # raises if any line is not valid JSON
        assert "order_id" in parsed
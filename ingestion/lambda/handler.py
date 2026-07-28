import json
import os
import boto3
from datetime import datetime, timezone


def build_s3_key(event_type: str, now: datetime) -> str:
    return (
        f"{event_type}/"
        f"year={now.strftime('%Y')}/"
        f"month={now.strftime('%m')}/"
        f"day={now.strftime('%d')}/"
        f"hour={now.strftime('%H')}/"
        f"batch_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"
    )


def write_to_s3(bucket: str, key: str, events: list[dict]) -> int:
    body = "\n".join(json.dumps(event) for event in events)

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/x-ndjson"
    )
    return len(events)


def lambda_handler(event, context):
    if isinstance(event.get("body"), str):
        payload = json.loads(event["body"])
    else:
        payload = event

    # EventBridge sends a ping with no event_type — handle gracefully
    if "event_type" not in payload:
        print("Received EventBridge ping with no payload — skipping")
        return {"statusCode": 200, "body": {"written": 0, "path": "none"}}

    event_type = payload["event_type"]
    events = payload["events"]

    bucket = os.environ["RAW_BUCKET_NAME"]
    now = datetime.now(timezone.utc)
    key = build_s3_key(event_type, now)

    written = write_to_s3(bucket, key, events)

    s3_path = f"s3://{bucket}/{key}"
    print(f"Written {written} events to {s3_path}")

    return {
        "statusCode": 200,
        "body": {
            "written": written,
            "path": s3_path
        }
    }

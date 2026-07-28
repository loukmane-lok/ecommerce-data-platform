import subprocess
import sys


def main():
    # Read JSON from stdin (piped from generate_events.py)
    payload = sys.stdin.read()

    result = subprocess.run([
        "aws", "lambda", "invoke",
        "--function-name", "ecommerce-event-ingestion",
        "--region", "us-east-1",
        "--cli-binary-format", "raw-in-base64-out",
        "--payload", payload,
        "/dev/stdout"
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()

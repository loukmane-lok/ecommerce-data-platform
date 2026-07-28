from __future__ import annotations

import uuid
import random
import sys
import argparse
import json
from datetime import datetime, timezone
from dataclasses import asdict
from schemas import OrderEvent, ClickEvent


def make_order() -> dict:
    return asdict(OrderEvent(
        order_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        product_id=f"PROD-{random.randint(1, 200):04d}",
        category=random.choice(["electronics", "clothing", "food", "home"]),
        price=round(random.uniform(0.01, 999.99), 2),
        quantity=random.randint(1, 10),
        timestamp=datetime.now(timezone.utc).isoformat(),
        status=random.choice(["pending", "confirmed", "shipped", "cancelled"]),
        country=random.choice(["FR", "DE", "GB", "ES", "IT"])
    ))


def make_click() -> dict:
    page_type = random.choice(["home", "product", "cart", "checkout", "confirm"])
    return asdict(ClickEvent(
        session_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        page_type=page_type,
        product_id=f"PROD-{random.randint(1, 200):04d}" if page_type == "product" else None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        device=random.choice(["mobile", "desktop", "tablet"]),
        country=random.choice(["FR", "DE", "GB", "ES", "IT"]),
        referrer=random.choice(["google", "direct", "email", "social", None])
    ))


def inject_noise(events: list[dict], event_type: str) -> list[dict]:
    noisy = []
    duplicates = []

    for event in events:
        if event_type == "orders":
            if random.random() < 0.05:
                event["timestamp"] = None
            if random.random() < 0.02:
                event["price"] = round(random.uniform(-999.99, -0.01), 2)
            if random.random() < 0.02:
                event["order_id"] = None
            if random.random() < 0.03:
                duplicates.append(event.copy())
        elif event_type == "clicks":
            if random.random() < 0.05:
                event["user_id"] = None
        noisy.append(event)

    noisy.extend(duplicates)
    return noisy, len(duplicates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--type", dest="event_type",
                        choices=["orders", "clicks", "both"], default="both")
    args = parser.parse_args()

    output = {}

    if args.event_type in ("orders", "both"):
        orders = [make_order() for _ in range(args.count)]
        orders, dupes = inject_noise(orders, "orders")
        nulls = sum(1 for e in orders if e["timestamp"] is None)
        print(f"Generated {len(orders)} orders, {dupes} duplicates, {nulls} null timestamps",
              file=sys.stderr)
        output["event_type"] = "orders"
        output["events"] = orders

    if args.event_type in ("clicks", "both"):
        clicks = [make_click() for _ in range(args.count)]
        clicks, _ = inject_noise(clicks, "clicks")
        print(f"Generated {len(clicks)} clicks", file=sys.stderr)
        output["event_type"] = "clicks"
        output["events"] = clicks

    print(json.dumps(output))


if __name__ == "__main__":
    main()

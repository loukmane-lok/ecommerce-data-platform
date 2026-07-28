from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderEvent:
    order_id: Optional[str]       # UUID string — Optional because we'll inject nulls as noise
    user_id: str                  # UUID string — always present
    product_id: str               # e.g. "PROD-0042"
    category: str                 # electronics | clothing | food | home
    price: float                  # 0.01–999.99 (we'll also inject negatives as noise)
    quantity: int                 # 1–10
    timestamp: Optional[str]      # ISO 8601 UTC — Optional because we'll inject nulls
    status: str                   # pending | confirmed | shipped | cancelled
    country: str                  # FR | DE | GB | ES | IT


@dataclass
class ClickEvent:
    session_id: str                # UUID — always present, tracks a browser session
    user_id: Optional[str]         # UUID — None for anonymous visitors (realistic, not an error)
    page_type: str                 # home | product | cart | checkout | confirm
    product_id: Optional[str]      # only meaningful on product pages, None elsewhere
    timestamp: str                 # ISO 8601 UTC — always present for clicks
    device: str                    # mobile | desktop | tablet
    country: str                   # FR | DE | GB | ES | IT
    referrer: Optional[str]        # google | direct | email | social | None

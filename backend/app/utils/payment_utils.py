# app/utils/payment_utils.py
from datetime import datetime
import random, string, re
from typing import Optional

def gen_order_code(booking_id: int) -> str:
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TB{booking_id}-{datetime.now():%Y%m%d}-{rand}"

_ORDER_RE = re.compile(r"(TB\d+-\d{8}-[A-Z0-9]{4})", re.IGNORECASE)

def extract_order_code(text: str | None) -> Optional[str]:
    if not text:
        return None
    m = _ORDER_RE.search(text)
    return m.group(1).upper() if m else None

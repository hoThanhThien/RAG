# app/utils/sepay.py
import hmac, hashlib, os, time, random, string, re
from typing import Optional

SEPAY_WEBHOOK_SECRET = os.getenv("SEPAY_WEBHOOK_SECRET", "change_me")

def verify_signature(raw_body: bytes, signature: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(SEPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return digest.lower() == signature.lower()

def gen_order_code(prefix: str = "ORDER") -> str:
    ts = time.strftime("%Y%m%d")
    tail = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{ts}-{tail}"

_ORDER_RE = re.compile(r"(\bORDER[_\-]?\d{6,}\b|\bODR\d{6,}\b)", re.I)

def extract_order_code(text: str) -> Optional[str]:
    if not text:
        return None
    m = _ORDER_RE.search(text)
    return m.group(1).upper() if m else None

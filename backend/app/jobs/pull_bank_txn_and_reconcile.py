import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta, timezone

from app.database import get_db_connection

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

CASSO_BASE_URL = os.getenv("CASSO_BASE_URL", "https://oauth.casso.vn/v2")
CASSO_API_KEY = os.getenv("CASSO_API_KEY")
CASSO_ACCESS_TOKEN = os.getenv("CASSO_ACCESS_TOKEN")

CASSO_LOOKBACK_DAYS = int(os.getenv("CASSO_LOOKBACK_DAYS", "2"))
CASSO_PAGE_SIZE = int(os.getenv("CASSO_PAGE_SIZE", "50"))
PAY_RECONCILE_INTERVAL = int(os.getenv("PAY_RECONCILE_INTERVAL", "60"))
VERBOSE = os.getenv("RECONCILE_VERBOSE", "0") == "1"


def _norm(s: str) -> str:
    import re
    return re.sub(r"\s+", "", (s or "")).upper()

def _contains(desc: str, order_code: str) -> bool:
    return bool(order_code) and _norm(order_code) in _norm(desc)

def _same_amount(a, b) -> bool:
    try:
        return round(float(a)) == round(float(b))
    except Exception:
        return False

def _auth_header():
    if CASSO_API_KEY:
        return {"Authorization": f"Apikey {CASSO_API_KEY}"}
    if CASSO_ACCESS_TOKEN:
        return {"Authorization": f"Bearer {CASSO_ACCESS_TOKEN}"}
    return {}

def fetch_casso_since(since_date: str) -> list:
    """
    since_date: YYYY-MM-DD
    """
    headers = _auth_header()
    if not headers:
        print("[CASSO] Missing credentials: set CASSO_API_KEY or CASSO_ACCESS_TOKEN")
        return []

    url = f"{CASSO_BASE_URL.rstrip('/')}/transactions"
    page = 1
    all_tx = []
    unauthorized_logged = False

    while True:
        params = {
            "fromDate": since_date,
            "page": page,
            "pageSize": CASSO_PAGE_SIZE,
            "sort": "ASC",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 401:
                if not unauthorized_logged:
                    print("[CASSO] 401 Unauthorized. Kiểm tra CASSO_API_KEY/CASSO_ACCESS_TOKEN và BASE_URL (nên là oauth.casso.vn/v2).")
                    if VERBOSE:
                        print("[CASSO] Body:", r.text[:500])
                unauthorized_logged = True
                break
            if r.status_code != 200:
                print("[CASSO] ERROR", r.status_code)
                if VERBOSE:
                    print("[CASSO] Body:", r.text[:500])
                break

            data = r.json()
            records = []
            if isinstance(data, dict):
                if isinstance(data.get("data"), list):
                    records = data["data"]
                elif isinstance(data.get("data"), dict) and isinstance(data["data"].get("records"), list):
                    records = data["data"]["records"]
                elif isinstance(data.get("transactions"), list):
                    records = data["transactions"]

            if not records:
                break

            all_tx.extend(records)
            if len(records) < CASSO_PAGE_SIZE:
                break
            page += 1

        except requests.RequestException as e:
            print("[CASSO] Request error:", e)
            break

    return all_tx

def upsert_bank_txn(conn, provider: str, ref: str, amount: float, desc: str, paid_at: datetime, raw: dict):
    raw_json = json.dumps(raw, ensure_ascii=False) if raw else None
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO bank_txn (Provider, ProviderRef, Amount, Description, PaidAt, RawPayload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    Amount=VALUES(Amount),
                    Description=VALUES(Description),
                    PaidAt=VALUES(PaidAt)
                """,
                (provider, ref, float(amount or 0), desc or "", paid_at, raw_json),
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            if VERBOSE:
                print("[DB] upsert_bank_txn error:", e)
            return False

def reconcile_pending(conn, lookback_days: int = 7) -> dict:
    matched = 0
    checked = 0
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT PaymentID, BookingID, OrderCode, Amount
            FROM payment
            WHERE Status='Pending'
              AND CreatedAt >= NOW() - INTERVAL %s DAY
            """,
            (lookback_days,),
        )
        pending = cur.fetchall()

        for p in pending:
            checked += 1
            order_code = p["OrderCode"]
            amt = p["Amount"]

            cur.execute(
                """
                SELECT Provider, ProviderRef, Amount, Description, PaidAt
                FROM bank_txn
                WHERE PaidAt >= NOW() - INTERVAL %s DAY
                  AND ROUND(Amount,0)=ROUND(%s,0)
                  AND UPPER(REPLACE(Description, ' ', '')) LIKE CONCAT('%', UPPER(REPLACE(%s, ' ', '')), '%')
                ORDER BY PaidAt DESC
                LIMIT 1
                """,
                (lookback_days, amt, order_code),
            )
            hit = cur.fetchone()
            if hit:
                try:
                    cur.execute(
                        "UPDATE payment SET Status='Paid', ProviderTxnID=%s, PaidAt=%s WHERE PaymentID=%s",
                        (hit["ProviderRef"], hit["PaidAt"], p["PaymentID"]),
                    )
                    cur.execute(
                        "UPDATE booking SET Status='Confirmed' WHERE BookingID=%s",
                        (p["BookingID"],),
                    )
                    conn.commit()
                    matched += 1
                except Exception as e:
                    conn.rollback()
                    if VERBOSE:
                        print("[DB] reconcile update error:", e)

    return {"checked": checked, "matched": matched}

def run_once():
    # thời điểm kéo theo UTC (Casso dùng ngày, không tính timezone phức tạp)
    since_date = (datetime.now(timezone.utc) - timedelta(days=CASSO_LOOKBACK_DAYS)).date().isoformat()

    fetched = 0
    inserted = 0

    # 1) kéo Casso (nếu có cred)
    if _auth_header():
        txs = fetch_casso_since(since_date)
        fetched = len(txs)
        if fetched:
            conn = get_db_connection()
            try:
                for t in txs:
                    ref = str(t.get("tid") or t.get("id") or t.get("transactionID") or t.get("transaction_id") or "")
                    amount = float(t.get("amount") or t.get("creditAmount") or t.get("Amount") or 0)
                    desc = t.get("description") or t.get("content") or t.get("Remark") or ""

                    when = t.get("when") or t.get("time") or t.get("transactionDate") or t.get("paid_at")
                    if isinstance(when, str):
                        try:
                            paid_at = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
                        except Exception:
                            paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    else:
                        paid_at = datetime.now(timezone.utc).replace(tzinfo=None)

                    if upsert_bank_txn(conn, "casso", ref, amount, desc, paid_at, t):
                        inserted += 1
            finally:
                conn.close()
    else:
        print("[CASSO] Skip fetch: no credentials in ENV")

    # 2) đối soát
    conn = get_db_connection()
    try:
        res = reconcile_pending(conn, lookback_days=max(CASSO_LOOKBACK_DAYS, 7))
    finally:
        conn.close()

    print(
        f"[{datetime.now().isoformat()}] reconcile_once => "
        f"fetched={fetched} inserted={inserted} checked={res['checked']} matched={res['matched']}"
    )
    return {"fetched": fetched, "inserted": inserted, **res}

def run_loop():
    while True:
        try:
            run_once()
        except Exception as e:
            # KHÔNG dùng % format ở đây
            print("[RECONCILE] Error:", e)
        time.sleep(PAY_RECONCILE_INTERVAL)

if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_loop()

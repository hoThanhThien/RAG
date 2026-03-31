from fastapi import APIRouter, HTTPException, Query, Body
from app.database import get_db_connection
from typing import Optional, List, Dict, Any
import datetime, decimal

router = APIRouter(prefix="/photos", tags=["Photos"])

def to_jsonable(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in row.items():
        if isinstance(v, decimal.Decimal):
            out[k] = float(v)
        elif isinstance(v, (datetime.date, datetime.datetime)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

# ---------- A) List ảnh (có thể lọc theo tour) ----------
@router.get("")
def list_photos(
    tour_id: Optional[int] = Query(None),
    page: int = 1,
    page_size: int = 50
):
    offset = (page - 1) * page_size
    sql = """
        SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
               ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
        FROM photo
    """
    params: List[Any] = []
    if tour_id is not None:
        sql += " WHERE TourID = %s"; params.append(tour_id)
    sql += " ORDER BY IsPrimary DESC, PhotoID DESC LIMIT %s OFFSET %s"
    params += [page_size, offset]

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [to_jsonable(r) for r in rows]
    finally:
        conn.close()

# ---------- B) Lấy 1 ảnh ----------
@router.get("/{photo_id}")
def get_photo(photo_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE PhotoID = %s
            """, (photo_id,))
            r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Photo not found")
        return to_jsonable(r)
    finally:
        conn.close()

# ---------- C) Ảnh của 1 tour ----------
@router.get("/tour/{tour_id}")
def list_photos_of_tour(tour_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE TourID = %s
                ORDER BY IsPrimary DESC, PhotoID DESC
            """, (tour_id,))
            rows = cur.fetchall()
        return [to_jsonable(r) for r in rows]
    finally:
        conn.close()

# ---------- D) Ảnh chính của tour ----------
@router.get("/tour/{tour_id}/primary")
def get_primary_photo(tour_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE TourID = %s AND IsPrimary = 1
                ORDER BY PhotoID DESC LIMIT 1
            """, (tour_id,))
            r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Primary photo not found")
        return to_jsonable(r)
    finally:
        conn.close()

# ---------- E) Thêm 1 ảnh cho tour ----------
@router.post("/tour/{tour_id}")
def add_photo_for_tour(
    tour_id: int,
    caption: Optional[str] = Body(None),
    image_url: str = Body(...),
    upload_date: Optional[str] = Body(None),  # "YYYY-MM-DD"
    is_primary: Optional[bool] = Body(False)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM tour WHERE TourID = %s", (tour_id,))
            if not cur.fetchone():
                raise HTTPException(400, "TourID does not exist")

            if is_primary:
                cur.execute("UPDATE photo SET IsPrimary = 0 WHERE TourID = %s", (tour_id,))

            cur.execute("""
                INSERT INTO photo (TourID, Caption, ImageURL, UploadDate, IsPrimary)
                VALUES (%s, %s, %s, %s, %s)
            """, (tour_id, caption, image_url, upload_date, 1 if is_primary else 0))
            new_id = cur.lastrowid
            conn.commit()

            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE PhotoID = %s
            """, (new_id,))
            r = cur.fetchone()
        return to_jsonable(r)
    finally:
        conn.close()

# ---------- F) Thêm nhiều ảnh cho tour (bulk) ----------
@router.post("/tour/{tour_id}/bulk")
def add_photos_bulk(tour_id: int, photos: List[Dict[str, Any]] = Body(...)):
    """
    photos = [
      {"caption":"...", "image_url":"...", "upload_date":"2025-08-23", "is_primary": false},
      ...
    ]
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM tour WHERE TourID = %s", (tour_id,))
            if not cur.fetchone():
                raise HTTPException(400, "TourID does not exist")

            if any(p.get("is_primary") for p in photos):
                cur.execute("UPDATE photo SET IsPrimary = 0 WHERE TourID = %s", (tour_id,))

            args = []
            for p in photos:
                if "image_url" not in p:
                    raise HTTPException(400, "Each photo requires image_url")
                args.append((
                    tour_id,
                    p.get("caption"),
                    p["image_url"],
                    p.get("upload_date"),
                    1 if p.get("is_primary") else 0
                ))
            cur.executemany("""
                INSERT INTO photo (TourID, Caption, ImageURL, UploadDate, IsPrimary)
                VALUES (%s, %s, %s, %s, %s)
            """, args)
            conn.commit()

            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE TourID = %s
                ORDER BY IsPrimary DESC, PhotoID DESC
            """, (tour_id,))
            rows = cur.fetchall()
        return [to_jsonable(r) for r in rows]
    finally:
        conn.close()

# ---------- G) Cập nhật 1 ảnh ----------
@router.patch("/{photo_id}")
def update_photo(
    photo_id: int,
    caption: Optional[str] = Body(None),
    image_url: Optional[str] = Body(None),
    upload_date: Optional[str] = Body(None),
    is_primary: Optional[bool] = Body(None)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT TourID FROM photo WHERE PhotoID = %s", (photo_id,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Photo not found")
            tour_id = r["TourID"]

            if is_primary is True:
                cur.execute("UPDATE photo SET IsPrimary = 0 WHERE TourID = %s", (tour_id,))

            sets, params = [], []
            if caption is not None:     sets.append("Caption = %s");     params.append(caption)
            if image_url is not None:   sets.append("ImageURL = %s");    params.append(image_url)
            if upload_date is not None: sets.append("UploadDate = %s");  params.append(upload_date)
            if is_primary is not None:  sets.append("IsPrimary = %s");   params.append(1 if is_primary else 0)

            if sets:
                params.append(photo_id)
                cur.execute(f"UPDATE photo SET {', '.join(sets)} WHERE PhotoID = %s", params)
                conn.commit()

            cur.execute("""
                SELECT PhotoID AS photo_id, TourID AS tour_id, Caption AS caption,
                       ImageURL AS image_url, UploadDate AS upload_date, IsPrimary AS is_primary
                FROM photo WHERE PhotoID = %s
            """, (photo_id,))
            row = cur.fetchone()
        return to_jsonable(row)
    finally:
        conn.close()

# ---------- H) Xoá 1 ảnh ----------
@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM photo WHERE PhotoID = %s", (photo_id,))
            conn.commit()
        return None
    finally:
        conn.close()

from fastapi import APIRouter, HTTPException
from app.database import get_db_connection
from app.schemas.discount_schema import DiscountSchema, DiscountResponse
from typing import List
import pymysql.cursors  # ✅ để dùng DictCursor

router = APIRouter(prefix="/discounts", tags=["Discounts"])

@router.get("", response_model=List[DiscountResponse])
def get_discounts():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)  # ✅ sửa ở đây
        cursor.execute("""
    SELECT
        DiscountID AS discount_id,
        Code AS code,
        Description AS description,
        DiscountAmount AS discount_amount,
        IsPercent AS is_percent,
        StartDate AS start_date,
        EndDate AS end_date
    FROM discount
""")

        result = cursor.fetchall()
        return result
    finally:
        conn.close()

@router.post("")
def create_discount(payload: DiscountSchema):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO discount (Code, Description, DiscountAmount, IsPercent, StartDate, EndDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payload.code,
                payload.description,
                payload.discount_amount,
                payload.is_percent,
                payload.start_date,
                payload.end_date
            )
        )
        conn.commit()
        return {"message": "Thêm mã giảm giá thành công"}
    finally:
        conn.close()

@router.put("/{discount_id}")
def update_discount(discount_id: int, payload: DiscountSchema):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DiscountID FROM discount WHERE DiscountID = %s", (discount_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Không tìm thấy mã giảm giá")

        cursor.execute(
            """
            UPDATE discount
            SET Code=%s, Description=%s, DiscountAmount=%s, IsPercent=%s, StartDate=%s, EndDate=%s
            WHERE DiscountID=%s
            """,
            (
                payload.code,
                payload.description,
                payload.discount_amount,
                payload.is_percent,
                payload.start_date,
                payload.end_date,
                discount_id
            )
        )
        conn.commit()
        return {"message": "Cập nhật thành công"}
    finally:
        conn.close()

@router.delete("/{discount_id}")
def delete_discount(discount_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM discount WHERE DiscountID = %s", (discount_id,))
        conn.commit()
        return {"message": "Xoá thành công"}
    finally:
        conn.close()

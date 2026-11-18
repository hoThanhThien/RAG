from fastapi import APIRouter

from app.database import get_db_connection

router = APIRouter(tags=["Roles"])


@router.get(
    "/roles",
    summary="Lấy danh sách vai trò (Roles)",
    description="Trả về danh sách các vai trò phân quyền hiện có trong hệ thống (Admin, Guide, User).",
)
def get_roles():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT RoleID AS role_id, RoleName AS role_name FROM role ORDER BY RoleID ASC")
            rows = cur.fetchall()
            if rows:
                return list(rows)
    except Exception:
        pass
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return [
        {"role_id": 1, "role_name": "admin"},
        {"role_id": 2, "role_name": "guide"},
        {"role_id": 3, "role_name": "user"},
    ]

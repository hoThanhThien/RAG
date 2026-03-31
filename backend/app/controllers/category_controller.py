from fastapi import APIRouter, Depends
from app.database import get_db_connection
from app.utils.pagination import PaginationParams, paginate_mysql, parse_sort
from fastapi import HTTPException
from app.schemas.category_schema import CategoryCreateSchema


router = APIRouter(prefix="/categories", tags=["Categories"])




@router.get("")
def list_categories(paging: PaginationParams = Depends()):
    conn = get_db_connection()
    try:
        count_sql = "SELECT COUNT(*) AS cnt FROM category"
        data_sql_base = "SELECT CategoryID AS category_id, CategoryName AS name, Description AS description FROM category"
        allowed = {"name": "CategoryName", "category_id": "CategoryID"}
        order_by_sql = parse_sort(paging.sort, allowed, "ORDER BY CategoryName")

        result = paginate_mysql(conn, count_sql, data_sql_base, (), paging.page, paging.page_size, order_by_sql)
        return result
    finally:
        conn.close()

@router.post("")
def create_category(payload: CategoryCreateSchema):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO category (CategoryName, Description) VALUES (%s, %s)",
                (payload.name, payload.description)
            )
            conn.commit()
        return {"message": "Category created successfully"}
    finally:
        conn.close()

@router.put("/{category_id}")
def update_category(category_id: int, payload: CategoryCreateSchema):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT CategoryID FROM category WHERE CategoryID = %s", (category_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")

            cur.execute(
                "UPDATE category SET CategoryName = %s, Description = %s WHERE CategoryID = %s",
                (payload.name, payload.description, category_id)
            )
            conn.commit()
        return {"message": "Category updated successfully"}
    finally:
        conn.close()

@router.delete("/{category_id}")
def delete_category(category_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Kiểm tra ràng buộc trước khi xoá
            cursor.execute("SELECT COUNT(*) as count FROM tour WHERE CategoryID = %s", (category_id,))
            result = cursor.fetchone()
            if result["count"] > 0:
                raise HTTPException(status_code=400, detail="Không thể xoá danh mục vì còn tour liên quan.")

            # Nếu không có tour liên quan, tiến hành xoá
            cursor.execute("DELETE FROM category WHERE CategoryID = %s", (category_id,))
            conn.commit()
            return {"message": "Xoá danh mục thành công"}
    finally:
        conn.close()





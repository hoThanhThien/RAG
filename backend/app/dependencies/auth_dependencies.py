from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth import verify_token
from app.database import get_db_connection
from typing import Dict, Any, Optional
from pymysql.cursors import DictCursor
import pymysql
from fastapi import WebSocket, WebSocketException
from jose import jwt, JWTError
from app.utils.auth import SECRET_KEY, ALGORITHM  # ✅ Sử dụng từ file auth.py bạn đang có


security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Lấy thông tin user hiện tại từ HttpOnly Cookie hoặc Authorization Bearer header"""
    token = None
    if request and "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    elif credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_token(token)
    
    # Lấy thông tin user từ database
    connection = get_db_connection()
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)  # ✅ Đúng
    
    try:
        cursor.execute("""
            SELECT u.*, r.RoleName 
            FROM user u 
            JOIN role r ON u.RoleID = r.RoleID 
            WHERE u.UserID = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    finally:
        cursor.close()
        connection.close()

def require_role(required_role: str):
    """Decorator để yêu cầu quyền cụ thể"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user.get("RoleName") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {required_role}"
            )
        return current_user
    return role_checker

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    role = current_user.get("RoleName", "").lower()
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_guide(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Yêu cầu quyền hướng dẫn viên"""
    if current_user.get("RoleName") not in ["admin", "guide"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guide access required"
        )
    return current_user

def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Lấy user hiện tại, không bắt buộc đăng nhập (hỗ trợ cookie & header)"""
    try:
        return get_current_user(request, credentials)
    except HTTPException:
        return None


async def get_current_user_ws(websocket: WebSocket):
    # Ưu tiên lấy từ cookie WebSocket handshake, sau đó fallback query param ?token=
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    if not token:
        raise WebSocketException(code=4401, reason="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))

        connection = get_db_connection()
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)

        try:
            cursor.execute("""
                SELECT u.*, r.RoleName 
                FROM user u 
                JOIN role r ON u.RoleID = r.RoleID 
                WHERE u.UserID = %s
            """, (user_id,))
            user = cursor.fetchone()
            if not user:
                raise WebSocketException(code=4401, reason="User not found")
            return user
        finally:
            cursor.close()
            connection.close()

    except JWTError:
        raise WebSocketException(code=4401, reason="Invalid token")
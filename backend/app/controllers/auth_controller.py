import os
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer

from app.database import get_db_connection
from app.dependencies.auth_dependencies import get_current_user, get_current_user_optional
from app.schemas.auth_schema import (
    ChangePassword,
    GoogleAuthRequest,
    LoginResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    encode_account_id,
    get_password_hash,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


def _is_secure_request(request: Request) -> bool:
    env_val = os.getenv("COOKIE_SECURE", "").strip().lower()
    if env_val in ("1", "true", "yes"):
        return True
    if env_val in ("0", "false", "no"):
        return False
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    return request.url.scheme == "https" or forwarded_proto == "https"


def _set_auth_cookies(
    response: Response,
    request: Request,
    access_token: str,
    refresh_token: str,
    access_max_age: int,
    refresh_max_age: int,
) -> None:
    is_secure = _is_secure_request(request)
    samesite_mode = "none" if is_secure else "lax"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=access_max_age,
        expires=access_max_age,
        samesite=samesite_mode,
        secure=is_secure,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=refresh_max_age,
        expires=refresh_max_age,
        samesite=samesite_mode,
        secure=is_secure,
        path="/",
    )


def _clear_auth_cookies(response: Response, request: Request) -> None:
    is_secure = _is_secure_request(request)
    samesite_mode = "none" if is_secure else "lax"
    for cookie_name in ("access_token", "refresh_token"):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            samesite=samesite_mode,
            secure=is_secure,
            httponly=True,
        )


def _build_account_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    email = user.get("Email") or ""
    username = (
        user.get("Username")
        or user.get("FullName")
        or user.get("FirstName")
        or (email.split("@")[0] if "@" in email else "")
        or f"user_{user['UserID']}"
    )
    return {
        "id": encode_account_id(int(user["UserID"])),
        "username": username,
        "email": email,
        "phone": user.get("Phone") or "",
        "address": user.get("Address") or "",
        "roles": user.get("RoleName") or "User",
    }


def _issue_login_response(
    user: Dict[str, Any],
    response: Response,
    request: Request,
    message: str,
) -> Dict[str, Any]:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    account_payload = _build_account_payload(user)

    token_claims = {
        "sub": account_payload["id"],
        "uid": int(user["UserID"]),
        "username": account_payload["username"],
        "email": account_payload["email"],
        "roles": account_payload["roles"],
    }
    access_token = create_access_token(data=token_claims, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=token_claims, expires_delta=refresh_token_expires)

    _set_auth_cookies(
        response=response,
        request=request,
        access_token=access_token,
        refresh_token=refresh_token,
        access_max_age=int(access_token_expires.total_seconds()),
        refresh_max_age=int(refresh_token_expires.total_seconds()),
    )

    return {
        "data": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "account": account_payload,
        },
        "message": message,
    }


def _split_name_parts(first_name: str, last_name: str, full_name: Optional[str], email: str) -> tuple[str, str, str]:
    fn = (first_name or "").strip()
    ln = (last_name or "").strip()
    full = (full_name or "").strip()
    if full and not fn and not ln:
        parts = full.split()
        fn = parts[0]
        ln = " ".join(parts[1:]) if len(parts) > 1 else ""
    combined = full or " ".join(p for p in (fn, ln) if p).strip()
    if not combined:
        combined = email.split("@")[0] if "@" in email else "User"
    if not fn:
        fn = combined.split()[0]
    return fn[:50], ln[:50], combined[:100]


def _verify_google_identity(payload: GoogleAuthRequest) -> Dict[str, str]:
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    dev_mode = os.getenv("GOOGLE_AUTH_DEV_MODE", "true").strip().lower() in ("1", "true", "yes")

    if payload.credential:
        try:
            resp = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": payload.credential},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Không thể kết nối Google để xác thực: {exc}",
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google ID token không hợp lệ hoặc đã hết hạn",
            )
        info = resp.json()
        if google_client_id and info.get("aud") != google_client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Client ID không khớp",
            )
        if str(info.get("email_verified", "true")).lower() not in ("true", "1"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản Google chưa xác minh email",
            )
        email = (info.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không lấy được email từ tài khoản Google",
            )
        return {
            "email": email,
            "first_name": (info.get("given_name") or "").strip(),
            "last_name": (info.get("family_name") or "").strip(),
            "full_name": (info.get("name") or "").strip(),
        }

    if payload.access_token:
        try:
            resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {payload.access_token}"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Không thể kết nối Google để lấy thông tin tài khoản: {exc}",
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google access token không hợp lệ hoặc đã hết hạn",
            )
        info = resp.json()
        if info.get("email_verified") is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản Google chưa xác minh email",
            )
        email = (info.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không lấy được email từ tài khoản Google",
            )
        return {
            "email": email,
            "first_name": (info.get("given_name") or "").strip(),
            "last_name": (info.get("family_name") or "").strip(),
            "full_name": (info.get("name") or "").strip(),
        }

    if payload.email and (not google_client_id or dev_mode):
        return {
            "email": str(payload.email).strip().lower(),
            "first_name": (payload.first_name or "").strip(),
            "last_name": (payload.last_name or "").strip(),
            "full_name": (payload.full_name or "").strip(),
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Thiếu Google credential hoặc access_token hợp lệ",
    )


@router.post("/register", response_model=LoginResponse)
async def register(user_data: UserRegister, response: Response, request: Request):
    """Đăng ký tài khoản mới - Tự động đăng nhập & lưu JWT vào HttpOnly Cookie."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        normalized_email = str(user_data.email).strip().lower()
        cursor.execute("SELECT UserID FROM user WHERE Email = %s", (normalized_email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Mã hóa mật khẩu bằng bcrypt
        hashed_password = get_password_hash(user_data.password)
        first_name, last_name, full_name = _split_name_parts(
            user_data.first_name or "",
            user_data.last_name or "",
            user_data.full_name,
            normalized_email,
        )
        phone = (user_data.phone or "").strip()

        # Luôn gán role User (3) cho đăng ký công khai
        cursor.execute(
            """
            INSERT INTO user (FirstName, LastName, FullName, Password, Phone, Email, RoleID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                first_name,
                last_name,
                full_name,
                hashed_password,
                phone,
                normalized_email,
                3,
            ),
        )

        new_user_id = cursor.lastrowid
        connection.commit()

        cursor.execute(
            """
            SELECT u.*, r.RoleName
            FROM user u
            JOIN role r ON u.RoleID = r.RoleID
            WHERE u.UserID = %s
            """,
            (new_user_id,),
        )
        new_user = cursor.fetchone()
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load newly registered user",
            )

        return _issue_login_response(
            user=new_user,
            response=response,
            request=request,
            message="Đăng ký tài khoản thành công",
        )

    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        cursor.close()
        connection.close()


@router.post("/google", response_model=LoginResponse)
async def google_auth(payload: GoogleAuthRequest, response: Response, request: Request):
    """Đăng ký / Đăng nhập bằng Google - Cấp JWT lưu trong HttpOnly Cookie."""
    identity = _verify_google_identity(payload)
    email = identity["email"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT u.*, r.RoleName
            FROM user u
            JOIN role r ON u.RoleID = r.RoleID
            WHERE u.Email = %s
            """,
            (email,),
        )
        user = cursor.fetchone()

        if user:
            message = "Đăng nhập bằng Google thành công"
        else:
            first_name, last_name, full_name = _split_name_parts(
                identity.get("first_name", ""),
                identity.get("last_name", ""),
                identity.get("full_name", ""),
                email,
            )
            random_password_hash = get_password_hash(secrets.token_urlsafe(24))
            cursor.execute(
                """
                INSERT INTO user (FirstName, LastName, FullName, Password, Phone, Email, RoleID)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, full_name, random_password_hash, "", email, 3),
            )
            new_user_id = cursor.lastrowid
            connection.commit()

            cursor.execute(
                """
                SELECT u.*, r.RoleName
                FROM user u
                JOIN role r ON u.RoleID = r.RoleID
                WHERE u.UserID = %s
                """,
                (new_user_id,),
            )
            user = cursor.fetchone()
            message = "Đăng ký và đăng nhập bằng Google thành công"

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể khởi tạo tài khoản Google",
            )

        return _issue_login_response(
            user=user,
            response=response,
            request=request,
            message=message,
        )

    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        cursor.close()
        connection.close()


@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, response: Response, request: Request):
    """Đăng nhập - Mã hóa JWT (accessToken, refreshToken) và lưu trong HttpOnly Cookie."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        identifier_email = (user_credentials.email or "").strip()
        identifier_username = (user_credentials.username or "").strip()

        if identifier_email:
            cursor.execute(
                """
                SELECT u.*, r.RoleName
                FROM user u
                JOIN role r ON u.RoleID = r.RoleID
                WHERE u.Email = %s
                """,
                (identifier_email,),
            )
        else:
            cursor.execute(
                """
                SELECT u.*, r.RoleName
                FROM user u
                JOIN role r ON u.RoleID = r.RoleID
                WHERE u.Email = %s OR u.FullName = %s
                """,
                (identifier_username, identifier_username),
            )

        user = cursor.fetchone()

        if not user or not verify_password(user_credentials.password, user["Password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return _issue_login_response(
            user=user,
            response=response,
            request=request,
            message="Đăng nhập thành công",
        )

    finally:
        cursor.close()
        connection.close()


@router.post("/refresh", response_model=LoginResponse)
async def refresh_session(request: Request, response: Response):
    """Làm mới cặp accessToken & refreshToken từ refresh_token trong HttpOnly Cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_token(refresh_token, expected_type="refresh")
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT u.*, r.RoleName
            FROM user u
            JOIN role r ON u.RoleID = r.RoleID
            WHERE u.UserID = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return _issue_login_response(
            user=user,
            response=response,
            request=request,
            message="Làm mới phiên đăng nhập thành công",
        )
    finally:
        cursor.close()
        connection.close()


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    """Đăng xuất - Xóa hoàn toàn HttpOnly Cookies (access_token & refresh_token)."""
    _ = current_user
    _clear_auth_cookies(response, request)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lấy thông tin user hiện tại từ HttpOnly Cookie session."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) as booking_count
                FROM booking
                WHERE UserID = %s
                """,
                (current_user["UserID"],),
            )
            result = cursor.fetchone()
            booking_count = result["booking_count"] if result else 0
    finally:
        connection.close()

    account_payload = _build_account_payload(current_user)
    return UserResponse(
        id=account_payload["id"],
        user_id=current_user["UserID"],
        username=account_payload["username"],
        first_name=current_user.get("FirstName") or "",
        last_name=current_user.get("LastName") or "",
        full_name=current_user.get("FullName") or "",
        email=current_user.get("Email") or "",
        phone=current_user.get("Phone") or "",
        address=account_payload["address"],
        role_name=current_user.get("RoleName") or "User",
        roles=account_payload["roles"],
        role_id=current_user.get("RoleID") or 3,
        booking_count=booking_count,
        created_at=current_user.get("CreatedAt"),
    )


@router.put("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Đổi mật khẩu"""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if not verify_password(password_data.old_password, current_user["Password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password",
            )

        new_hashed_password = get_password_hash(password_data.new_password)

        cursor.execute(
            """
            UPDATE user SET Password = %s WHERE UserID = %s
            """,
            (new_hashed_password, current_user["UserID"]),
        )

        connection.commit()
        return {"message": "Password changed successfully"}

    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        cursor.close()
        connection.close()

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.schemas.auth_schema import UserLogin, UserRegister, Token, UserResponse, ChangePassword
from app.utils.auth import verify_password, get_password_hash, create_access_token
from app.dependencies.auth_dependencies import get_current_user
from app.database import get_db_connection
from datetime import timedelta
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    """Đăng ký tài khoản mới"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Kiểm tra email đã tồn tại
        cursor.execute("SELECT UserID FROM user WHERE Email = %s", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Mã hóa mật khẩu
        hashed_password = get_password_hash(user_data.password)
        full_name = f"{user_data.first_name} {user_data.last_name}"
        
        # Thêm user mới
        cursor.execute("""
            INSERT INTO user (FirstName, LastName, FullName, Password, Phone, Email, RoleID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_data.first_name,
            user_data.last_name, 
            full_name,
            hashed_password,
            user_data.phone,
            user_data.email,
            user_data.role_id
        ))
        
        connection.commit()
        return {"message": "User registered successfully"}
        
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Đăng nhập"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Tìm user theo email
        cursor.execute("""
            SELECT u.*, r.RoleName 
            FROM user u 
            JOIN role r ON u.RoleID = r.RoleID 
            WHERE u.Email = %s
        """, (user_credentials.email,))
        
        user = cursor.fetchone()
        
        if not user or not verify_password(user_credentials.password, user["Password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Tạo access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user["UserID"]), "full_name": user["FullName"] },
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    finally:
        cursor.close()
        connection.close()

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Đăng xuất"""
    # Trong implementation thực tế, bạn có thể thêm token vào blacklist
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lấy thông tin user hiện tại"""
    # Đếm số booking của user
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as booking_count 
                FROM booking 
                WHERE UserID = %s
            """, (current_user["UserID"],))
            result = cursor.fetchone()
            booking_count = result["booking_count"] if result else 0
    finally:
        connection.close()
    
    return UserResponse(
        user_id=current_user["UserID"],
        first_name=current_user["FirstName"],
        last_name=current_user["LastName"], 
        full_name=current_user["FullName"],
        email=current_user["Email"],
        phone=current_user["Phone"],
        role_name=current_user["RoleName"],
        role_id=current_user["RoleID"],
        booking_count=booking_count,
        created_at=current_user.get("CreatedAt")
    )

@router.put("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Đổi mật khẩu"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Verify old password
        if not verify_password(password_data.old_password, current_user["Password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update password
        cursor.execute("""
            UPDATE user SET Password = %s WHERE UserID = %s
        """, (new_hashed_password, current_user["UserID"]))
        
        connection.commit()
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        cursor.close()
        connection.close()

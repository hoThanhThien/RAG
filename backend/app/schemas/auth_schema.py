from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self):
        if not ((self.email and self.email.strip()) or (self.username and self.username.strip())):
            raise ValueError("Email or username is required")
        return self


class UserRegister(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    full_name: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = ""
    role_id: Optional[int] = 3  # Default to user role


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AccountSchema(BaseModel):
    id: str = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    username: str = Field(..., examples=["string"])
    email: str = Field(..., examples=["string"])
    phone: str = Field(default="", examples=["string"])
    address: str = Field(default="", examples=["string"])
    roles: str = Field(..., examples=["Admin"])


class LoginDataSchema(BaseModel):
    accessToken: str = Field(..., examples=["string"])
    refreshToken: str = Field(..., examples=["string"])
    account: AccountSchema


class LoginResponse(BaseModel):
    data: LoginDataSchema
    message: str = Field(default="Đăng nhập thành công", examples=["string"])


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserResponse(BaseModel):
    id: Optional[str] = None
    user_id: int
    username: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str
    address: Optional[str] = ""
    role_name: str
    roles: Optional[str] = None
    role_id: int
    booking_count: Optional[int] = 0
    created_at: Optional[datetime] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str

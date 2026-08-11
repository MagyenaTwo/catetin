from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    otp: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class PhoneUpdateSchema(BaseModel):
    phone_number: str = Field(..., min_length=8, max_length=15, description="Nomor WhatsApp user")


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True
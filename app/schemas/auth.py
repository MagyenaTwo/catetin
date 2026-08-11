from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    otp: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True
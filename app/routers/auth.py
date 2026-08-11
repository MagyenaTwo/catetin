import traceback
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response, responses, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin
from app.services.auth_service import create_user, authenticate_user, create_and_send_otp
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

limiter = Limiter(key_func=get_remote_address)

SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak. Silakan login terlebih dahulu."
        )

    try:
        scheme, token = token_cookie.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Skema token tidak valid."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format token cookie tidak valid."
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid."
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token kadaluwarsa atau tidak valid."
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan."
        )

    return user

class OTPRequest(BaseModel):
    email: EmailStr

@router.post("/send-otp")
@limiter.limit("3/minute")
def send_otp(request: Request, payload: OTPRequest, db: Session = Depends(get_db)):
    try:
        create_and_send_otp(db, payload.email)
        return {"message": "Kode OTP berhasil dikirim."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal mengirim kode OTP. Silakan coba lagi nanti."
        )

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@router.post("/register")
@limiter.limit("5/hour")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db, user_in)
        return {"message": "Pendaftaran berhasil", "user_id": new_user.id}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan sistem saat pendaftaran."
        )

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah."
        )
    
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=86400
    )
    
    return {"message": "Login berhasil", "redirect_url": "/dashboard"}

@router.get("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token_cookie = request.cookies.get("access_token")
    
    if token_cookie:
        try:
            # Ambil raw token tanpa awalan 'Bearer '
            _, token = token_cookie.split(" ")
            
            # Simpan ke tabel blacklist jika belum ada
            existing = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
            if not existing:
                blacklisted = BlacklistedToken(token=token)
                db.add(blacklisted)
                db.commit()
        except ValueError:
            pass

    res = responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return res

@router.get("/dashboard")
def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": current_user}
    )
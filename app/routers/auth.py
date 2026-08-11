import traceback

from fastapi import APIRouter, Depends, Request, Form, Response, responses, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin
from app.services.auth_service import create_user, authenticate_user, create_and_send_otp
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

class OTPRequest(BaseModel):
    email: EmailStr
@router.post("/send-otp")
def send_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    try:
        print(f"[OTP REQUEST] Mengirim OTP ke email: {payload.email}")
        create_and_send_otp(db, payload.email)
        return {"message": "Kode OTP berhasil dikirim."}
    except ValueError as e:
        print(f"[OTP ERROR 400] {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("=== [OTP ERROR 500 TRACEBACK START] ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        traceback.print_exc()
        print("=== [OTP ERROR 500 TRACEBACK END] ===")
        raise HTTPException(status_code=500, detail=f"Gagal mengirim OTP: {str(e)}")

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@router.post("/register")
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        new_user = create_user(db, user_in)
        return {"message": "Pendaftaran berhasil", "user_id": new_user.id}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print("="*50)
        print("ERROR REGISTER 500:")
        traceback.print_exc()
        print("="*50)
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@router.post("/login")
def login(
    data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah."
        )
    
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return {"message": "Login berhasil", "redirect_url": "/dashboard"}

@router.get("/logout")
def logout():
    response = responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user_id")
    return response
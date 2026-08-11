import traceback

from fastapi import APIRouter, Depends, Request, Form, responses, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate
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
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    otp: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user_in = UserCreate(
            username=username,
            email=email,
            otp=otp,
            phone_number=phone_number,
            password=password
        )
        create_user(db, user_in)
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as ve:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": str(ve)}
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Terjadi kesalahan saat pendaftaran."}
        )

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Username atau password salah."}
        )
    
    response = responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/logout")
def logout():
    response = responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user_id")
    return response
from fastapi import APIRouter, Depends, Request, Form, responses, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate
from app.services.auth_service import create_user, authenticate_user
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

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
    phone_number: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user_in = UserCreate(username=username, phone_number=phone_number, password=password)
        create_user(db, user_in)
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username/No HP sudah digunakan."}
        )

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
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
            name="login.html",
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
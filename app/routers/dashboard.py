from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.transaction_service import get_user_transactions
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")  # Typo sudah diperbaiki
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Menggunakan JWT Dependency yang aman
):
    # Ambil transaksi berdasarkan user yang sedang login
    transactions = get_user_transactions(db, user_id=current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "transactions": transactions
        }
    )
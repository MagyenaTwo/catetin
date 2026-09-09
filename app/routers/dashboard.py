from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.transaction_service import get_user_transactions
from app.schemas.auth import PhoneUpdateSchema  # Import schema dari file terpisah

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


@router.post("/user/update-phone")
def update_phone_number(
    payload: PhoneUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    phone = payload.phone_number.strip()
    
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Nomor WhatsApp tidak boleh kosong."
        )

    # Simpan nomor HP baru ke database
    current_user.phone_number = phone
    db.commit()
    db.refresh(current_user)

    return {"message": "Nomor WhatsApp berhasil diperbarui."}


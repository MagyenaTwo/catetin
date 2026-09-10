from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, Transaksi_Keluar  # Import model transaksi
# from app.models.stock import Stock  # Import model Stok/Produk kamu jika ada
from app.services.transaction_service import get_user_transactions
from app.schemas.auth import PhoneUpdateSchema

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Hitung Total Pemasukan
    total_masuk = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.user_id == current_user.id)
        .scalar()
    )

    # 2. Hitung Total Pengeluaran
    total_keluar = (
        db.query(func.coalesce(func.sum(Transaksi_Keluar.amount), 0.0))
        .filter(Transaksi_Keluar.user_id == current_user.id)
        .scalar()
    )

    # 3. Hitung Total Saldo (Pemasukan - Pengeluaran)
    total_saldo = total_masuk - total_keluar

    # 4. Hitung Total Transaksi (Banyaknya entri transaksi masuk + keluar)
    count_masuk = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.user_id == current_user.id)
        .scalar()
    )
    count_keluar = (
        db.query(func.count(Transaksi_Keluar.id))
        .filter(Transaksi_Keluar.user_id == current_user.id)
        .scalar()
    )
    total_transaksi = count_masuk + count_keluar

    # 5. Hitung Total Stok
    # Sesuaikan 'Stock' dan nama kolomnya (misal: Stock.quantity atau Stock.stock) dengan model kamu
    # Jika stok belum ada modelnya/belum dipakai, set default ke 0
    total_stock = 0
    # Contoh jika ada model Stock:
    # total_stock = (
    #     db.query(func.coalesce(func.sum(Stock.quantity), 0))
    #     .filter(Stock.user_id == current_user.id)
    #     .scalar()
    # )

    # Ambil transaksi terbaru jika masih dibutuhkan
    transactions = get_user_transactions(db, user_id=current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "total_saldo": total_saldo,
            "total_masuk": total_masuk,
            "total_keluar": total_keluar,
            "total_count": total_transaksi,
            "total_stock": total_stock,
            "transactions": transactions,
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
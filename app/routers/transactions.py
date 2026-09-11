from datetime import datetime
import logging
from typing import List, Optional

import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings  # <-- DITAMBAHKAN: Memastikan Cloudinary terkonfigurasi saat router dimuat
from app.database import get_db
from app.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionResponse

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER
# --------------------------------------------------------------------------
web_router = APIRouter(prefix="/transaksi", tags=["Web Pages"])


@web_router.get("/", response_class=HTMLResponse)
@web_router.get("/in", response_class=HTMLResponse)
def render_transactions_page(
    request: Request,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    templates = (
        request.app.state.templates
        if hasattr(request.app.state, "templates")
        else Jinja2Templates(directory="app/templates")
    )

    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.amount > 0,
    )

    if search and search.strip():
        query = query.filter(Transaction.description.ilike(f"%{search.strip()}%"))

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(Transaction.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(Transaction.created_at <= end_dt)
        except ValueError:
            pass

    transactions = query.order_by(Transaction.created_at.desc()).all()

    total_masuk = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.user_id == current_user.id, Transaction.amount > 0)
        .scalar()
    )

    return templates.TemplateResponse(
        request=request,
        name="transaksi.html",
        context={
            "user": current_user,
            "transactions": transactions,
            "total_masuk": total_masuk,
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/transaksi", tags=["Transactions API"])


@api_router.get("/", response_model=List[TransactionResponse])
def get_user_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    only_income: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if only_income:
        query = query.filter(Transaction.amount > 0)

    if search and search.strip():
        query = query.filter(Transaction.description.ilike(f"%{search.strip()}%"))

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(Transaction.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(Transaction.created_at <= end_dt)
        except ValueError:
            pass

    total_masuk = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.id.in_(query.with_entities(Transaction.id)))
        .scalar()
    )

    logger.info(
        f"[API LOG] User ID: {current_user.id} | Total Pemasukan: {total_masuk}"
    )

    return (
        query.order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    description: str = Form(...),
    amount: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_url = None
    image_public_id = None

    if image and image.filename:
        try:
            upload_result = cloudinary.uploader.upload(
                image.file, folder="transactions"
            )
            image_url = upload_result.get("secure_url")
            image_public_id = upload_result.get("public_id")
        except Exception as e:
            logger.error(f"Gagal mengunggah gambar ke Cloudinary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal mengunggah gambar.",
            )

    new_txn = Transaction(
        user_id=current_user.id,
        description=description,
        amount=amount,
        image_url=image_url,
        image_public_id=image_public_id,
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn


@api_router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan.",
        )
    return txn


@api_router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    description: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan.",
        )

    if description is not None:
        txn.description = description
    if amount is not None:
        txn.amount = amount

    # Jika mengunggah gambar baru
    if image and image.filename:
        try:
            # Hapus gambar lama di Cloudinary jika ada
            if txn.image_public_id:
                cloudinary.uploader.destroy(txn.image_public_id)

            upload_result = cloudinary.uploader.upload(
                image.file, folder="transactions"
            )
            txn.image_url = upload_result.get("secure_url")
            txn.image_public_id = upload_result.get("public_id")
        except Exception as e:
            logger.error(f"Gagal memperbarui gambar di Cloudinary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal memperbarui gambar.",
            )

    db.commit()
    db.refresh(txn)
    return txn


@api_router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan.",
        )

    # Hapus file dari Cloudinary
    if txn.image_public_id:
        try:
            cloudinary.uploader.destroy(txn.image_public_id)
        except Exception as e:
            logger.error(f"Gagal menghapus gambar dari Cloudinary: {str(e)}")

    db.delete(txn)
    db.commit()
    return {"message": "Transaksi berhasil dihapus."}
from datetime import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Khusus Rendering Tampilan HTML / Frontend)
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
        query = query.filter(
            Transaction.description.ilike(f"%{search.strip()}%")
        )

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

    # Kirim user ke context agar base.html tidak error
    return templates.TemplateResponse(
        request=request,
        name="transaksi.html",  # sesuaikan dengan nama template HTML kamu
        context={
            "user": current_user,
            "transactions": transactions,
            "total_masuk": total_masuk,
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER (Khusus Endpoint JSON Data)
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
    """API JSON yang dipanggil via Fetch/Axios dari FE"""
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if only_income:
        query = query.filter(Transaction.amount > 0)

    if search and search.strip():
        query = query.filter(
            Transaction.description.ilike(f"%{search.strip()}%")
        )

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
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_txn = Transaction(
        user_id=current_user.id,
        description=data.description,
        amount=data.amount,
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
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
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

    if data.description is not None:
        txn.description = data.description
    if data.amount is not None:
        txn.amount = data.amount

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

    db.delete(txn)
    db.commit()
    return {"message": "Transaksi berhasil dihapus."}
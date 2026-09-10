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
from app.models.transaction import Transaksi_Keluar
from app.models.user import User
from app.schemas.transaksi_keluar import (
    Transaksi_KeluarCreate,
    Transaksi_KeluarResponse,
    Transaksi_KeluarUpdate,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Khusus Rendering Tampilan HTML / Frontend)
# --------------------------------------------------------------------------
web_router = APIRouter(prefix="/transaksi-keluar", tags=["Web Pages - Transaksi Keluar"])


@web_router.get("/", response_class=HTMLResponse)
@web_router.get("/out", response_class=HTMLResponse)
def render_expense_transactions_page(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
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

    query = db.query(Transaksi_Keluar).filter(
        Transaksi_Keluar.user_id == current_user.id
    )

    if search and search.strip():
        query = query.filter(
            Transaksi_Keluar.description.ilike(f"%{search.strip()}%")
        )

    if category and category.strip():
        query = query.filter(
            Transaksi_Keluar.category.ilike(f"%{category.strip()}%")
        )

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(Transaksi_Keluar.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(Transaksi_Keluar.created_at <= end_dt)
        except ValueError:
            pass

    transactions = query.order_by(Transaksi_Keluar.created_at.desc()).all()

    # Menghitung total keluar sesuai filter aktif
    total_keluar = sum(t.amount for t in transactions if t.amount)

    return templates.TemplateResponse(
        request=request,
        name="transaksi_keluar.html",
        context={
            "user": current_user,
            "transactions": transactions,
            "total_keluar": total_keluar,
            "total_count": len(transactions),
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER (Khusus Endpoint JSON Data)
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/transaksi-keluar", tags=["Expense Transactions API"])


@api_router.get("/", response_model=List[Transaksi_KeluarResponse])
def get_user_expense_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """API JSON untuk transaksi keluar (Fetch/Axios)"""
    query = db.query(Transaksi_Keluar).filter(
        Transaksi_Keluar.user_id == current_user.id
    )

    if search and search.strip():
        query = query.filter(
            Transaksi_Keluar.description.ilike(f"%{search.strip()}%")
        )

    if category and category.strip():
        query = query.filter(
            Transaksi_Keluar.category.ilike(f"%{category.strip()}%")
        )

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(Transaksi_Keluar.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(Transaksi_Keluar.created_at <= end_dt)
        except ValueError:
            pass

    total_keluar = (
        db.query(func.coalesce(func.sum(Transaksi_Keluar.amount), 0))
        .filter(Transaksi_Keluar.id.in_(query.with_entities(Transaksi_Keluar.id)))
        .scalar()
    )

    logger.info(
        f"[API LOG] User ID: {current_user.id} | Total Pengeluaran: {total_keluar}"
    )

    return (
        query.order_by(Transaksi_Keluar.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/",
    response_model=Transaksi_KeluarResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense_transaction(
    data: Transaksi_KeluarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_txn = Transaksi_Keluar(
        user_id=current_user.id,
        description=data.description,
        amount=data.amount,
        category=data.category,
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn


@api_router.get("/{transaction_id}", response_model=Transaksi_KeluarResponse)
def get_expense_transaction_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaksi_Keluar)
        .filter(
            Transaksi_Keluar.id == transaction_id,
            Transaksi_Keluar.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi keluar tidak ditemukan.",
        )
    return txn


@api_router.put("/{transaction_id}", response_model=Transaksi_KeluarResponse)
def update_expense_transaction(
    transaction_id: int,
    data: Transaksi_KeluarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaksi_Keluar)
        .filter(
            Transaksi_Keluar.id == transaction_id,
            Transaksi_Keluar.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi keluar tidak ditemukan.",
        )

    if data.description is not None:
        txn.description = data.description
    if data.amount is not None:
        txn.amount = data.amount
    if data.category is not None:
        txn.category = data.category

    db.commit()
    db.refresh(txn)
    return txn


@api_router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_expense_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaksi_Keluar)
        .filter(
            Transaksi_Keluar.id == transaction_id,
            Transaksi_Keluar.user_id == current_user.id,
        )
        .first()
    )

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi keluar tidak ditemukan.",
        )

    db.delete(txn)
    db.commit()
    return {"message": "Transaksi keluar berhasil dihapus."}
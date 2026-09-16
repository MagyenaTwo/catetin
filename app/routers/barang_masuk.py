from datetime import datetime
import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.stock import BarangMasuk, Product
from app.models.user import User
from app.schemas.stock import BarangMasukCreate, BarangMasukResponse

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Render Halaman HTML)
# --------------------------------------------------------------------------
web_router = APIRouter(prefix="/stok-masuk", tags=["Stok Masuk Web Pages"])


@web_router.get("/", response_class=HTMLResponse)
def render_stok_masuk_page(
    request: Request,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Render halaman HTML riwayat stok masuk.
    """
    templates = (
        request.app.state.templates
        if hasattr(request.app.state, "templates")
        else Jinja2Templates(directory="app/templates")
    )

    query = (
        db.query(BarangMasuk)
        .options(joinedload(BarangMasuk.product), joinedload(BarangMasuk.user))
        .filter(BarangMasuk.user_id == current_user.id)
    )

    # Filter berdasarkan pencarian nama barang atau catatan
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.join(BarangMasuk.product).filter(
            (Product.name.ilike(search_term)) | (BarangMasuk.notes.ilike(search_term))
        )

    # Filter rentang tanggal
    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(BarangMasuk.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(BarangMasuk.created_at <= end_dt)
        except ValueError:
            pass

    stok_masuk_list = query.order_by(BarangMasuk.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="stok_masuk.html",  # Pastikan nama file template disesuaikan di folder app/templates
        context={
            "user": current_user,
            "stok_masuk_list": stok_masuk_list,
            "total_items": len(stok_masuk_list),
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/stok-masuk", tags=["Stok Masuk API"])


@api_router.get("/", response_model=List[BarangMasukResponse])
def get_stok_masuk_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan daftar riwayat stok masuk dengan paginasi dan filter.
    """
    query = db.query(BarangMasuk).filter(BarangMasuk.user_id == current_user.id)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.join(BarangMasuk.product).filter(
            (Product.name.ilike(search_term)) | (BarangMasuk.notes.ilike(search_term))
        )

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(BarangMasuk.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(BarangMasuk.created_at <= end_dt)
        except ValueError:
            pass

    total_qty = (
        db.query(func.coalesce(func.sum(BarangMasuk.quantity), 0))
        .filter(BarangMasuk.id.in_(query.with_entities(BarangMasuk.id)))
        .scalar()
    )

    logger.info(
        f"[API LOG] User ID: {current_user.id} | Total Quantity Masuk: {total_qty}"
    )

    return (
        query.order_by(BarangMasuk.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/",
    response_model=BarangMasukResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stok_masuk(
    product_id: int = Form(...),
    quantity: int = Form(...),
    unit_cost: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mencatat transaksi stok masuk dan mengupdate jumlah stok pada tabel Product secara otomatis.
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jumlah stok masuk (quantity) harus lebih besar dari 0.",
        )

    # Validasi keberadaan produk
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == current_user.id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barang/Produk tidak ditemukan.",
        )

    # 1. Buat catatan stok masuk
    new_stok_masuk = BarangMasuk(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
        unit_cost=unit_cost,
        notes=notes,
    )
    db.add(new_stok_masuk)

    # 2. Update/Tambahkan jumlah stok produk terkait
    product.stock = (product.stock or 0) + quantity

    db.commit()
    db.refresh(new_stok_masuk)
    return new_stok_masuk


@api_router.get("/{stok_masuk_id}", response_model=BarangMasukResponse)
def get_stok_masuk_by_id(
    stok_masuk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan detail riwayat stok masuk berdasarkan ID.
    """
    item = (
        db.query(BarangMasuk)
        .filter(
            BarangMasuk.id == stok_masuk_id,
            BarangMasuk.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data stok masuk tidak ditemukan.",
        )
    return item


@api_router.delete("/{stok_masuk_id}", status_code=status.HTTP_200_OK)
def delete_stok_masuk(
    stok_masuk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menghapus riwayat stok masuk dan mengurangi kembali stok barang terkait.
    """
    item = (
        db.query(BarangMasuk)
        .filter(
            BarangMasuk.id == stok_masuk_id,
            BarangMasuk.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data stok masuk tidak ditemukan.",
        )

    # Kurangi kembali stok produk jika data dihapus
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if product:
        product.stock = max(0, (product.stock or 0) - item.quantity)

    db.delete(item)
    db.commit()
    return {"message": "Data stok masuk berhasil dihapus dan stok telah disesuaikan."}
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
from app.models.stock import BarangKeluar, Product
from app.models.user import User
from app.schemas.stock import BarangKeluarCreate, BarangKeluarResponse

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Render Halaman HTML)
# --------------------------------------------------------------------------
web_router = APIRouter(prefix="/stok-keluar", tags=["Stok Keluar Web Pages"])


@web_router.get("/", response_class=HTMLResponse)
def render_stok_keluar_page(
    request: Request,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Render halaman HTML riwayat stok keluar.
    """
    templates = (
        request.app.state.templates
        if hasattr(request.app.state, "templates")
        else Jinja2Templates(directory="app/templates")
    )

    query = (
        db.query(BarangKeluar)
        .options(joinedload(BarangKeluar.product), joinedload(BarangKeluar.user))
        .filter(BarangKeluar.user_id == current_user.id)
    )

    # Filter berdasarkan pencarian nama barang atau catatan
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.join(BarangKeluar.product).filter(
            (Product.name.ilike(search_term)) | (BarangKeluar.notes.ilike(search_term))
        )

    # Filter rentang tanggal
    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(BarangKeluar.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(BarangKeluar.created_at <= end_dt)
        except ValueError:
            pass

    stok_keluar_list = query.order_by(BarangKeluar.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="stok_keluar.html",  # Pastikan nama file template disesuaikan di folder app/templates
        context={
            "user": current_user,
            "stok_keluar_list": stok_keluar_list,
            "total_items": len(stok_keluar_list),
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/stok-keluar", tags=["Stok Keluar API"])


@api_router.get("/", response_model=List[BarangKeluarResponse])
def get_stok_keluar_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan daftar riwayat stok keluar dengan paginasi dan filter.
    """
    query = db.query(BarangKeluar).filter(BarangKeluar.user_id == current_user.id)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.join(BarangKeluar.product).filter(
            (Product.name.ilike(search_term)) | (BarangKeluar.notes.ilike(search_term))
        )

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(BarangKeluar.created_at >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(
                f"{end_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            )
            query = query.filter(BarangKeluar.created_at <= end_dt)
        except ValueError:
            pass

    total_qty = (
        db.query(func.coalesce(func.sum(BarangKeluar.quantity), 0))
        .filter(BarangKeluar.id.in_(query.with_entities(BarangKeluar.id)))
        .scalar()
    )

    logger.info(
        f"[API LOG] User ID: {current_user.id} | Total Quantity Keluar: {total_qty}"
    )

    return (
        query.order_by(BarangKeluar.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/",
    response_model=BarangKeluarResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stok_keluar(
    product_id: int = Form(...),
    quantity: int = Form(...),
    unit_price: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mencatat transaksi stok keluar/penjualan dan mengurangi jumlah stok pada tabel Product secara otomatis.
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jumlah stok keluar (quantity) harus lebih besar dari 0.",
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

    # Validasi jumlah stok mencukupi
    current_stock = product.stock or 0
    if current_stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stok tidak mencukupi. Stok saat ini: {current_stock}, diminta: {quantity}.",
        )

    # 1. Buat catatan stok keluar
    new_stok_keluar = BarangKeluar(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        notes=notes,
    )
    db.add(new_stok_keluar)

    # 2. Kurangi jumlah stok produk terkait
    product.stock = current_stock - quantity

    db.commit()
    db.refresh(new_stok_keluar)
    return new_stok_keluar


@api_router.get("/{stok_keluar_id}", response_model=BarangKeluarResponse)
def get_stok_keluar_by_id(
    stok_keluar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan detail riwayat stok keluar berdasarkan ID.
    """
    item = (
        db.query(BarangKeluar)
        .filter(
            BarangKeluar.id == stok_keluar_id,
            BarangKeluar.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data stok keluar tidak ditemukan.",
        )
    return item


@api_router.delete("/{stok_keluar_id}", status_code=status.HTTP_200_OK)
def delete_stok_keluar(
    stok_keluar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menghapus riwayat stok keluar dan mengembalikan/menambahkan kembali stok barang terkait.
    """
    item = (
        db.query(BarangKeluar)
        .filter(
            BarangKeluar.id == stok_keluar_id,
            BarangKeluar.user_id == current_user.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data stok keluar tidak ditemukan.",
        )

    # Kembalikan/tambahkan stok produk jika transaksi dibatalkan/dihapus
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if product:
        product.stock = (product.stock or 0) + item.quantity

    db.delete(item)
    db.commit()
    return {"message": "Data stok keluar berhasil dihapus dan stok telah dikembalikan."}
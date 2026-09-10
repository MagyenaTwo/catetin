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
from app.models.stock import BarangKeluar, BarangMasuk, Product
from app.models.user import User
from app.schemas.stock import (
    BarangKeluarCreate,
    BarangKeluarResponse,
    BarangMasukCreate,
    BarangMasukResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Khusus Rendering Tampilan HTML / Frontend)
# --------------------------------------------------------------------------
# FIX: Diubah dari /stock ke /stok agar cocok dengan endpoint HTML
web_router = APIRouter(prefix="/stock", tags=["Stock Web Pages"])


@web_router.get("/", response_class=HTMLResponse)
@web_router.get("", response_class=HTMLResponse)
def render_stock_page(
    request: Request,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    templates = (
        request.app.state.templates
        if hasattr(request.app.state, "templates")
        else Jinja2Templates(directory="app/templates")
    )

    query = db.query(Product).filter(Product.user_id == current_user.id)

    if search and search.strip():
        query = query.filter(Product.name.ilike(f"%{search.strip()}%"))

    products = query.order_by(Product.created_at.desc()).all()

    total_produk = len(products)
    total_stok = (
        db.query(func.coalesce(func.sum(Product.stock), 0))
        .filter(Product.user_id == current_user.id)
        .scalar()
    )

    return templates.TemplateResponse(
        request=request,
        name="stock.html", # Memastikan merender stok.html
        context={
            "user": current_user,
            "products": products,
            "total_produk": total_produk,
            "total_stok": total_stok,
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER (Khusus Endpoint JSON Data)
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/stock", tags=["Stock API"])

# --- PRODUCT ENDPOINTS ---

@api_router.get("/products", response_model=List[ProductResponse])
def get_user_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Product).filter(Product.user_id == current_user.id)

    if search and search.strip():
        query = query.filter(Product.name.ilike(f"%{search.strip()}%"))

    return (
        query.order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Cek jika SKU sudah pernah digunakan oleh user yang sama
    if data.sku and data.sku.strip():
        existing_sku = (
            db.query(Product)
            .filter(
                Product.user_id == current_user.id,
                Product.sku == data.sku.strip(),
            )
            .first()
        )
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU produk sudah digunakan.",
            )

    new_product = Product(
        user_id=current_user.id,
        name=data.name,
        sku=data.sku,
        stock=data.stock,
        unit=data.unit,
        buy_price=data.buy_price,
        sell_price=data.sell_price,
        min_stock=data.min_stock,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@api_router.get("/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )
    return product


@api_router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    # Validasi SKU unik jika diubah
    if data.sku is not None and data.sku.strip() != product.sku:
        existing_sku = (
            db.query(Product)
            .filter(
                Product.user_id == current_user.id,
                Product.sku == data.sku.strip(),
                Product.id != product_id,
            )
            .first()
        )
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU produk sudah digunakan.",
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@api_router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    # Hapus transaksi barang masuk & keluar terkait secara eksplisit 
    # untuk mencegah error relasi / cascade FK
    db.query(BarangMasuk).filter(BarangMasuk.product_id == product_id).delete(synchronize_session=False)
    db.query(BarangKeluar).filter(BarangKeluar.product_id == product_id).delete(synchronize_session=False)

    db.delete(product)
    db.commit()
    return {"message": "Produk berhasil dihapus."}


# --- TRANSAKSI BARANG MASUK & KELUAR ENDPOINTS ---

@api_router.post(
    "/in",
    response_model=BarangMasukResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_barang_masuk(
    data: BarangMasukCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mencatat barang masuk dan otomatis MENAMBAH stok produk."""
    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.user_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    # 1. Catat transaksi barang masuk
    new_entry = BarangMasuk(
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity,
        unit_cost=data.unit_cost if hasattr(data, 'unit_cost') and data.unit_cost else getattr(product, 'buy_price', 0),
        notes=data.notes,
    )
    db.add(new_entry)

    # 2. Update stok otomatis
    product.stock += data.quantity

    db.commit()
    db.refresh(new_entry)

    logger.info(
        f"[STOK MASUK] User: {current_user.id} | Product ID: {product.id} | "
        f"Tambah: {data.quantity} | Stok Sekarang: {product.stock}"
    )

    return new_entry


@api_router.post(
    "/out",
    response_model=BarangKeluarResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_barang_keluar(
    data: BarangKeluarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mencatat barang keluar dan otomatis MENGURANGI stok produk."""
    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.user_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produk tidak ditemukan.",
        )

    if product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stok tidak mencukupi. Stok saat ini: {product.stock}",
        )

    # 1. Catat transaksi barang keluar
    new_exit = BarangKeluar(
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity,
        unit_price=data.unit_price if hasattr(data, 'unit_price') and data.unit_price else getattr(product, 'sell_price', 0),
        notes=data.notes,
    )
    db.add(new_exit)

    # 2. Update stok otomatis
    product.stock -= data.quantity

    db.commit()
    db.refresh(new_exit)

    logger.info(
        f"[STOK KELUAR] User: {current_user.id} | Product ID: {product.id} | "
        f"Kurang: {data.quantity} | Stok Sekarang: {product.stock}"
    )

    return new_exit
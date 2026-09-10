from pydantic import BaseModel, ConfigDict, Field, PositiveInt
from datetime import datetime
from typing import Optional


# ==========================================
# PRODUCT SCHEMAS
# ==========================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Kopi Susu Gula Aren")
    sku: Optional[str] = Field(None, max_length=100, example="KOP-001")
    unit: str = Field(default="pcs", max_length=50, example="pcs")
    buy_price: Optional[float] = Field(default=0.0, ge=0, example=15000.0)
    sell_price: Optional[float] = Field(default=0.0, ge=0, example=25000.0)
    min_stock: Optional[int] = Field(default=0, ge=0, example=5)


class ProductCreate(ProductBase):
    stock: int = Field(default=0, ge=0, description="Stok awal produk", example=10)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    buy_price: Optional[float] = Field(None, ge=0)
    sell_price: Optional[float] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    id: int
    user_id: int
    stock: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# BARANG MASUK SCHEMAS
# ==========================================

class BarangMasukCreate(BaseModel):
    product_id: int = Field(..., description="ID Produk yang masuk")
    quantity: PositiveInt = Field(..., description="Jumlah barang masuk (harus > 0)", example=50)
    unit_cost: Optional[float] = Field(None, ge=0, description="Harga beli per unit saat transaksi", example=14500.0)
    notes: Optional[str] = Field(None, max_length=500, example="Restock dari Supplier A")


class BarangMasukResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    unit_cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    
    # Menampilkan ringkasan produk di dalam response (opsional)
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# BARANG KELUAR SCHEMAS
# ==========================================

class BarangKeluarCreate(BaseModel):
    product_id: int = Field(..., description="ID Produk yang keluar")
    quantity: PositiveInt = Field(..., description="Jumlah barang keluar (harus > 0)", example=5)
    unit_price: Optional[float] = Field(None, ge=0, description="Harga jual per unit saat transaksi", example=25000.0)
    notes: Optional[str] = Field(None, max_length=500, example="Penjualan toko online")


class BarangKeluarResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    unit_price: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    # Menampilkan ringkasan produk di dalam response (opsional)
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)
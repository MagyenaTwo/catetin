from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """Tabel master data barang/stok"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    sku = Column(String, nullable=True, index=True)  # Kode unik barang
    stock = Column(Integer, default=0, nullable=False)  # Sisa stok saat ini
    unit = Column(String, default="pcs", nullable=False)  # Pcs, kg, box, dll.
    
    # Opsional: Tambahkan jika butuh lacak harga & stok minimal
    buy_price = Column(Float, default=0.0, nullable=True)
    sell_price = Column(Float, default=0.0, nullable=True)
    min_stock = Column(Integer, default=0, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique Constraint: Satu user tidak boleh punya 2 SKU yang sama
    __table_args__ = (
        UniqueConstraint('user_id', 'sku', name='unique_user_sku'),
    )

    # Relationship
    user = relationship("User", back_populates="products")
    barang_masuk = relationship("BarangMasuk", back_populates="product", cascade="all, delete-orphan")
    barang_keluar = relationship("BarangKeluar", back_populates="product", cascade="all, delete-orphan")


class BarangMasuk(Base):
    """Tabel riwayat penerimaan/pembelian stok barang"""
    __tablename__ = "barang_masuk"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)  # Jumlah barang masuk
    unit_cost = Column(Float, nullable=True)   # Harga beli per unit (opsional)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="barang_masuk")
    product = relationship("Product", back_populates="barang_masuk")


class BarangKeluar(Base):
    """Tabel riwayat pengeluaran/penjualan stok barang"""
    __tablename__ = "barang_keluar"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)  # Jumlah barang keluar
    unit_price = Column(Float, nullable=True)  # Harga jual per unit (opsional)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="barang_keluar")
    product = relationship("Product", back_populates="barang_keluar")
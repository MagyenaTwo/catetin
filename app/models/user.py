from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)

    # Relasi yang sudah ada
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    transaksi_keluar = relationship("Transaksi_Keluar", back_populates="user", cascade="all, delete-orphan")

    # TAMBAHKAN RELASI STOK DI SINI:
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    barang_masuk = relationship("BarangMasuk", back_populates="user", cascade="all, delete-orphan")
    barang_keluar = relationship("BarangKeluar", back_populates="user", cascade="all, delete-orphan")


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
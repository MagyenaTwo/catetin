from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
  __tablename__ = "transactions"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  description = Column(String, nullable=False)
  amount = Column(Float, nullable=False)

  # Kolom baru untuk menyalankan URL & Public ID Cloudinary
  image_url = Column(String, nullable=True)
  image_public_id = Column(String, nullable=True)

  created_at = Column(DateTime(timezone=True), server_default=func.now())

  user = relationship("User", back_populates="transactions")

class Transaksi_Keluar(Base):
    __tablename__ = "transaksi_keluar"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)

    # Kolom baru ditambahkan untuk menyalankan URL & Public ID Cloudinary
    image_url = Column(String, nullable=True)
    image_public_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship ke model User
    user = relationship("User", back_populates="transaksi_keluar")
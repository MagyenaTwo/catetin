from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base

class MonthlyRecap(Base):
    __tablename__ = "monthly_recaps"

    id = Column(Integer, primary_key=True, index=True)
    bulan = Column(Integer, nullable=False) # 1 - 12
    tahun = Column(Integer, nullable=False) # misal 2026
    total_konten = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Mencegah duplikasi rekap di bulan & tahun yang sama
    __table_args__ = (
        UniqueConstraint('bulan', 'tahun', name='_bulan_tahun_uc'),
    )
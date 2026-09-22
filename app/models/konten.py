from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CreatorPerformance(Base):
    __tablename__ = "creator_performance"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    akun = Column(String(100), nullable=False)
    status_vt = Column(String(20), default="Kerkun")
    views = Column(Integer, default=0)
    link_video = Column(Text, nullable=False)
    tanggal_upload = Column(Date, nullable=False)
    status_upload = Column(String(20), default="Uploaded")
    review = Column(String(20), default="Not Yet")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
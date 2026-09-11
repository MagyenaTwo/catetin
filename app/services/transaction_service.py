from typing import Optional
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.transaction import Transaksi_Keluar  # Sesuaikan nama file/class model kamu


# ==========================================
# TRANSAKSI (MASUK)
# ==========================================

def get_user_transactions(db: Session, user_id: int):
    return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).all()
def create_transaction(
    db: Session,
    user_id: int,
    description: str,
    amount: float,
    image_url: Optional[str] = None,
    image_public_id: Optional[str] = None,
) -> Transaction:
  new_txn = Transaction(
      user_id=user_id,
      description=description,
      amount=amount,
      image_url=image_url,
      image_public_id=image_public_id,
  )
  db.add(new_txn)
  db.commit()
  db.refresh(new_txn)
  return new_txn


# ==========================================
# TRANSAKSI KELUAR
# ==========================================

def get_user_transaksi_keluar(db: Session, user_id: int):
    return db.query(Transaksi_Keluar).filter(Transaksi_Keluar.user_id == user_id).order_by(Transaksi_Keluar.created_at.desc()).all()

def create_transaksi_keluar(db: Session, user_id: int, description: str, amount: float, category: Optional[str] = None) -> Transaksi_Keluar:
    new_txn = Transaksi_Keluar(
        user_id=user_id,
        description=description,
        amount=amount,
        category=category
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn
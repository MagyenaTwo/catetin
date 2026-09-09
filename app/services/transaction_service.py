from sqlalchemy.orm import Session
from app.models.transaction import Transaction

def get_user_transactions(db: Session, user_id: int):
    return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).all()

def create_transaction(db: Session, user_id: int, description: str, amount: float) -> Transaction:
    new_txn = Transaction(
        user_id=user_id,
        description=description,
        amount=amount
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn
    

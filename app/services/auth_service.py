import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.context import CryptContext
from app.models.user import User, OTPVerification
from app.schemas.auth import UserCreate
from app.services.email_services import send_otp_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_and_send_otp(db: Session, email: str):
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email sudah terdaftar.")

    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    otp_record = db.query(OTPVerification).filter(OTPVerification.email == email).first()
    if otp_record:
        otp_record.otp_code = otp_code
        otp_record.expires_at = expires_at
    else:
        otp_record = OTPVerification(email=email, otp_code=otp_code, expires_at=expires_at)
        db.add(otp_record)
    
    db.commit()

    if not send_otp_email(email, otp_code):
        raise ValueError("Gagal mengirim email OTP.")

def create_user(db: Session, user: UserCreate) -> User:
    if db.query(User).filter(User.username == user.username).first():
        raise ValueError("Username sudah digunakan.")

    email_val = user.email.strip() if user.email else None
    phone_val = user.phone_number.strip().replace("+", "") if user.phone_number else None

    if not email_val and not phone_val:
        raise ValueError("Email atau Nomor WhatsApp wajib diisi.")

    if email_val:
        if db.query(User).filter(User.email == email_val).first():
            raise ValueError("Email sudah terdaftar.")
        
        if not user.otp:
            raise ValueError("Kode OTP wajib diisi untuk pendaftaran via email.")

        otp_record = db.query(OTPVerification).filter(
            OTPVerification.email == email_val,
            OTPVerification.otp_code == user.otp
        ).first()

        if not otp_record:
            raise ValueError("Kode OTP tidak valid.")
        
        if datetime.now(timezone.utc) > otp_record.expires_at.replace(tzinfo=timezone.utc) if otp_record.expires_at.tzinfo is None else otp_record.expires_at:
            raise ValueError("Kode OTP sudah kadaluwarsa.")
        
        db.delete(otp_record)

    if phone_val:
        if db.query(User).filter(User.phone_number == phone_val).first():
            raise ValueError("Nomor WhatsApp sudah digunakan.")

    db_user = User(
        username=user.username,
        email=email_val,
        phone_number=phone_val,
        hashed_password=hash_password(user.password)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, identifier: str, password: str):
    clean_identifier = identifier.strip().replace("+", "")
    
    user = db.query(User).filter(
        or_(
            User.username == identifier,
            User.email == identifier,
            User.phone_number == clean_identifier
        )
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
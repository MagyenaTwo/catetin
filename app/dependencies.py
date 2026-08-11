from urllib.parse import unquote
import os
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_123456789")
ALGORITHM = "HS256"

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token_cookie = request.cookies.get("access_token")

    if not token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak. Silakan login terlebih dahulu."
        )

    token_cookie = unquote(token_cookie)
    if token_cookie.lower().startswith("bearer "):
        token = token_cookie[7:].strip()
    elif " " in token_cookie:
        token = token_cookie.split(" ")[1].strip()
    else:
        token = token_cookie.strip()

    is_blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah dicabut."
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid."
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token kadaluwarsa atau tidak valid."
        )

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pengguna tidak ditemukan."
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error database."
        )

    return user
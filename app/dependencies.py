from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User  # Sesuaikan lokasi Model User Anda
from app.routers.auth import SECRET_KEY, ALGORITHM  # Import kunci rahasia yang sama


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak. Silakan login terlebih dahulu."
        )

    try:
        scheme, token = token_cookie.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Skema token tidak valid."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format token cookie tidak valid."
        )

    # -------------------------------------------------------------
    # PENGECEKAN BLACKLIST
    # -------------------------------------------------------------
    is_blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah dicabut. Silakan login kembali."
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

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan."
        )

    return user
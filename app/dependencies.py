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
    print("\n" + "="*50)
    print("[DEBUG GET_CURRENT_USER] RUNNING CHECK...")

    # 1. Cek Cookie
    token_cookie = request.cookies.get("access_token")
    print(f"[DEBUG 1] RAW COOKIE FROM REQUEST: {repr(token_cookie)}")

    if not token_cookie:
        print("[FAIL 1] Cookie 'access_token' TIDAK DITEMUKAN di request header!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak. Silakan login terlebih dahulu."
        )

    # 2. Extract Token
    token_cookie = unquote(token_cookie)
    if token_cookie.lower().startswith("bearer "):
        token = token_cookie[7:].strip()
    elif " " in token_cookie:
        token = token_cookie.split(" ")[1].strip()
    else:
        token = token_cookie.strip()

    print(f"[DEBUG 2] EXTRACTED CLEAN TOKEN: {repr(token)}")

    # 3. Cek Blacklist
    try:
        is_blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
        print(f"[DEBUG 3] IS BLACKLISTED: {is_blacklisted is not None}")
        if is_blacklisted:
            print("[FAIL 3] Token ini terdaftar di BlacklistedToken!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesi telah dicabut."
            )
    except Exception as e:
        print(f"[ERROR DB BLACKLIST CHECK]: {e}")

    # 4. Decode JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[DEBUG 4] JWT DECODED PAYLOAD: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            print("[FAIL 4] Claim 'sub' (User ID) tidak ditemukan di payload JWT!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid."
            )
    except JWTError as e:
        print(f"[FAIL 4] JWT DECODE ERROR: {e}")
        print(f"[FAIL 4] SECRET_KEY USED FOR DECODE: {repr(SECRET_KEY)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token kadaluwarsa atau tidak valid."
        )

    # 5. Cek User di DB
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        print(f"[DEBUG 5] DB QUERY USER: {user}")
        if user is None:
            print(f"[FAIL 5] User ID {user_id} TIDAK DITEMUKAN di database!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Pengguna tidak ditemukan."
            )
    except Exception as e:
        print(f"[FAIL 5] DB ERROR WHILST FETCHING USER: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error database."
        )

    print("[SUCCESS] USER AUTHENTICATED SUCCESSFULLY!")
    print("="*50 + "\n")
    return user
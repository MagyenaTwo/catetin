from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base, get_db
from app.dependencies import get_current_user
from app.routers import stock
from app.models.user import User
from app.routers import auth, dashboard, transactions, transaksi_keluar, whatsapp
import app.models
from app.services.transaction_service import get_user_transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Transaction Tracker")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 1. Daftarkan router yang di-import dari modul app.routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(whatsapp.router)
app.include_router(transactions.web_router)
app.include_router(transactions.api_router)
app.include_router(transaksi_keluar.web_router)
app.include_router(transaksi_keluar.api_router)

app.include_router(stock.web_router)
app.include_router(stock.api_router)

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/db-check")
def check_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Berhasil terhubung ke Supabase PostgreSQL!"}
    except Exception as e:
        return {"status": "error", "message": f"Gagal konek ke database: {str(e)}"}


# 2. Perbaikan Custom Exception Handler untuk 401 & Browser Navigation
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")

    # Tangkap jika error 401 Unauthenticated
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Browser navigasi menyertakan text/html atau dest=document
        is_html_request = "text/html" in accept or request.headers.get("sec-fetch-dest") == "document"
        
        if is_html_request:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Untuk request API / Fetch JSON, tetap kembalikan JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None)
    )

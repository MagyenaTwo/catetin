from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base, get_db
from app.routers import auth, dashboard, whatsapp
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Transaction Tracker")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(whatsapp.router)


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

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")

    # Jika request meminta halaman HTML (misal user buka URL /dashboard di browser tanpa login)
    if "text/html" in accept and exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Untuk request API/JSON (AJAX fetch), kembalikan response JSON asli dari FastAPI
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )
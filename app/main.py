from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from streamlit import status
from streamlit import status
from app.database import engine, Base, get_db
from app.routers import auth, dashboard, whatsapp
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Transaction Tracker")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

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
    # Jika error 401 terjadi saat meminta halaman web HTML
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Jika request meminta halaman HTML (bukan request API AJAX/Fetch JSON)
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
            
    return RedirectResponse(url="/login")
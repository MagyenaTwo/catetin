from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
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
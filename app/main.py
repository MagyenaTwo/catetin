from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, dashboard, whatsapp

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Transaction Tracker")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(whatsapp.router)

@app.get("/")
def root():
    return {"message": "Sistem Aktif. Silakan akses /login atau /register."}

from datetime import datetime
import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.konten import CreatorPerformance
from app.models.rekap import MonthlyRecap  # Model untuk rekap
from app.models.user import User
from app.schemas.konten import ContentCreate, ContentResponse, ContentUpdate
from app.schemas.rekap import RecapCreate, RecapResponse  # Schema rekap

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. WEB ROUTER (Render Template HTML)
# --------------------------------------------------------------------------
web_router = APIRouter(prefix="/konten", tags=["Konten Web Pages"])


@web_router.get("/", response_class=HTMLResponse)
def render_konten_page(
    request: Request,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status_vt: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    templates = (
        request.app.state.templates
        if hasattr(request.app.state, "templates")
        else Jinja2Templates(directory="app/templates")
    )

    query = db.query(CreatorPerformance)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (CreatorPerformance.nama.ilike(search_term))
            | (CreatorPerformance.akun.ilike(search_term))
        )

    if status_vt and status_vt.strip():
        query = query.filter(CreatorPerformance.status_vt == status_vt.strip())

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(CreatorPerformance.tanggal_upload >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d")
            query = query.filter(CreatorPerformance.tanggal_upload <= end_dt)
        except ValueError:
            pass

    contents_db = query.order_by(CreatorPerformance.tanggal_upload.desc()).all()

    total_views = (
        db.query(func.coalesce(func.sum(CreatorPerformance.views), 0))
        .filter(CreatorPerformance.id.in_(query.with_entities(CreatorPerformance.id)))
        .scalar()
    )

    # Ambil riwayat rekap bulanan untuk ditampilkan di template
    recaps_db = (
        db.query(MonthlyRecap)
        .order_by(MonthlyRecap.tahun.desc(), MonthlyRecap.bulan.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="konten.html",
        context={
            "user": current_user,
            "contents": contents_db,
            "total_views": total_views,
            "recaps": recaps_db,
        },
    )


# --------------------------------------------------------------------------
# 2. REST API ROUTER
# --------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1/konten", tags=["Konten API"])


# --- ENDPOINT REKAP BULANAN (Posisikan di paling atas) ---

@api_router.get("/rekap", response_model=List[RecapResponse])
def get_all_recaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar semua rekap bulanan yang tersimpan."""
    return (
        db.query(MonthlyRecap)
        .order_by(MonthlyRecap.tahun.desc(), MonthlyRecap.bulan.desc())
        .all()
    )


@api_router.post(
    "/rekap",
    response_model=RecapResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_monthly_recap(
    payload: RecapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hitung agregasi data bulan tertentu lalu simpan sebagai snapshot rekap."""
    # Cek duplikasi
    existing_recap = (
        db.query(MonthlyRecap)
        .filter(
            MonthlyRecap.bulan == payload.bulan,
            MonthlyRecap.tahun == payload.tahun,
        )
        .first()
    )

    if existing_recap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rekap untuk bulan {payload.bulan} tahun {payload.tahun} sudah pernah disimpan.",
        )

    # Hitung total konten & views berdasarkan bulan & tahun upload
    total_konten = (
        db.query(CreatorPerformance)
        .filter(
            extract("month", CreatorPerformance.tanggal_upload) == payload.bulan,
            extract("year", CreatorPerformance.tanggal_upload) == payload.tahun,
        )
        .count()
    )

    total_views = (
        db.query(func.coalesce(func.sum(CreatorPerformance.views), 0))
        .filter(
            extract("month", CreatorPerformance.tanggal_upload) == payload.bulan,
            extract("year", CreatorPerformance.tanggal_upload) == payload.tahun,
        )
        .scalar()
    )

    new_recap = MonthlyRecap(
        bulan=payload.bulan,
        tahun=payload.tahun,
        total_konten=total_konten,
        total_views=total_views,
    )

    db.add(new_recap)
    db.commit()
    db.refresh(new_recap)
    return new_recap


# --- ENDPOINT KONTEN UTAMA ---

@api_router.get("/", response_model=List[ContentResponse])
def get_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CreatorPerformance)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (CreatorPerformance.nama.ilike(search_term))
            | (CreatorPerformance.akun.ilike(search_term))
        )

    if start_date and start_date.strip():
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(CreatorPerformance.tanggal_upload >= start_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d")
            query = query.filter(CreatorPerformance.tanggal_upload <= end_dt)
        except ValueError:
            pass

    logger.info(f"[API LOG] User ID: {current_user.id} fetching content performance")

    return (
        query.order_by(CreatorPerformance.tanggal_upload.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@api_router.post(
    "/",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_content = CreatorPerformance(**payload.model_dump())
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content


# --- ENDPOINT DETAIL, UPDATE, DELETE KONTEN BY ID (Selalu di Paling Bawah) ---

@api_router.get("/{content_id}", response_model=ContentResponse)
def get_content_by_id(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = (
        db.query(CreatorPerformance)
        .filter(CreatorPerformance.id == content_id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data konten tidak ditemukan.",
        )
    return content


@api_router.put("/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: int,
    payload: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = (
        db.query(CreatorPerformance)
        .filter(CreatorPerformance.id == content_id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data konten tidak ditemukan.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content, key, value)

    db.commit()
    db.refresh(content)
    return content


@api_router.delete("/{content_id}", status_code=status.HTTP_200_OK)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = (
        db.query(CreatorPerformance)
        .filter(CreatorPerformance.id == content_id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data konten tidak ditemukan.",
        )

    db.delete(content)
    db.commit()
    return {"message": "Data konten berhasil dihapus."}
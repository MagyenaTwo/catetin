from fastapi import APIRouter, Depends, Request, responses, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.transaction_service import get_user_transactions
from app.models.user import User
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    transactions = get_user_transactions(db, user_id=user.id)

    # Perubahan di baris ini: request dipindah ke argumen pertama
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "transactions": transactions
        }
    )
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.services.whatsapp_service import process_whatsapp_payload, send_whatsapp_message
from app.services.ai_service import generate_ai_reply
from app.config import settings

router = APIRouter(prefix=settings.WEBHOOK_PREFIX, tags=[settings.WEBHOOK_TAG])

BOT_PHONE_NUMBER = "628999239305" 

def process_ai_and_reply(db_session_factory, sender: str, message: str):
    db = db_session_factory()
    try:
        tx_result = process_whatsapp_payload(db, sender=sender, message=message)
        ai_reply = generate_ai_reply(user_message=message, transaction_result=tx_result)
        send_whatsapp_message(target=sender, reply_text=ai_reply)
    finally:
        db.close()

@router.api_route("/whatsapp", methods=["GET", "POST"])
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    if request.method == "GET":
        return {"status": "success", "message": "Webhook active"}

    json_data = {}
    try:
        json_data = await request.json()
    except Exception:
        pass

    form_data = {}
    try:
        form = await request.form()
        form_data = dict(form)
    except Exception:
        pass

    payload = {**form_data, **json_data}

    if payload.get("status") or payload.get("id") or "device" in payload and not payload.get("message"):
        return {"status": "ignored", "message": "Delivery status notification ignored"}

    sender = payload.get("sender") or payload.get("from")
    message = payload.get("message") or payload.get("text")

    if sender and message:
        clean_sender = str(sender).replace("+", "").strip()
        clean_message = str(message).strip()
        
        if clean_sender == BOT_PHONE_NUMBER or not clean_message:
            return {"status": "ignored", "message": "Ignored self or empty message"}

        background_tasks.add_task(process_ai_and_reply, SessionLocal, clean_sender, clean_message)

        return {"status": "success", "message": "Processing in background"}

    return {"status": "ignored", "message": "Payload not relevant"}
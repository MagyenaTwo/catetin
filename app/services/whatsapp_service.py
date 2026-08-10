import re
import os
import requests
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.transaction_service import create_transaction

def parse_whatsapp_message(text: str) -> Tuple[Optional[str], Optional[float]]:
    text = text.strip()
    match = re.search(r"^(.*?)\s+(\d+(?:\.\d+)?)\s*(k|rb|ribu)?$", text, re.IGNORECASE)
    if not match:
        return None, None

    desc = match.group(1).strip()
    amount_num = float(match.group(2))
    unit = match.group(3)

    if unit:
        unit = unit.lower()
        if unit in ["k", "rb", "ribu"]:
            amount_num *= 1000

    return desc, amount_num

def process_whatsapp_payload(db: Session, sender: str, message: str):
    clean_sender = sender.strip().replace("+", "")
    user = db.query(User).filter(User.phone_number == clean_sender).first()
    if not user:
        return {"status": "error", "message": "Nomor WhatsApp tidak terdaftar."}

    desc, amount = parse_whatsapp_message(message)
    if not desc or not amount:
        return {"status": "error", "message": "Format pesan tidak valid. Contoh: 'beli kopi 29k'"}

    txn = create_transaction(db, user_id=user.id, description=desc, amount=amount)
    return {
        "status": "success",
        "message": f"Berhasil mencatat '{desc}' sebesar Rp {amount:,.0f} "
    }

def sanitize_text_for_fonnte(text: str) -> str:
    sensitive_words = ["anjing", "babi", "kuntul", "monyet", "bangsat", "kontol", "memek"]
    censored_text = str(text)
    for word in sensitive_words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        if len(word) > 2:
            replacement = word[0] + "*" * (len(word) - 2) + word[-1]
        else:
            replacement = "*" * len(word)
        censored_text = pattern.sub(replacement, censored_text)
    return censored_text

def send_whatsapp_message(target: str, reply_text: str):
    fonnte_token = os.getenv("FONNTE_TOKEN", "")
    if not fonnte_token:
        print("[FONNTE WARNING] FONNTE_TOKEN belum diisi di .env")
        return None

    clean_target = "".join(filter(str.isdigit, str(target)))
    safe_reply_text = sanitize_text_for_fonnte(reply_text)

    url = "https://api.fonnte.com/send"
    headers = {
        "Authorization": fonnte_token
    }
    payload = {
        "target": clean_target,
        "message": safe_reply_text,
        "countryCode": "62"
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        print(f"[FONNTE SEND] Status: {response.status_code}, Response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"[FONNTE SEND ERROR] {str(e)}")
        return None
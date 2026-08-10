import re
import os
import requests
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.transaction_service import create_transaction

LOGO_URL = "https://0259-125-167-191-40.ngrok-free.app/static/logo-catetin.png"

def parse_whatsapp_message(text: str) -> Tuple[Optional[str], Optional[float]]:
    text = text.strip()
    
    pattern = r"^(.*?)\s+(\d+(?:\.\d+)?)\s*(puluhan\s*ribu|ratusan\s*ribu|puluhan\s*juta|ratusan\s*juta|ratusan|ribu|rb|k|juta|jt|miliar|milyar|m)?$"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return None, None

    desc = match.group(1).strip()
    amount_num = float(match.group(2))
    unit = match.group(3)

    if unit:
        unit = re.sub(r"\s+", "", unit.lower())
        
        if unit == "ratusan":
            amount_num *= 100
        elif unit in ["k", "rb", "ribu"]:
            amount_num *= 1000
        elif unit == "puluhanribu":
            amount_num *= 10000
        elif unit == "ratusanribu":
            amount_num *= 100000
        elif unit in ["jt", "juta"]:
            amount_num *= 1000000
        elif unit == "puluhanjuta":
            amount_num *= 10000000
        elif unit == "ratusanjuta":
            amount_num *= 100000000
        elif unit in ["m", "miliar", "milyar"]:
            amount_num *= 1000000000

    return desc, amount_num

def process_whatsapp_payload(db: Session, sender: str, message: str):
    clean_sender = sender.strip().replace("+", "")
    user = db.query(User).filter(User.phone_number == clean_sender).first()
    if not user:
        return {
            "status": "error",
            "type": "unregistered",
            "message": "Nomor WhatsApp tidak terdaftar."
        }

    desc, amount = parse_whatsapp_message(message)
    if not desc or not amount:
        return {
            "status": "chat_only",
            "type": "chat",
            "message": "Pengguna tidak mengirimkan format transaksi."
        }

    txn = create_transaction(db, user_id=user.id, description=desc, amount=amount)
    return {
        "status": "success",
        "type": "transaction",
        "message": f"Berhasil mencatat '{desc}' sebesar Rp {amount:,.0f}"
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
        "url": LOGO_URL,
        "countryCode": "62"
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        return response.json()
    except Exception:
        return None
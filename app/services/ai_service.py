import os
import re
import requests

BYNARA_API_KEY = os.getenv("BYNARA_API_KEY", "")
BYNARA_URL = "https://router.bynara.id/v1/chat/completions"

def get_smart_fallback(user_message: str, transaction_result: dict = None) -> str:
    if transaction_result:
        status = transaction_result.get("status")
        msg = transaction_result.get("message", "")
        if status == "success":
            return f"Siap, pencatatan berhasil! {msg} 👍"
        
    has_numbers = bool(re.search(r'\d', user_message))
    if has_numbers:
        return "Format pencatatan kurang pas nih. Contoh format yang benar: 'beli kopi 29k' atau 'gaji 5jt'."
    
    return "Halo! Ada yang bisa Catetin bantu? Kalau mau catat transaksi, kirim dengan format seperti 'beli kopi 29k' ya!"

def generate_ai_reply(user_message: str, transaction_result: dict = None) -> str:
    fallback = get_smart_fallback(user_message, transaction_result)

    if not BYNARA_API_KEY:
        return fallback

    is_success = transaction_result and transaction_result.get("status") == "success"

    if is_success:
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi di WhatsApp yang ramah dan kasual. "
            "Pengguna baru saja mencatat transaksi keuangan. Berikan konfirmasi pencatatan tersebut dengan gaya bahasa "
            "yang ramah, santai, ringkas (maksimal 2 kalimat), dan tambahkan sedikit saran/catatan manis jika relevan."
        )
        user_prompt = f"Pesan User: '{user_message}'.\nHasil Pencatatan Database: {transaction_result.get('message')}"
    else:
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi di WhatsApp. "
            "Jawab pertanyaan atau pesan pengguna dengan ramah, santai, dan singkat. "
            "Jika pengguna ingin mencatat transaksi, ingatkan format simpelnya (contoh: 'beli kopi 29k' atau 'gaji 5jt')."
        )
        user_prompt = user_message

    headers = {
        "Authorization": f"Bearer {BYNARA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-medium-3-5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        response = requests.post(BYNARA_URL, headers=headers, json=payload, timeout=5)
        
        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            print(f"[BYNARA ERROR {response.status_code}] {response.text}")
            return fallback

    except Exception as e:
        print(f"[BYNARA TIMEOUT/ERROR] {str(e)}")
        return fallback
import os
import re
import requests
from sqlalchemy.orm import Session

from app.models.user import User


BYNARA_API_KEY = os.getenv("BYNARA_API_KEY", "")
BYNARA_URL = "https://router.bynara.id/v1/chat/completions"

session = requests.Session()


def check_user_registered(db: Session, phone_number: str) -> bool:
    if not phone_number:
        return False
    
    clean_phone = re.sub(r"\D", "", phone_number)
    phones_to_check = [clean_phone]
    
    if clean_phone.startswith("62"):
        phones_to_check.append("0" + clean_phone[2:])
    elif clean_phone.startswith("0"):
        phones_to_check.append("62" + clean_phone[1:])

    user = db.query(User).filter(User.phone_number.in_(phones_to_check)).first()
    return user is not None


def get_smart_fallback(user_message: str, transaction_result: dict = None, is_registered: bool = True) -> str:
    if not is_registered:
        return (
            "=========================\n"
            "🔐 *CATETIN SYSTEM*\n"
            "=========================\n\n"
            "⚠️ *AKUN BELUM TERDAFTAR*\n\n"
            "Nomor WhatsApp ini belum terdaftar di Catetin.\n"
            "Silakan mendaftar via Web Dashboard dulu ya!"
        )

    if transaction_result:
        status = transaction_result.get("status")
        msg = transaction_result.get("message", "")
        txn_type = transaction_result.get("type", "pemasukan")  # "pemasukan" atau "pengeluaran/transaksi_keluar"

        if status == "success":
            type_label = "🔴 *PENGELUARAN DICATAT*" if txn_type in ["pengeluaran", "transaksi_keluar"] else "🟢 *PEMASUKAN DICATAT*"
            
            return (
                "=========================\n"
                "🟢 *CATETIN FINANCIAL* 🟢\n"
                "=========================\n\n"
                f"{type_label}\n\n"
                f"📝 {msg}\n\n"
                "=========================\n"
                "💾 _Autosaved_"
            )

        elif status == "error" and transaction_result.get("type") == "unregistered":
            return (
                "=========================\n"
                "🔐 *CATETIN SYSTEM*\n"
                "=========================\n\n"
                "⚠️ *AKUN BELUM TERDAFTAR*\n\n"
                "Nomor WhatsApp ini belum terdaftar di Catetin.\n"
                "Silakan mendaftar via Web Dashboard dulu ya!"
            )

    has_numbers = bool(re.search(r"\d", user_message))

    if has_numbers:
        return (
            "=========================\n"
            "💡 *CATETIN HELPER*\n"
            "=========================\n\n"
            "⚠️ *FORMAT KURANG PAS*\n\n"
            "Formatnya simpel kok, contoh:\n\n"
            "🔴 *Pengeluaran:*\n"
            "• ☕ beli kopi 29k\n"
            "• 🍜 nasi goreng 15rb\n"
            "• ⛽ bensin 50rb\n\n"
            "🟢 *Pemasukan:*\n"
            "• 💰 gaji 5jt\n"
            "• 💵 transferan 500rb"
        )

    return (
        "=========================\n"
        "🟢 *CATETIN ASSISTANT* 🟢\n"
        "=========================\n\n"
        "👋 *Halo! Mau catat transaksi apa hari ini?*\n\n"
        "Langsung ketik aja, contoh:\n\n"
        "🔴 *Pengeluaran:*\n"
        "• ☕ beli kopi 29k\n"
        "• 🍜 makan siang 25rb\n\n"
        "🟢 *Pemasukan:*\n"
        "• 💰 gaji 5jt\n\n"
        "✨ _Nanti otomatis aku masukkan ke catatanmu._"
    )


def generate_ai_reply(db: Session, phone_number: str, user_message: str, transaction_result: dict = None) -> str:
    is_registered = check_user_registered(db, phone_number)
    
    if not is_registered:
        return get_smart_fallback(user_message, transaction_result, is_registered=False)

    fallback = get_smart_fallback(user_message, transaction_result, is_registered=True)

    if not BYNARA_API_KEY:
        return fallback

    is_success = (
        transaction_result
        and transaction_result.get("status") == "success"
    )

    if is_success:
        txn_type = transaction_result.get("type", "pemasukan")
        
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi yang santai, ramah, dan solutif di WhatsApp.\n"
            "Tugasmu: Mengonfirmasi pencatatan transaksi (baik pemasukan maupun transaksi keluar/pengeluaran) ke user dengan gaya bahasa Indonesia sehari-hari yang natural.\n\n"
            "ATURAN FORMAT BALASAN:\n"
            "1. Selalu mulai dengan header ini:\n"
            "=========================\n"
            "🟢 *CATETIN FINANCIAL* 🟢\n"
            "=========================\n\n"
            "2. Lalu konfirmasi transaksi secara singkat dan santai (contoh pengeluaran: 'Sip, pengeluaran kamu berhasil dicatat!', contoh pemasukan: 'Mantap, pemasukan baru tercatat!').\n"
            "3. Tampilkan detail dari database persis seperti ini: 📝 [detail dari database]. Dilarang mengubah nominal angka/deskripsi.\n"
            "4. Tutup dengan footer ini:\n"
            "=========================\n"
            "💾 _Autosaved_"
        )

        user_prompt = (
            f"Pesan User: '{user_message}'\n"
            f"Jenis Transaksi: {txn_type}\n"
            f"Hasil Database: {transaction_result.get('message')}\n\n"
            "Buatkan pesan konfirmasi yang ramah dan luwes."
        )

    else:
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi di WhatsApp yang ramah, gaul tapi sopan, dan responsive.\n"
            "Tugasmu: Membalas sapaan dengan format yang bagus beraturan teksnya, pertanyaan, atau membantu user yang bingung cara pakai.\n\n"
            "ATURAN FORMAT BALASAN:\n"
            "1. Selalu mulai dengan header ini:\n"
            "=========================\n"
            "🟢 *CATETIN ASSISTANT* 🟢\n"
            "=========================\n\n"
            "2. Jawab pesan user secara santai dan natural.\n"
            "3. Jika user kelihatan bingung atau bertanya cara mencatat, berikan contoh format pemasukan & transaksi keluar secara jelas:\n"
            "🔴 Transaksi Keluar:\n"
            "• ☕ beli kopi 29k\n"
            "• ⛽ isi bensin 50rb\n\n"
            "🟢 Pemasukan:\n"
            "• 💰 gaji 5jt\n"
            "4. Dilarang menggunakan backtick (`) pada teks contoh. Dilarang menggunakan box/frame garis kotak."
        )

        user_prompt = user_message

    headers = {
        "Authorization": f"Bearer {BYNARA_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "curl/7.68.0"
    }

    payload = {
        "model": "agnes-2.5-flash",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        response = session.post(
            BYNARA_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()

        print(f"[BYNARA ERROR {response.status_code}] {response.text}")
        return fallback

    except Exception as e:
        print(f"[BYNARA ERROR] {str(e)}")
        return fallback
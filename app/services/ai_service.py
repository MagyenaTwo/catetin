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
            return (
                "```"
                "=========================\n"
                "   🟢 C A T E T I N 🟢   \n"
                "   FINANCIAL ASSISTANT   \n"
                "=========================\n"
                "```\n"
                "✅ *TRANSAKSI BERHASIL DICATAT*\n\n"
                f"📝 {msg}\n\n"
                "```"
                "-------------------------\n"
                " Status  : Auto Saved 💾 \n"
                " Catet   : Makin Praktis \n"
                "========================="
                "```"
            )

        elif status == "error" and transaction_result.get("type") == "unregistered":
            return (
                "```"
                "=========================\n"
                "   🔐 C A T E T I N 🔐   \n"
                "   AKUN BELUM TERDAFTAR  \n"
                "=========================\n"
                "```\n"
                "Waduh, nomor WhatsApp kamu belum terdaftar nih! 🧐\n\n"
                "✨ *Cara Pakai:*\n"
                "Silakan daftar akun terlebih dahulu di Web Dashboard Catetin, lalu coba kirim format transaksi lagi ya!"
            )

    has_numbers = bool(re.search(r'\d', user_message))

    if has_numbers:
        return (
            "```"
            "=========================\n"
            "   💡 C A T E T I N 💡   \n"
            "   FORMAT BELUM PAS      \n"
            "=========================\n"
            "```\n"
            "Hampir benar! Cobalah kirim dengan format simpel ini:\n\n"
            "☕ `beli kopi 29k`\n"
            "🍜 `nasi goreng 15rb`\n"
            "⛽ `isi bensin 50rb`\n"
            "💰 `gaji 5jt`\n\n"
            "⚡ _Langsung ketik & kirim, otomatis terdata!_"
        )

    return (
        "```"
        "=========================\n"
        "   🟢 C A T E T I N 🟢   \n"
        "   YOUR FINANCE PARTNER  \n"
        "=========================\n"
        "```\n"
        "Halo! Ada transaksi yang mau dicatat hari ini? 💸\n\n"
        "Cukup ketik pengeluaran atau pemasukanmu:\n"
        "☕ `beli kopi 29k`\n"
        "💰 `gaji 5jt`\n\n"
        "✨ _Pencatatan keuangan jadi super simpel & cepat!_"
    )

def generate_ai_reply(user_message: str, transaction_result: dict = None) -> str:
    fallback = get_smart_fallback(user_message, transaction_result)
    if not BYNARA_API_KEY:
        return fallback

    is_success = transaction_result and transaction_result.get("status") == "success"

    if is_success:
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi super ramah, cekatan, dan responsif di WhatsApp. "
            "Buat konfirmasi transaksi dalam format WhatsApp yang rapi, ramah, dan keren. "
            "Gunakan header monospace ```=========================\n   🟢 C A T E T I N 🟢\n=========================``` di bagian paling atas. "
            "Tampilkan status sukses, detail transaksi dari database dengan ramah, dan penutup singkat yang menyemangati. "
            "Jangan pernah mengubah nominal atau data transaksi asli dari database."
        )
        user_prompt = (
            f"Pesan User: '{user_message}'\n"
            f"Hasil Pencatatan Database: {transaction_result.get('message')}\n\n"
            "Buat balasan konfirmasi transaksi."
        )
    else:
        system_prompt = (
            "Kamu adalah Catetin, asisten keuangan pribadi di WhatsApp yang ramah dan membantu. "
            "Jawab pesan secara singkat, jelas, menarik, dan berikan panduan format jika user kebingungan. "
            "Selalu gunakan header monospace ```=========================\n   🟢 C A T E T I N 🟢\n=========================``` di bagian paling atas pesan."
        )
        user_prompt = user_message

    headers = {
        "Authorization": f"Bearer {BYNARA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-5.2-free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        response = requests.post(
            BYNARA_URL,
            headers=headers,
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()

        return fallback

    except Exception:
        return fallback
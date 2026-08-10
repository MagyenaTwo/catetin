# FastAPI WhatsApp Transaction Tracker

Aplikasi pemantau transaksi otomatis dari WhatsApp berbasis FastAPI, SQLAlchemy, dan Jinja2 Templates.

## Cara Menjalankan

1. Ekstrak file zip ini dan buka folder di VS Code.
2. Buat virtual environment dan install dependensi:
   ```bash
   python -m venv venv
   # Aktifkan venv:
   # Windows: venv\Scripts\activate
   # Linux/Mac: source venv/bin/activate

   pip install -r requirements.txt
   ```
3. Jalankan aplikasi FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Buka di browser: `http://127.0.0.1:8000/register`

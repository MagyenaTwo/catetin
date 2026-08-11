import resend
import os

resend.api_key = os.getenv("RESEND_API_KEY")
def send_otp_email(to_email: str, otp_code: str):
    try:
        resend.Emails.send({
            "from": "Catetin <onboarding@resend.dev>", # Ganti domain terverifikasi kamu
            "to": [to_email],
            "subject": f"Kode OTP Catetin Anda: {otp_code}",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 400px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                    <h2 style="color: #033a28; text-align: center;">Verifikasi Email</h2>
                    <p style="color: #475569;">Gunakan kode OTP berikut untuk mendaftar di Catetin:</p>
                    <div style="background-color: #f0fdf4; color: #1bb774; font-size: 28px; font-weight: bold; text-align: center; padding: 12px; border-radius: 8px; letter-spacing: 4px;">
                        {otp_code}
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; margin-top: 16px; text-align: center;">Kode berlaku selama 5 menit.</p>
                </div>
            """
        })
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
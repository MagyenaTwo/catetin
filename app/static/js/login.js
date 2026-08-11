let currentRegMethod = 'email';

function showToast(message, type = 'error') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    
    setTimeout(() => {
        toast.className = 'toast hidden';
    }, 4000);
}

function parseErrorMessage(data) {
    if (typeof data.detail === 'string') {
        return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail.length > 0) {
        const err = data.detail[0];
        const fieldName = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : '';
        const fieldMap = {
            'username': 'Username',
            'password': 'Password',
            'email': 'Email',
            'phone_number': 'Nomor WhatsApp',
            'otp': 'Kode OTP'
        };
        const label = fieldMap[fieldName] || fieldName;
        if (err.type === 'missing') {
            return `Field ${label} wajib diisi.`;
        }
        return `${label}: ${err.msg || 'Terjadi kesalahan validasi.'}`;
    }
    return data.message || 'Terjadi kesalahan pada sistem.';
}

function showForm(type) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const navLogin = document.getElementById('nav-login');
    const navRegister = document.getElementById('nav-register');
    const formTitle = document.getElementById('form-title');
    const formSub = document.getElementById('form-sub');

    if (type === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        navLogin.classList.add('active');
        navRegister.classList.remove('active');
        formTitle.textContent = "Selamat Datang";
        formSub.textContent = "Masuk ke akun Anda untuk mulai mengelola pencatatan keuangan secara otomatis.";
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        navLogin.classList.remove('active');
        navRegister.classList.add('active');
        formTitle.textContent = "Buat Akun Baru";
        formSub.textContent = "Daftarkan diri Anda untuk merasakan kemudahan catat keuangan via WhatsApp.";
        switchRegMethod(currentRegMethod);
    }
}

function switchRegMethod(method) {
    currentRegMethod = method;
    const emailSection = document.getElementById('reg-email-section');
    const phoneSection = document.getElementById('reg-phone-section');
    const btnEmail = document.getElementById('btn-method-email');
    const btnPhone = document.getElementById('btn-method-phone');

    const emailInput = document.getElementById('reg-email');
    const phoneInput = document.getElementById('reg-phone');
    const otpInput = document.getElementById('reg-otp');

    if (method === 'email') {
        emailSection.classList.remove('hidden');
        phoneSection.classList.add('hidden');
        btnEmail.classList.add('active');
        btnPhone.classList.remove('active');

        emailInput.required = true;
        phoneInput.required = false;
        phoneInput.value = '';
    } else {
        emailSection.classList.add('hidden');
        phoneSection.classList.remove('hidden');
        btnEmail.classList.remove('active');
        btnPhone.classList.add('active');

        phoneInput.required = true;
        emailInput.required = false;
        otpInput.required = false;
        emailInput.value = '';
        otpInput.value = '';
    }
}

async function requestOTP() {
    const emailInput = document.getElementById('reg-email');
    const email = emailInput.value.trim();
    const btnSendOtp = document.getElementById('btn-send-otp');
    const otpGroup = document.getElementById('otp-group');
    const otpInput = document.getElementById('reg-otp');

    if (!email) {
        showToast('Harap masukkan alamat email terlebih dahulu.', 'error');
        return;
    }

    btnSendOtp.disabled = true;
    btnSendOtp.textContent = 'Mengirim...';

    try {
        const response = await fetch('/send-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Kode OTP telah dikirim ke email Anda.', 'success');
            otpGroup.classList.remove('hidden');
            otpInput.required = true;
            startCooldown(btnSendOtp, 60);
        } else {
            showToast(parseErrorMessage(data), 'error');
            btnSendOtp.disabled = false;
            btnSendOtp.textContent = 'Kirim OTP';
        }
    } catch (error) {
        showToast('Terjadi kesalahan koneksi server.', 'error');
        btnSendOtp.disabled = false;
        btnSendOtp.textContent = 'Kirim OTP';
    }
}

function startCooldown(button, seconds) {
    let timeLeft = seconds;
    button.disabled = true;

    const timer = setInterval(() => {
        button.textContent = `${timeLeft}s`;
        timeLeft--;

        if (timeLeft < 0) {
            clearInterval(timer);
            button.disabled = false;
            button.textContent = 'Kirim Ulang';
        }
    }, 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(loginForm);
        const payload = {};
        formData.forEach((value, key) => {
            const trimmed = value.trim();
            if (trimmed !== '') {
                payload[key] = trimmed;
            }
        });
        const submitBtn = loginForm.querySelector('button[type="submit"]');

        submitBtn.disabled = true;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Login berhasil! Mengalihkan...', 'success');
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/dashboard';
                }, 1000);
            } else {
                showToast(parseErrorMessage(data), 'error');
                submitBtn.disabled = false;
            }
        } catch (error) {
            showToast('Terjadi kesalahan koneksi server.', 'error');
            submitBtn.disabled = false;
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(registerForm);
        const payload = {};
        formData.forEach((value, key) => {
            const trimmed = value.trim();
            if (trimmed !== '') {
                payload[key] = trimmed;
            }
        });
        const submitBtn = registerForm.querySelector('button[type="submit"]');

        submitBtn.disabled = true;

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Pendaftaran berhasil! Silakan masuk.', 'success');
                setTimeout(() => {
                    showForm('login');
                    submitBtn.disabled = false;
                }, 1500);
            } else {
                showToast(parseErrorMessage(data), 'error');
                submitBtn.disabled = false;
            }
        } catch (error) {
            showToast('Terjadi kesalahan koneksi server.', 'error');
            submitBtn.disabled = false;
        }
    });
});
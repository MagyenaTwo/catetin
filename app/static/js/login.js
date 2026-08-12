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

function resetRegisterFormState() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.reset();
    }
    clearOtpBoxes();
    const otpGroup = document.getElementById('otp-group');
    if (otpGroup) {
        otpGroup.classList.add('hidden');
    }
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
        formTitle.textContent = "Masuk";
        formSub.textContent = "Masuk ke akun Anda untuk mulai mengelola pencatatan keuangan secara otomatis.";
        resetRegisterFormState();
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        navLogin.classList.remove('active');
        navRegister.classList.add('active');
        formTitle.textContent = "Buat Akun Baru";
        formSub.textContent = "Daftarkan diri Anda untuk merasakan kemudahan catat keuangan via WhatsApp.";
        if (loginForm) {
            loginForm.reset();
        }
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
    const otpHiddenInput = document.getElementById('reg-otp');

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
        otpHiddenInput.required = false;
        emailInput.value = '';
        otpHiddenInput.value = '';
        clearOtpBoxes();
    }
}

function setupOtpBoxes() {
    const digits = document.querySelectorAll('.otp-digit');
    const hiddenOtp = document.getElementById('reg-otp');

    digits.forEach((digit, index) => {
        digit.addEventListener('input', (e) => {
            const val = e.target.value.replace(/[^0-9]/g, '');
            e.target.value = val;

            if (val && index < digits.length - 1) {
                digits[index + 1].focus();
            }
            updateHiddenOtp();
        });

        digit.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !digit.value && index > 0) {
                digits[index - 1].focus();
            }
        });

        digit.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasted = e.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6);
            if (pasted) {
                pasted.split('').forEach((char, i) => {
                    if (digits[i]) digits[i].value = char;
                });
                if (digits[pasted.length - 1]) digits[pasted.length - 1].focus();
                updateHiddenOtp();
            }
        });
    });

    function updateHiddenOtp() {
        let code = '';
        digits.forEach(d => code += d.value);
        hiddenOtp.value = code;
    }
}

function clearOtpBoxes() {
    const digits = document.querySelectorAll('.otp-digit');
    digits.forEach(d => d.value = '');
    const hiddenOtp = document.getElementById('reg-otp');
    if (hiddenOtp) {
        hiddenOtp.value = '';
    }
}

function validatePasswordCombination(password) {
    const minLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    return minLength && hasUpper && hasLower && hasNumber;
}

function setBtnLoading(button, isLoading, originalText) {
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');

    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.textContent = 'Memproses...';
        if (spinner) spinner.classList.remove('hidden');
    } else {
        button.disabled = false;
        if (btnText) btnText.textContent = originalText;
        if (spinner) spinner.classList.add('hidden');
    }
}

async function requestOTP() {
    const emailInput = document.getElementById('reg-email');
    const email = emailInput.value.trim();
    const btnSendOtp = document.getElementById('btn-send-otp');
    const otpGroup = document.getElementById('otp-group');
    const otpHiddenInput = document.getElementById('reg-otp');

    if (!email) {
        showToast('Harap masukkan alamat email terlebih dahulu.', 'error');
        return;
    }

    setBtnLoading(btnSendOtp, true, 'Kirim OTP');

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
            otpHiddenInput.required = true;
            startCooldown(btnSendOtp, 60);
        } else {
            showToast(parseErrorMessage(data), 'error');
            setBtnLoading(btnSendOtp, false, 'Kirim OTP');
        }
    } catch (error) {
        showToast('Terjadi kesalahan koneksi server.', 'error');
        setBtnLoading(btnSendOtp, false, 'Kirim OTP');
    }
}

function startCooldown(button, seconds) {
    let timeLeft = seconds;
    button.disabled = true;
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    if (spinner) spinner.classList.add('hidden');

    const timer = setInterval(() => {
        if (btnText) btnText.textContent = `${timeLeft}s`;
        timeLeft--;

        if (timeLeft < 0) {
            clearInterval(timer);
            button.disabled = false;
            if (btnText) btnText.textContent = 'Kirim Ulang';
        }
    }, 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    setupOtpBoxes();

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const formData = new FormData(loginForm);
        const payload = {};
        
        formData.forEach((value, key) => {
            const trimmed = value.trim();
            if (trimmed !== '') {
                payload[key] = trimmed;
            }
        });

        setBtnLoading(submitBtn, true, 'Masuk ke Dashboard');

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
                setBtnLoading(submitBtn, false, 'Masuk ke Dashboard');
            }
        } catch (error) {
            showToast('Terjadi kesalahan koneksi server.', 'error');
            setBtnLoading(submitBtn, false, 'Masuk ke Dashboard');
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const passwordInput = document.getElementById('reg-password').value;

        if (!validatePasswordCombination(passwordInput)) {
            showToast('Password harus minimal 8 karakter dan kombinasi huruf besar, huruf kecil, serta angka.', 'error');
            return;
        }

        if (currentRegMethod === 'email') {
            const otpCode = document.getElementById('reg-otp').value;
            if (otpCode.length !== 6) {
                showToast('Kode OTP harus terdiri dari 6 digit angka.', 'error');
                return;
            }
        }

        const formData = new FormData(registerForm);
        const payload = {};
        formData.forEach((value, key) => {
            const trimmed = value.trim();
            if (trimmed !== '') {
                payload[key] = trimmed;
            }
        });

        setBtnLoading(submitBtn, true, 'Daftar Sekarang');

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
                resetRegisterFormState();
                setTimeout(() => {
                    showForm('login');
                    setBtnLoading(submitBtn, false, 'Daftar Sekarang');
                }, 1500);
            } else {
                showToast(parseErrorMessage(data), 'error');
                setBtnLoading(submitBtn, false, 'Daftar Sekarang');
            }
        } catch (error) {
            showToast('Terjadi kesalahan koneksi server.', 'error');
            setBtnLoading(submitBtn, false, 'Daftar Sekarang');
        }
    });
});

function openAuthModal() {
    const authContainer = document.getElementById('auth-container');
    const overlay = document.getElementById('mobile-overlay');
    
    if (authContainer) authContainer.classList.add('active');
    if (overlay) overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
    const authContainer = document.getElementById('auth-container');
    const overlay = document.getElementById('mobile-overlay');
    
    if (authContainer) authContainer.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}
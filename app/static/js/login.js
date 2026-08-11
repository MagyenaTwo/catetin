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
    }
}
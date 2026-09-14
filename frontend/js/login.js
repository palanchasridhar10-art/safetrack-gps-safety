const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const errorBox = document.getElementById("errorBox");

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError(errorBox);
  loginBtn.disabled = true;
  loginBtn.textContent = "Logging in…";

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    const res = await Api.login({ email, password });
    Storage.setOtpSession(res.otp_session_token);
    if (res.dev_otp_preview) {
      // Dev-mode convenience only: shown when no SMTP server is configured.
      sessionStorage.setItem("safetrack_dev_otp_preview", res.dev_otp_preview);
    }
    window.location.href = "otp.html";
  } catch (err) {
    showError(errorBox, err.message);
    loginBtn.disabled = false;
    loginBtn.textContent = "Login";
  }
});

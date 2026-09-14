const otpForm = document.getElementById("otpForm");
const verifyBtn = document.getElementById("verifyBtn");
const errorBox = document.getElementById("errorBox");
const resendBtn = document.getElementById("resendBtn");
const devHint = document.getElementById("devHint");

// Guard: must have come from a login step.
if (!Storage.getOtpSession()) {
  window.location.href = "index.html";
}

// Dev-mode convenience: if no SMTP server is configured backend-side, the
// login response includes a preview OTP so the flow is testable locally.
const devOtp = sessionStorage.getItem("safetrack_dev_otp_preview");
if (devOtp) {
  devHint.style.display = "block";
  devHint.textContent = `Dev mode (no SMTP configured): your OTP is ${devOtp}`;
}

otpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError(errorBox);
  verifyBtn.disabled = true;
  verifyBtn.textContent = "Verifying…";

  const otp = document.getElementById("otp").value.trim();

  try {
    const res = await Api.verifyOtp({
      otp_session_token: Storage.getOtpSession(),
      otp,
    });
    Storage.setToken(res.access_token);
    Storage.setUser(res.user);
    Storage.clearOtpSession();
    sessionStorage.removeItem("safetrack_dev_otp_preview");

    // Route based on whether the user already has two trusted contacts.
    try {
      const contacts = await Api.listContacts();
      window.location.href = contacts.length >= 2 ? "dashboard.html" : "contacts.html";
    } catch (_) {
      window.location.href = "contacts.html";
    }
  } catch (err) {
    showError(errorBox, err.message);
    verifyBtn.disabled = false;
    verifyBtn.textContent = "Verify OTP";
  }
});

resendBtn.addEventListener("click", () => {
  Storage.clearOtpSession();
  window.location.href = "index.html";
});

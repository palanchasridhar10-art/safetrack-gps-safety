const registerForm = document.getElementById("registerForm");
const registerBtn = document.getElementById("registerBtn");
const errorBox = document.getElementById("errorBox");
const successBox = document.getElementById("successBox");

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError(errorBox);
  registerBtn.disabled = true;
  registerBtn.textContent = "Creating account…";

  const payload = {
    name: document.getElementById("name").value.trim(),
    email: document.getElementById("email").value.trim(),
    phone: document.getElementById("phone").value.trim() || null,
    password: document.getElementById("password").value,
  };

  try {
    await Api.register(payload);
    showSuccess(successBox, "Account created! Redirecting to login…");
    setTimeout(() => (window.location.href = "index.html"), 1200);
  } catch (err) {
    showError(errorBox, err.message);
    registerBtn.disabled = false;
    registerBtn.textContent = "Create account";
  }
});

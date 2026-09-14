requireAuth();

const existingList = document.getElementById("existingList");
const contactForm = document.getElementById("contactForm");
const addFormBlock = document.getElementById("addFormBlock");
const addBtn = document.getElementById("addBtn");
const errorBox = document.getElementById("errorBox");
const successBox = document.getElementById("successBox");
const continueBtn = document.getElementById("continueBtn");

const confirmModal = document.getElementById("confirmModal");
const confirmText = document.getElementById("confirmText");
const cancelConfirm = document.getElementById("cancelConfirm");
const acceptConfirm = document.getElementById("acceptConfirm");

let pendingPayload = null;
let contactsCache = [];

async function loadContacts() {
  hideError(errorBox);
  try {
    contactsCache = await Api.listContacts();
    renderContacts();
  } catch (err) {
    showError(errorBox, err.message);
  }
}

function renderContacts() {
  existingList.innerHTML = "";
  contactsCache.forEach((c) => {
    const row = document.createElement("div");
    row.className = "existing";
    row.innerHTML = `
      <span>👤 <strong>${escapeHtml(c.name)}</strong> — ${escapeHtml(c.phone)}${c.relationship_label ? ` (${escapeHtml(c.relationship_label)})` : ""}</span>
      <button class="small-btn" data-id="${c.id}">Remove</button>
    `;
    row.querySelector("button").addEventListener("click", () => deleteContact(c.id));
    existingList.appendChild(row);
  });

  const atLimit = contactsCache.length >= 2;
  addFormBlock.style.display = atLimit ? "none" : "block";
  continueBtn.style.display = atLimit ? "block" : "none";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function deleteContact(id) {
  hideError(errorBox);
  try {
    await Api.deleteContact(id);
    await loadContacts();
  } catch (err) {
    showError(errorBox, err.message);
  }
}

contactForm.addEventListener("submit", (e) => {
  e.preventDefault();
  hideError(errorBox);

  pendingPayload = {
    name: document.getElementById("cName").value.trim(),
    phone: document.getElementById("cPhone").value.trim(),
    relationship_label: document.getElementById("cRelationship").value.trim() || null,
    email: document.getElementById("cEmail").value.trim() || null,
  };

  confirmText.textContent = `Save ${pendingPayload.name} (${pendingPayload.phone}) as a trusted contact? They will receive your safety location alerts.`;
  confirmModal.classList.add("show");
});

cancelConfirm.addEventListener("click", () => {
  pendingPayload = null;
  confirmModal.classList.remove("show");
});

acceptConfirm.addEventListener("click", async () => {
  if (!pendingPayload) return;
  addBtn.disabled = true;
  confirmModal.classList.remove("show");

  try {
    await Api.addContact(pendingPayload);
    contactForm.reset();
    showSuccess(successBox, "Contact saved.");
    setTimeout(() => successBox.classList.remove("show"), 2500);
    await loadContacts();
  } catch (err) {
    showError(errorBox, err.message);
  } finally {
    addBtn.disabled = false;
    pendingPayload = null;
  }
});

continueBtn.addEventListener("click", () => {
  window.location.href = "dashboard.html";
});

loadContacts();

requireAuth();

const userNameEl = document.getElementById("userName");
const gpsStatusEl = document.getElementById("gpsStatus");
const trackingStatusEl = document.getElementById("trackingStatus");
const contactsListEl = document.getElementById("contactsList");
const errorBox = document.getElementById("errorBox");
const successBox = document.getElementById("successBox");
const lastCoords = document.getElementById("lastCoords");
const lastUpdated = document.getElementById("lastUpdated");
const waLinks = document.getElementById("waLinks");

const sosBtn = document.getElementById("sosBtn");
const sosModal = document.getElementById("sosModal");
const cancelSos = document.getElementById("cancelSos");
const confirmSos = document.getElementById("confirmSos");

const sendLocationBtn = document.getElementById("sendLocationBtn");
const trackingBtn = document.getElementById("trackingBtn");

const consentModal = document.getElementById("consentModal");
const consentTitle = document.getElementById("consentTitle");
const consentText = document.getElementById("consentText");
const cancelConsent = document.getElementById("cancelConsent");
const acceptConsent = document.getElementById("acceptConsent");

const logoutBtn = document.getElementById("logoutBtn");

let hasTwoContacts = false;
let isTracking = false;
let trackingWatchId = null;
let trackingIntervalId = null;
let pendingConsentAction = null; // "send" | "start_tracking"

// ---------- init ----------

async function init() {
  const user = Storage.getUser();
  userNameEl.textContent = user ? user.name : "there";

  await loadContacts();
  await checkGpsPermission();
  await refreshTrackingStatus();
  await loadLastLocation();
}

async function loadContacts() {
  try {
    const contacts = await Api.listContacts();
    hasTwoContacts = contacts.length >= 2;
    if (contacts.length === 0) {
      contactsListEl.innerHTML = `<span style="color:var(--muted)">No contacts yet — <a href="contacts.html" style="color:var(--primary)">add two now</a></span>`;
    } else {
      contactsListEl.innerHTML = contacts
        .map((c) => `<div class="contact-chip">👩 ${escapeHtml(c.name)} <span style="color:var(--muted)">(${escapeHtml(c.relationship_label || "Contact")})</span></div>`)
        .join("");
      if (!hasTwoContacts) {
        contactsListEl.innerHTML += `<div style="margin-top:8px;"><a href="contacts.html" style="color:var(--primary); font-size:13px;">Add one more contact</a></div>`;
      }
    }
    sendLocationBtn.disabled = !hasTwoContacts;
    trackingBtn.disabled = !hasTwoContacts;
    sosBtn.disabled = !hasTwoContacts;
  } catch (err) {
    showError(errorBox, err.message);
  }
}

async function checkGpsPermission() {
  if (!("geolocation" in navigator)) {
    gpsStatusEl.innerHTML = `<span class="status-dot dot-red"></span>Not supported`;
    return;
  }
  if ("permissions" in navigator) {
    try {
      const status = await navigator.permissions.query({ name: "geolocation" });
      renderGpsStatus(status.state);
      status.onchange = () => renderGpsStatus(status.state);
      return;
    } catch (_) {
      /* fall through */
    }
  }
  gpsStatusEl.innerHTML = `<span class="status-dot dot-amber"></span>Unknown`;
}

function renderGpsStatus(state) {
  if (state === "granted") {
    gpsStatusEl.innerHTML = `<span class="status-dot dot-green"></span>Available`;
  } else if (state === "denied") {
    gpsStatusEl.innerHTML = `<span class="status-dot dot-red"></span>Blocked`;
  } else {
    gpsStatusEl.innerHTML = `<span class="status-dot dot-amber"></span>Not yet granted`;
  }
}

async function refreshTrackingStatus() {
  try {
    const session = await Api.trackingStatus();
    if (session && session.status === "active") {
      setTrackingUI(true);
    } else {
      setTrackingUI(false);
    }
  } catch (_) {
    setTrackingUI(false);
  }
}

async function loadLastLocation() {
  try {
    const loc = await Api.latestLocation();
    lastCoords.textContent = `${loc.latitude.toFixed(5)}, ${loc.longitude.toFixed(5)}`;
    lastUpdated.textContent = `Last updated: ${new Date(loc.timestamp).toLocaleString()}`;
  } catch (_) {
    lastCoords.textContent = "No location shared yet";
    lastUpdated.textContent = "";
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- consent modal (Mode A / Mode B) ----------

function openConsent(action) {
  pendingConsentAction = action;
  if (action === "send") {
    consentTitle.textContent = "📍 Location Sharing";
    consentText.textContent = "Your location will be shared with your selected trusted contacts only when you activate location sharing.";
  } else {
    consentTitle.textContent = "🛡️ Safety Tracking";
    consentText.textContent = "Your location will be periodically shared with your selected trusted contacts while tracking is active. You can stop at any time.";
  }
  consentModal.classList.add("show");
}

cancelConsent.addEventListener("click", () => {
  pendingConsentAction = null;
  consentModal.classList.remove("show");
});

acceptConsent.addEventListener("click", async () => {
  consentModal.classList.remove("show");
  if (pendingConsentAction === "send") {
    await sendCurrentLocationFlow();
  } else if (pendingConsentAction === "start_tracking") {
    await startTrackingFlow();
  }
  pendingConsentAction = null;
});

// ---------- Mode A: send current location ----------

sendLocationBtn.addEventListener("click", () => openConsent("send"));

async function sendCurrentLocationFlow() {
  hideError(errorBox);
  sendLocationBtn.disabled = true;
  sendLocationBtn.textContent = "Getting location…";

  try {
    const pos = await getCurrentPosition();
    const res = await Api.sendCurrentLocation(pos);
    renderShareResult(res);
    showSuccess(successBox, "Location sent to your trusted contacts.");
    setTimeout(() => successBox.classList.remove("show"), 3000);
  } catch (err) {
    showError(errorBox, err.message);
  } finally {
    sendLocationBtn.disabled = false;
    sendLocationBtn.innerHTML = `<span class="icon">📍</span> Send current location`;
  }
}

function renderShareResult(res) {
  lastCoords.textContent = `${res.location.latitude.toFixed(5)}, ${res.location.longitude.toFixed(5)}`;
  lastUpdated.textContent = `Last updated: ${new Date(res.location.timestamp).toLocaleString()}`;

  waLinks.innerHTML = "";
  if (res.delivery_mode === "cloud_api") {
    waLinks.innerHTML = `<div style="color:var(--success); font-size:13px;">✅ Sent via WhatsApp Business API</div>`;
  } else if (res.delivery_mode === "click_to_chat" && res.whatsapp_links.length) {
    res.whatsapp_links.forEach((link, i) => {
      const a = document.createElement("a");
      a.href = link;
      a.target = "_blank";
      a.rel = "noopener";
      a.className = "wa-link";
      a.textContent = `📲 Send WhatsApp alert to contact ${i + 1}`;
      waLinks.appendChild(a);
    });
  }
}

// ---------- Mode B: safety tracking ----------

trackingBtn.addEventListener("click", () => {
  if (isTracking) {
    stopTrackingFlow();
  } else {
    openConsent("start_tracking");
  }
});

async function startTrackingFlow() {
  hideError(errorBox);
  try {
    await Api.startTracking();
    setTrackingUI(true);

    trackingWatchId = watchPosition(
      async (pos) => {
        try {
          await Api.updateTrackingLocation(pos);
          lastCoords.textContent = `${pos.latitude.toFixed(5)}, ${pos.longitude.toFixed(5)}`;
          lastUpdated.textContent = `Last updated: ${new Date().toLocaleString()}`;
        } catch (_) {
          /* silent — next update will retry */
        }
      },
      (err) => {
        showError(errorBox, err.message || "Lost GPS signal during tracking.");
      }
    );
  } catch (err) {
    showError(errorBox, err.message);
  }
}

async function stopTrackingFlow() {
  hideError(errorBox);
  try {
    await Api.stopTracking();
    setTrackingUI(false);
    stopWatching(trackingWatchId);
    trackingWatchId = null;
  } catch (err) {
    showError(errorBox, err.message);
  }
}

function setTrackingUI(active) {
  isTracking = active;
  if (active) {
    trackingStatusEl.innerHTML = `<span class="status-dot dot-green"></span>Active`;
    trackingBtn.innerHTML = `<span class="icon">🛑</span> Stop tracking`;
    trackingBtn.classList.add("stop");
  } else {
    trackingStatusEl.innerHTML = `<span class="status-dot dot-red"></span>Inactive`;
    trackingBtn.innerHTML = `<span class="icon">🛡️</span> Start safety tracking`;
    trackingBtn.classList.remove("stop");
  }
}

// ---------- SOS ----------

sosBtn.addEventListener("click", () => {
  sosModal.classList.add("show");
});

cancelSos.addEventListener("click", () => {
  sosModal.classList.remove("show");
});

confirmSos.addEventListener("click", async () => {
  sosModal.classList.remove("show");
  hideError(errorBox);
  confirmSos.disabled = true;

  try {
    const pos = await getCurrentPosition();
    const res = await Api.triggerSOS(pos);
    renderShareResult(res);
    showSuccess(successBox, "🚨 SOS sent to your trusted contacts.");
  } catch (err) {
    // Still try to trigger SOS even if GPS fails, so the event is recorded
    // and contacts can be told to check in manually.
    try {
      const res = await Api.triggerSOS({});
      showError(errorBox, `${err.message} An SOS event was still recorded — please contact your trusted people directly if possible.`);
    } catch (err2) {
      showError(errorBox, err.message);
    }
  } finally {
    confirmSos.disabled = false;
  }
});

// ---------- logout ----------

logoutBtn.addEventListener("click", async () => {
  stopWatching(trackingWatchId);
  try {
    await Api.logout();
  } catch (_) {
    /* ignore */
  }
  Storage.clearAll();
  window.location.href = "index.html";
});

init();

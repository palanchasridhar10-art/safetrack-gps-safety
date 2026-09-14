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

const waStatusPill = document.getElementById("waStatusPill");
const waToggleHeader = document.getElementById("waToggleHeader");
const waDetailsPanel = document.getElementById("waDetailsPanel");
const waModeBadge = document.getElementById("waModeBadge");
const waModeExplanation = document.getElementById("waModeExplanation");
const waTestPhone = document.getElementById("waTestPhone");
const waTestBtn = document.getElementById("waTestBtn");
const waTestResult = document.getElementById("waTestResult");
const waWebhookUrl = document.getElementById("waWebhookUrl");
const waVerifyToken = document.getElementById("waVerifyToken");

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
  await refreshWhatsAppStatus();
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

// ---------- WhatsApp API Gateway ----------

async function refreshWhatsAppStatus() {
  try {
    const status = await Api.getWhatsAppStatus();
    if (status.mode === "cloud_api") {
      waStatusPill.innerHTML = `<span class="status-dot dot-green"></span>Cloud API`;
      waModeBadge.textContent = "Cloud API Active";
      waModeBadge.style.color = "var(--success)";
      waModeBadge.style.background = "rgba(52,211,153,0.15)";
      waModeExplanation.innerHTML = `Meta WhatsApp Cloud API is connected (Phone ID: <code>${escapeHtml(status.phone_number_id || "Active")}</code>). Alerts send automatically in the background.`;
    } else {
      waStatusPill.innerHTML = `<span class="status-dot dot-amber"></span>Click-to-Chat`;
      waModeBadge.textContent = "Click-to-Chat";
      waModeBadge.style.color = "var(--warn)";
      waModeBadge.style.background = "rgba(251,191,36,0.15)";
      waModeExplanation.textContent = "Running in consent-first Click-to-Chat mode (wa.me). Alerts open pre-filled in WhatsApp so you can send them with one tap.";
    }

    if (waWebhookUrl) {
      const fullWebhook = window.location.origin + status.webhook_endpoint;
      waWebhookUrl.textContent = fullWebhook;
    }
    if (waVerifyToken) {
      waVerifyToken.textContent = status.webhook_verify_token;
    }
  } catch (_) {
    waStatusPill.innerHTML = `<span class="status-dot dot-amber"></span>wa.me Mode`;
    waModeBadge.textContent = "wa.me Mode";
    waModeExplanation.textContent = "Click-to-chat fallback active.";
  }
}

if (waToggleHeader) {
  waToggleHeader.addEventListener("click", () => {
    const isHidden = waDetailsPanel.style.display === "none";
    waDetailsPanel.style.display = isHidden ? "block" : "none";
  });
}

if (waTestBtn) {
  waTestBtn.addEventListener("click", async () => {
    const phone = waTestPhone.value.trim();
    if (!phone) {
      waTestResult.style.display = "block";
      waTestResult.style.background = "rgba(255,77,94,0.15)";
      waTestResult.style.color = "var(--danger)";
      waTestResult.textContent = "Please enter a recipient phone number with country code (e.g. +1234567890).";
      return;
    }

    waTestBtn.disabled = true;
    waTestBtn.textContent = "Sending…";
    waTestResult.style.display = "none";

    try {
      const res = await Api.testWhatsApp({ phone_number: phone });
      waTestResult.style.display = "block";
      if (res.link) {
        waTestResult.style.background = "rgba(251,191,36,0.15)";
        waTestResult.style.color = "var(--warn)";
        waTestResult.innerHTML = `Test alert ready: <a href="${escapeHtml(res.link)}" target="_blank" rel="noopener" style="color:var(--primary); font-weight:600; text-decoration:underline;">Tap here to open test message in WhatsApp</a>`;
      } else {
        waTestResult.style.background = "rgba(52,211,153,0.15)";
        waTestResult.style.color = "var(--success)";
        waTestResult.textContent = res.message || "Test alert delivered successfully!";
      }
    } catch (err) {
      waTestResult.style.display = "block";
      waTestResult.style.background = "rgba(255,77,94,0.15)";
      waTestResult.style.color = "var(--danger)";
      waTestResult.textContent = err.message || "Failed to transmit WhatsApp test alert.";
    } finally {
      waTestBtn.disabled = false;
      waTestBtn.textContent = "Send Test Alert";
    }
  });
}

init();

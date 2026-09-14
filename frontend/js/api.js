/**
 * SafeTrack frontend API client.
 *
 * Talks to the FastAPI backend. Update API_BASE_URL to point at your
 * deployed backend (e.g. https://api.yourdomain.com) in production.
 */
const API_BASE_URL =
  window.SAFETRACK_API_BASE_URL ||
  ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.port === "5500"
    ? "http://127.0.0.1:8000"
    : "");

const TOKEN_KEY = "safetrack_access_token";
const OTP_SESSION_KEY = "safetrack_otp_session_token";
const USER_KEY = "safetrack_user";

const Storage = {
  getToken: () => sessionStorage.getItem(TOKEN_KEY),
  setToken: (t) => sessionStorage.setItem(TOKEN_KEY, t),
  clearToken: () => sessionStorage.removeItem(TOKEN_KEY),

  getOtpSession: () => sessionStorage.getItem(OTP_SESSION_KEY),
  setOtpSession: (t) => sessionStorage.setItem(OTP_SESSION_KEY, t),
  clearOtpSession: () => sessionStorage.removeItem(OTP_SESSION_KEY),

  getUser: () => JSON.parse(sessionStorage.getItem(USER_KEY) || "null"),
  setUser: (u) => sessionStorage.setItem(USER_KEY, JSON.stringify(u)),

  clearAll: () => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(OTP_SESSION_KEY);
    sessionStorage.removeItem(USER_KEY);
  },
};

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Storage.getToken();
    if (!token) throw new ApiError("Not authenticated", 401);
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      "Could not reach the SafeTrack server. Please check your connection.",
      0
    );
  }

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    /* no JSON body, e.g. 204 */
  }

  if (!response.ok) {
    if (response.status === 401) {
      Storage.clearAll();
    }
    const detail =
      (data && (data.detail || data.message)) ||
      `Request failed (${response.status})`;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg || JSON.stringify(d)).join(" ")
      : detail;
    throw new ApiError(message, response.status);
  }

  return data;
}

const Api = {
  register: (payload) => apiRequest("/api/auth/register", { method: "POST", body: payload }),
  login: (payload) => apiRequest("/api/auth/login", { method: "POST", body: payload }),
  verifyOtp: (payload) => apiRequest("/api/auth/verify-otp", { method: "POST", body: payload }),
  logout: () => apiRequest("/api/auth/logout", { method: "POST", auth: true }),
  me: () => apiRequest("/api/auth/me", { auth: true }),

  listContacts: () => apiRequest("/api/contacts", { auth: true }),
  addContact: (payload) => apiRequest("/api/contacts", { method: "POST", body: payload, auth: true }),
  updateContact: (id, payload) => apiRequest(`/api/contacts/${id}`, { method: "PUT", body: payload, auth: true }),
  deleteContact: (id) => apiRequest(`/api/contacts/${id}`, { method: "DELETE", auth: true }),

  sendCurrentLocation: (payload) => apiRequest("/api/location/current", { method: "POST", body: payload, auth: true }),
  latestLocation: () => apiRequest("/api/location/latest", { auth: true }),

  startTracking: () => apiRequest("/api/safety/start", { method: "POST", auth: true }),
  updateTrackingLocation: (payload) => apiRequest("/api/safety/update-location", { method: "POST", body: payload, auth: true }),
  stopTracking: () => apiRequest("/api/safety/stop", { method: "POST", auth: true }),
  trackingStatus: () => apiRequest("/api/safety/status", { auth: true }),

  triggerSOS: (payload) => apiRequest("/api/emergency/sos", { method: "POST", body: payload, auth: true }),
  emergencyHistory: () => apiRequest("/api/emergency/history", { auth: true }),
};

function requireAuth() {
  if (!Storage.getToken()) {
    window.location.href = "index.html";
  }
}

function showError(el, message) {
  el.textContent = message;
  el.classList.add("show");
}

function hideError(el) {
  el.classList.remove("show");
  el.textContent = "";
}

function showSuccess(el, message) {
  el.textContent = message;
  el.classList.add("show");
}

import { supabase } from "./supabase";

const API_URL = import.meta.env.VITE_API_URL;

// The bucket the backend hands out upload slots for.
export const PROOFS_BUCKET = "payment-proofs";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// The API speaks snake_case; the UI uses camelCase. Only keys are converted.
function camelize(value) {
  if (Array.isArray(value)) return value.map(camelize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase()), camelize(item)]),
    );
  }
  return value;
}

function messageFor(status, payload) {
  // Expected errors carry a readable `detail` string. Validation errors carry a list.
  if (typeof payload?.detail === "string") return payload.detail;
  if (status === 401) return "Your session has expired. Sign in again.";
  if (status === 403) return "You do not have access to this.";
  if (status === 422) return "Check the form and try again.";
  return "Something went wrong. Try again in a moment.";
}

async function request(method, path, body) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
        ...(body && { "Content-Type": "application/json" }),
      },
      body: body && JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Try again in a moment.");
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, messageFor(response.status, payload));
  return camelize(payload);
}

const get = (path) => request("GET", path);
const post = (path, body = {}) => request("POST", path, body);

// --- The signed-in user ---

export const getMe = () => get("/api/me");
export const getMyOrders = () => get("/api/me/orders");
export const getMyPromo = () => get("/api/me/promo");

// --- Orders ---

// Step 1 returns the order id, the price and one upload slot per screenshot.
export const createOrder = (order) =>
  post("/api/orders", {
    product: order.product,
    period: order.period,
    method: order.method,
    coin: order.coin,
    screenshots: order.files.map((file) => ({ content_type: file.type, size_bytes: file.size })),
  });

// Step 2, after the files are uploaded.
export const submitOrder = (id, { paths, proofText, note }) =>
  post(`/api/orders/${id}/submit`, { paths, proof_text: proofText, note });

// Uploads straight into the private bucket with the one-time token from createOrder.
export async function uploadProof(slot, file) {
  const { error } = await supabase.storage.from(PROOFS_BUCKET).uploadToSignedUrl(slot.path, slot.token, file);
  if (error) throw new ApiError(0, "Could not upload a screenshot. Try again.");
}

// --- Promo ---

export const createPromoClaim = ({ platform, url, rewardProduct }) =>
  post("/api/promo/claims", { platform, url, reward_product: rewardProduct });

// --- Admin ---

export const listAdminOrders = (status) => get(`/api/admin/orders?status=${status}`);
export const approveOrder = (id, receivedCents) => post(`/api/admin/orders/${id}/approve`, { received_cents: receivedCents });
export const rejectOrder = (id, reason) => post(`/api/admin/orders/${id}/reject`, { reason });

export const listAdminClaims = (status) => get(`/api/admin/promo-claims?status=${status}`);
export const approveClaim = (id, views) => post(`/api/admin/promo-claims/${id}/approve`, { views });
export const rejectClaim = (id, reason) => post(`/api/admin/promo-claims/${id}/reject`, { reason });

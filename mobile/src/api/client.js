import { API_BASE_URL } from "../config";

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const REQUEST_TIMEOUT_MS = 15_000;

function normalizeDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg)
      .filter(Boolean)
      .join(" ");
  }
  return "Request failed";
}

function withQuery(path, params = {}) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  return query ? `${path}?${query}` : path;
}

async function request(path, options = {}) {
  const controller = typeof AbortController === "undefined" ? null : new AbortController();
  const timeout = controller
    ? setTimeout(() => controller.abort(), options.timeout || REQUEST_TIMEOUT_MS)
    : null;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method || "GET",
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
        ...options.headers,
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller?.signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new ApiError("Request timed out", 408);
    }
    throw error;
  } finally {
    if (timeout) clearTimeout(timeout);
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const detail = payload?.detail;
    throw new ApiError(normalizeDetail(detail), response.status, detail);
  }

  return payload;
}

export const api = {
  login: (body) => request("/auth/login", { method: "POST", body }),
  register: (body) => request("/auth/register", { method: "POST", body }),
  acceptInvitation: (body) =>
    request("/auth/invitations/accept", { method: "POST", body }),
  requestPasswordReset: (body) =>
    request("/auth/password-reset/request", { method: "POST", body }),
  confirmPasswordReset: (body) =>
    request("/auth/password-reset/confirm", { method: "POST", body }),
  verifyEmail: (body) =>
    request("/auth/email/verify", { method: "POST", body }),
  resendEmailVerification: (email) =>
    request("/auth/email/verify/resend", {
      method: "POST",
      body: { email },
    }),
  changePassword: (token, body) =>
    request("/auth/password/change", { method: "POST", body, token }),
  updateProfile: (token, body) =>
    request("/auth/me", { method: "PATCH", body, token }),
  deleteAccount: (token) => request("/auth/me", { method: "DELETE", token }),
  refresh: (refreshToken) =>
    request("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    }),
  logout: (refreshToken, token) =>
    request("/auth/logout", {
      method: "POST",
      body: { refresh_token: refreshToken },
      token,
    }),
  getMe: (token) => request("/auth/me", { token }),
  getPersonalDashboardSummary: (token) =>
    request("/dashboard/summary", { token }),
  createInvitation: (token, body) =>
    request("/auth/invitations", { method: "POST", body, token }),
  listAdminUsers: (token, params) =>
    request(withQuery("/admin/users", params), { token }),
  getAdminUser: (token, userId) => request(`/admin/users/${userId}`, { token }),
  updateAdminUserStatus: (token, userId, body) =>
    request(`/auth/admin/users/${userId}/status`, {
      method: "PATCH",
      body,
      token,
    }),
  updateAdminUserRole: (token, userId, body) =>
    request(`/auth/admin/users/${userId}/role`, {
      method: "PATCH",
      body,
      token,
    }),
  getAdminUserPermissions: (token, userId) =>
    request(`/admin/users/${userId}/permissions`, { token }),
  listAdminInvitations: (token, params) =>
    request(withQuery("/admin/invitations", params), { token }),
  getAdminInvitation: (token, invitationId) =>
    request(`/admin/invitations/${invitationId}`, { token }),
  revokeAdminInvitation: (token, invitationId) =>
    request(`/admin/invitations/${invitationId}/revoke`, {
      method: "POST",
      token,
    }),
  deleteAdminInvitation: (token, invitationId) =>
    request(`/admin/invitations/${invitationId}`, {
      method: "DELETE",
      token,
    }),
  getAdminDashboardSummary: (token) =>
    request("/admin/dashboard/summary", { token }),
  listAdminAuditEvents: (token, params) =>
    request(withQuery("/admin/audit-events", params), { token }),
  listAdminPermissions: (token) => request("/admin/permissions", { token }),
  listAdminRoles: (token) => request("/admin/roles", { token }),
  getAdminRole: (token, role) => request(`/admin/roles/${role}`, { token }),
  createVaccineContent: (token, body) =>
    request("/admin/vaccine-content", { method: "POST", body, token }),
  listVaccineContent: (token, params) =>
    request(withQuery("/vaccine-content", params), { token }),
  getVaccineContent: (token, contentId) =>
    request(`/vaccine-content/${contentId}`, { token }),
  createQuestion: (token, body) =>
    request("/questions", { method: "POST", body, token }),
  listQuestions: (token) => request("/questions", { token }),
  getQuestion: (token, questionId) =>
    request(`/questions/${questionId}`, { token }),
  requestQuestionAnalysis: (token, questionId) =>
    request(`/questions/${questionId}/analysis`, {
      method: "POST",
      token,
    }),
  listQuestionReviewQueue: (token) =>
    request("/review/questions", { token }),
  getQuestionForReview: (token, questionId) =>
    request(`/review/questions/${questionId}`, { token }),
  publishProfessionalResponse: (token, questionId, body) =>
    request(`/review/questions/${questionId}/response`, {
      method: "POST",
      body,
      token,
    }),
  listNarratives: (token, params) =>
    request(withQuery("/narratives", params), { token }),
  getNarrative: (token, narrativeId) =>
    request(`/narratives/${narrativeId}`, { token }),
  getNarrativeHistory: (token, narrativeId, params) =>
    request(withQuery(`/narratives/${narrativeId}/history`, params), { token }),
  createNarrative: (token, body) =>
    request("/narratives", { method: "POST", body, token }),
  updateNarrative: (token, narrativeId, body) =>
    request(`/narratives/${narrativeId}`, { method: "PATCH", body, token }),
  listAssignments: (token, params) =>
    request(withQuery("/reviews/assignments", params), { token }),
  getAssignment: (token, assignmentId) =>
    request(`/reviews/assignments/${assignmentId}`, { token }),
  getAssignmentStatus: (token, assignmentId) =>
    request(`/reviews/assignments/${assignmentId}/status`, { token }),
  updateAssignmentStatus: (token, assignmentId, body) =>
    request(`/reviews/assignments/${assignmentId}/status`, {
      method: "POST",
      body,
      token,
    }),
  submitReview: (token, assignmentId, body) =>
    request(`/reviews/assignments/${assignmentId}/review`, {
      method: "POST",
      body,
      token,
    }),
  getReviewHistory: (token, assignmentId, params) =>
    request(withQuery(`/reviews/assignments/${assignmentId}/history`, params), { token }),
};

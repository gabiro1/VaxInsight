const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

export const API_BASE_URL = (
  configuredApiUrl || "http://10.0.2.2:8000/api/v1"
).replace(/\/+$/, "");

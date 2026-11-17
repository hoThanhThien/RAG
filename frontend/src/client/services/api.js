// File: frontend/src/client/services/api.js
import axios from "axios";

const TOKEN_STORAGE_KEYS = [
  "token",
  "access_token",
  "accessToken",
  "refresh_token",
  "refreshToken",
  "jwt",
];

const AUTH_SKIP_REFRESH_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/logout",
  "/auth/me",
];

// Dọn sạch mọi JWT từng lưu ở localStorage/sessionStorage (chỉ dùng HttpOnly Cookie)
export const clearClientStoredTokens = () => {
  if (typeof window === "undefined") return;
  try {
    TOKEN_STORAGE_KEYS.forEach((key) => {
      window.localStorage?.removeItem(key);
      window.sessionStorage?.removeItem(key);
    });
  } catch {
    // Bỏ qua nếu trình duyệt chặn storage
  }
};

clearClientStoredTokens();

// Tự động đồng bộ host giữa 127.0.0.1 và localhost theo URL của trình duyệt
export const getBaseApiUrl = () => {
  if (typeof window !== "undefined") {
    const { hostname, protocol } = window.location;
    if (hostname === "127.0.0.1" || hostname === "localhost") {
      return `${protocol}//${hostname}:8000`;
    }
  }
  return import.meta.env.VITE_API_URL || "http://localhost:8000";
};

export const api = axios.create({
  baseURL: getBaseApiUrl(),
  timeout: 10000,
  withCredentials: true, // Tự động gửi và nhận HttpOnly Cookie
});

export const toAbsoluteUrl = (url) => {
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url;
  const root = api.defaults.baseURL?.replace(/\/+$/, "") || "";
  const path = url.startsWith("/") ? url : `/${url}`;
  return `${root}${path}`;
};

// Request interceptor: đồng bộ baseURL và xóa header Authorization nếu có
api.interceptors.request.use((config) => {
  if (!config.baseURL || config.baseURL.includes("localhost") || config.baseURL.includes("127.0.0.1")) {
    config.baseURL = getBaseApiUrl();
  }
  if (config.headers?.Authorization) {
    delete config.headers.Authorization;
  }
  return config;
});

let refreshPromise = null;

// Response interceptor: tự động gọi /auth/refresh (dùng refresh_token HttpOnly Cookie) khi gặp 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config;
    const statusCode = error?.response?.status;
    const requestUrl = String(originalRequest?.url || "");
    const shouldSkipRefresh = AUTH_SKIP_REFRESH_PATHS.some((path) => requestUrl.includes(path));

    if (statusCode === 401 && originalRequest && !originalRequest._retry && !shouldSkipRefresh) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = api.post("/auth/refresh").finally(() => {
            refreshPromise = null;
          });
        }
        await refreshPromise;
        return api(originalRequest);
      } catch (refreshError) {
        clearClientStoredTokens();
        return Promise.reject(refreshError);
      }
    }

    if (statusCode === 401) {
      clearClientStoredTokens();
    }
    return Promise.reject(error);
  }
);

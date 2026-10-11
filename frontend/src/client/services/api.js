// File: frontend/src/client/services/api.js
import axios from "axios";

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

// Quản lý token tạm thời trong RAM (In-Memory) - Không lưu xuống localStorage/sessionStorage
let inMemoryToken = null;

export const setAuthToken = (token) => {
  inMemoryToken = token || null;
  if (inMemoryToken) {
    api.defaults.headers.common["Authorization"] = `Bearer ${inMemoryToken}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

export const getAuthToken = () => inMemoryToken;

export const api = axios.create({
  baseURL: getBaseApiUrl(),
  timeout: 10000,
  withCredentials: true, // ✅ Tự động gửi và nhận HttpOnly Cookie
});

export const toAbsoluteUrl = (url) => {
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url;
  const root = api.defaults.baseURL?.replace(/\/+$/, "") || "";
  const path = url.startsWith("/") ? url : `/${url}`;
  return `${root}${path}`;
};

// Request interceptor: tự động gắn in-memory token nếu có (hỗ trợ kép với HttpOnly Cookie)
api.interceptors.request.use((config) => {
  // Cập nhật baseURL nếu hostname thay đổi
  if (!config.baseURL || config.baseURL.includes("localhost") || config.baseURL.includes("127.0.0.1")) {
    config.baseURL = getBaseApiUrl();
  }
  if (inMemoryToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${inMemoryToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      setAuthToken(null);
    }
    return Promise.reject(error);
  }
);

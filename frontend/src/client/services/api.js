// File: frontend/src/client/services/api.js
import axios from "axios";

// 1. Lấy URL từ file .env (Code cũ hardcode nhom09_backend là sai)
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL, // <--- SỬA LỖI Ở ĐÂY (Code cũ là API_BASE_URL gây lỗi crash)
  timeout: 10000,
});

export const toAbsoluteUrl = (url) => {
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url;
  // Sửa nhẹ để tránh double slash //
  const root = api.defaults.baseURL?.replace(/\/+$/, "") || "";
  const path = url.startsWith("/") ? url : `/${url}`;
  return `${root}${path}`;
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
    }
    return Promise.reject(error);
  }
);

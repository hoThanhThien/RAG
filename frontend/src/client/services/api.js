// File: frontend/src/client/services/api.js
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
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

// Không còn lưu hay đọc access_token từ localStorage (chống XSS 100%)
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

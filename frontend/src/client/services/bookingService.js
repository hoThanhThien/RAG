// src/client/services/bookingService.js
import { api } from "./api";

export const bookingService = {
  async create(payload) {
    try {
      // BE đang @router.post("/") với prefix="/bookings" → POST /bookings/
      const res = await api.post("/bookings/", payload);
      return { ok: true, data: res.data };
    } catch (e) {
      // fallback nếu server map cả /bookings
      if (e?.response?.status === 404 || e?.response?.status === 405) {
        try {
          const res2 = await api.post("/bookings", payload);
          return { ok: true, data: res2.data };
        } catch (e2) {
          return { ok: false, error: e2?.response?.data || e2.message };
        }
      }
      return { ok: false, error: e?.response?.data || e.message };
    }
  },
  async getById(bookingId) {
    const res = await api.get(`/bookings/${bookingId}`);
    return res.data; // { booking_id, order_code, total_amount, ... }
  },
};

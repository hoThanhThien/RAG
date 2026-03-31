// src/services/bookingService.js
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function authHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Chuẩn hoá response phân trang về { items, meta }
function normalizePaging(json) {
  // Trường hợp BE đã trả meta gói sẵn
  if (json && json.meta) {
    const { meta, items } = json;
    return {
      items: Array.isArray(items) ? items : [],
      meta: {
        page: meta.page ?? 1,
        page_size: meta.page_size ?? 10,
        total: meta.total ?? 0,
        total_pages: meta.total_pages ?? 1,
        has_next: !!meta.has_next,
        has_prev: !!meta.has_prev,
      },
    };
  }
  // Trường hợp BE trả meta ở root
  return {
    items: Array.isArray(json?.items) ? json.items : [],
    meta: {
      page: json?.page ?? 1,
      page_size: json?.page_size ?? 10,
      total: json?.total ?? 0,
      total_pages: json?.total_pages ?? 1,
      has_next: !!json?.has_next,
      has_prev: !!json?.has_prev,
    },
  };
}

export async function getBookings({
  page = 1,
  page_size = 10,
  status_filter = "",
  sort = "booking_date:desc",
} = {}) {
  const qs = new URLSearchParams();
  qs.set("page", page);
  qs.set("page_size", page_size);
  if (status_filter) qs.set("status_filter", status_filter);
  if (sort) qs.set("sort", sort);

  const res = await fetch(`${API_BASE}/bookings?${qs.toString()}`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));

  const json = await res.json();
  return normalizePaging(json); // --> { items, meta }
}

export async function createBooking({ tour_id, number_of_people, discount_id = null }) {
  const res = await fetch(`${API_BASE}/bookings/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ tour_id, number_of_people, discount_id }),
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json(); // { message, booking_id, order_code, total_amount }
}

export async function getBookingDetail(bookingId) {
  const res = await fetch(`${API_BASE}/bookings/${bookingId}`, {
    headers: { "Content-Type": "application/json", ...authHeader() },
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json(); // { booking_id, ..., order_code, ... }
}

export async function updateBookingStatus(bookingId, newStatus) {
  const res = await fetch(
    `${API_BASE}/bookings/${bookingId}/status?new_status=${encodeURIComponent(newStatus)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeader() },
      credentials: "include",
    }
  );
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json();
}

export async function cancelBooking(bookingId) {
  const res = await fetch(`${API_BASE}/bookings/${bookingId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...authHeader() },
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json();
}

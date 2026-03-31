import { api } from "./api";

/* ===== Helpers ===== */

/** Base URL của API để ghép ảnh tương đối */
const API_BASE_URL = api?.defaults?.baseURL ?? "";
const API_URL = "http://nhom09_backend:8000"

/** Ghép URL ảnh tương đối thành tuyệt đối (handle https, data, blob, //cdn) */
function resolveImageUrl(url) {
  if (!url) return "";
  const s = String(url);

  // đã là absolute: http(s), data:, blob:, protocol-relative //cdn...
  if (/^(https?:|data:|blob:)/i.test(s)) return s;
  if (/^\/\//.test(s)) {
    // protocol-relative → mượn protocol từ base
    try {
      const proto = new URL(API_BASE_URL).protocol || "https:";
      return `${proto}${s}`;
    } catch {
      return `https:${s}`;
    }
  }

  // tương đối /uploads/... hoặc uploads/...
  try {
    // new URL xử lý chuẩn dấu /
    return new URL(s.replace(/^\/+/, "/"), API_BASE_URL.replace(/\/+$/, "/")).toString();
  } catch {
    // fallback nối chuỗi
    return `${API_BASE_URL?.replace(/\/+$/, "")}/${s.replace(/^\/+/, "")}`;
  }
}

/** Lấy ảnh đại diện: primary → first → "" */
function pickPrimaryPhoto(photos = [], fallbackTopLevel) {
  if (Array.isArray(photos) && photos.length) {
    const primary = photos.find((p) => Number(p.is_primary) === 1) || photos[0];
    return resolveImageUrl(primary?.image_url);
  }
  return resolveImageUrl(fallbackTopLevel);
}

/** Tính số ngày (bao gồm cả start & end) bằng UTC để không lệch múi giờ */
function calcDurationDays(start_date, end_date) {
  if (!start_date || !end_date) return null;
  const [y1, m1, d1] = String(start_date).split("-").map(Number);
  const [y2, m2, d2] = String(end_date).split("-").map(Number);
  if ([y1, m1, d1, y2, m2, d2].some((n) => Number.isNaN(n))) return null;
  const s = Date.UTC(y1, m1 - 1, d1);
  const e = Date.UTC(y2, m2 - 1, d2);
  const days = Math.floor((e - s) / 86400000) + 1;
  return Number.isFinite(days) ? Math.max(1, days) : null;
}

/** Map 1 photo */
function mapPhoto(p = {}) {
  return {
    ...p,
    photo_id: p.photo_id ?? p.PhotoID ?? p.id,
    image_url: resolveImageUrl(p.image_url ?? p.ImageURL),
    is_primary: Number(p.is_primary ?? p.IsPrimary ?? 0),
    caption: p.caption ?? p.Caption ?? "",
    upload_date: p.upload_date ?? p.UploadDate ?? null,
  };
}

/** Chuẩn hóa tour cho UI */
function mapTour(t = {}) {
  const photos = Array.isArray(t.photos) ? t.photos.map(mapPhoto) : [];
  return {
    id: t.tour_id ?? t.id,
    title: t.title,
    location: t.location,
    short_desc: t.description,
    description: t.description,
    price: t.price,
    start_date: t.start_date,
    end_date: t.end_date,
    duration_days: calcDurationDays(t.start_date, t.end_date),
    status: t.status,
    category_id: t.category_id,
    category_name: t.category_name,
    capacity: t.capacity,
    rating: t.rating ?? null, // UI có thể default nếu null
    photos,
    image_url: pickPrimaryPhoto(photos, t.image_url), // đại diện
  };
}

/* ===== Service ===== */

export const tourService = {
  /** GET /tours?page=&page_size= → { items:[mapped], meta } */
  async getAll(params = {}) {
    const res = await api.get("/tours", { params });
    const rawItems = res.data?.items ?? [];
    const items = rawItems.map(mapTour);

    const meta = {
      page: res.data?.page ?? 1,
      page_size: res.data?.page_size ?? rawItems.length,
      total: res.data?.total ?? rawItems.length,
      total_pages: res.data?.total_pages ?? 1,
      has_next: res.data?.has_next ?? false,
      has_prev: res.data?.has_prev ?? false,
    };
    return { items, meta };
  },

  /** Thử tải ảnh riêng nếu endpoint detail không trả photos */
  async _ensurePhotos(id, tourObj) {
    if (tourObj.photos?.length) return tourObj;

    // Ưu tiên /tours/:id/photos
    try {
      const pr = await api.get(`/tours/${id}/photos`);
      const photos = (pr.data?.items ?? pr.data?.data ?? pr.data ?? []).map(mapPhoto);
      return { ...tourObj, photos, image_url: pickPrimaryPhoto(photos, tourObj.image_url) };
    } catch {
      // Fallback /photos?tour_id=
      try {
        const pr2 = await api.get(`/photos`, { params: { tour_id: id } });
        const photos = (pr2.data?.items ?? pr2.data?.data ?? pr2.data ?? []).map(mapPhoto);
        return { ...tourObj, photos, image_url: pickPrimaryPhoto(photos, tourObj.image_url) };
      } catch {
        return tourObj; // không có endpoint ảnh → giữ nguyên
      }
    }
  },

  /** GET /tours/:id → object mapped (có cố gắng lấp ảnh) */
  async getById(id) {
    const res = await api.get(`/tours/${id}`);
    const raw = res.data?.data ?? (Array.isArray(res.data?.items) ? res.data.items[0] : res.data);
    let mapped = mapTour(raw || {});
    mapped = await this._ensurePhotos(id, mapped);
    return mapped;
  },
};

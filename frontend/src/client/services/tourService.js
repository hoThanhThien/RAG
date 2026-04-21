import { api } from "./api";

/* ===== Helpers ===== */

const API_BASE_URL = api?.defaults?.baseURL ?? "";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

/** 🔥 Tối ưu ảnh */
function optimizeImage(url) {
  if (!url) return "";

  // localhost uploads
  if (url.includes("/uploads/")) {
    return url + "?w=600&q=70";
  }

  // cloudinary (nếu có)
  if (url.includes("cloudinary")) {
    return url.replace("/upload/", "/upload/w_600,q_70/");
  }

  return url;
}

/** Ghép URL ảnh */
function resolveImageUrl(url) {
  if (!url) return "";
  const s = String(url);

  if (/^(https?:|data:|blob:)/i.test(s)) return optimizeImage(s);

  if (/^\/\//.test(s)) {
    try {
      const proto = new URL(API_BASE_URL).protocol || "https:";
      return optimizeImage(`${proto}${s}`);
    } catch {
      return optimizeImage(`https:${s}`);
    }
  }

  try {
    const full = new URL(
      s.replace(/^\/+/, "/"),
      API_BASE_URL.replace(/\/+$/, "/")
    ).toString();

    return optimizeImage(full); // 🔥 quan trọng
  } catch {
    const full = `${API_BASE_URL?.replace(/\/+$/, "")}/${s.replace(/^\/+/, "")}`;
    return optimizeImage(full);
  }
}

/** Các function còn lại giữ nguyên */
function pickPrimaryPhoto(photos = [], fallbackTopLevel) {
  if (Array.isArray(photos) && photos.length) {
    const primary = photos.find((p) => Number(p.is_primary) === 1) || photos[0];
    return resolveImageUrl(primary?.image_url);
  }
  return resolveImageUrl(fallbackTopLevel);
}

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

function mapTour(t = {}) {
  const photos = Array.isArray(t.photos) ? t.photos.map(mapPhoto) : [];
  return {
    id: t.tour_id ?? t.id,
    title: t.title ?? "Chưa có tiêu đề",
    location: t.location ?? "",
    short_desc: t.description ?? "",
    description: t.description ?? "",
    price: t.price,
    start_date: t.start_date,
    end_date: t.end_date,
    duration_days: t.duration_days ?? calcDurationDays(t.start_date, t.end_date),
    status: t.status,
    category_id: t.category_id,
    category_name: t.category_name,
    capacity: t.capacity,
    rating: t.rating ?? null,
    review_count: Number(t.review_count ?? t.total_reviews ?? 0),
    photos,
    image_url: pickPrimaryPhoto(photos, t.image_url),
  };
}

/* ===== Service giữ nguyên ===== */
export const tourService = {
  async getAll(params = {}) {
    const requestParams = {
      active_only: params.active_only ?? false,
      ...params,
    };

    const res = await api.get("/tours", { params: requestParams });
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

  async getById(id) {
    const res = await api.get(`/tours/${id}`);
    const raw = res.data?.data ?? (Array.isArray(res.data?.items) ? res.data.items[0] : res.data);
    let mapped = mapTour(raw || {});
    mapped = await this._ensurePhotos(id, mapped);
    return mapped;
  },

  async _ensurePhotos(id, tourObj) {
    if (tourObj.photos?.length) return tourObj;

    try {
      const pr = await api.get(`/tours/${id}/photos`);
      const photos = (pr.data?.items ?? pr.data?.data ?? pr.data ?? []).map(mapPhoto);
      return { ...tourObj, photos, image_url: pickPrimaryPhoto(photos, tourObj.image_url) };
    } catch {
      try {
        const pr2 = await api.get(`/photos`, { params: { tour_id: id } });
        const photos = (pr2.data?.items ?? pr2.data?.data ?? pr2.data ?? []).map(mapPhoto);
        return { ...tourObj, photos, image_url: pickPrimaryPhoto(photos, tourObj.image_url) };
      } catch {
        return tourObj;
      }
    }
  },
};
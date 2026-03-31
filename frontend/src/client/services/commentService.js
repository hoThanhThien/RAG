// src/services/commentService.js
import { api } from "./api";

const mapComment = (r) => ({
  id: r.comment_id ?? r.CommentID ?? r.id,
  user_id: r.user_id ?? r.UserID,
  tour_id: r.tour_id ?? r.TourID,
  content: r.content ?? r.Content,
  rating: Number(r.rating ?? r.Rating ?? 0),
  created_at: r.created_at ?? r.CreatedAt,
  user_name: r.user_name ?? r.UserName ?? r.user?.name ?? "Ẩn danh",
});

const pickMeta = (data) => ({
  page: data?.page ?? 1,
  page_size: data?.page_size ?? (Array.isArray(data?.items) ? data.items.length : 0),
  total: data?.total ?? (Array.isArray(data?.items) ? data.items.length : 0),
  total_pages: data?.total_pages ?? 1,
  has_next: data?.has_next ?? false,
  has_prev: data?.has_prev ?? false,
});

export const commentService = {
  async listByTour(tourId, params = {}) {
    const query = {
      sort: params.sort ?? "created_at:desc",
      page: params.page ?? 1,
      page_size: params.page_size ?? 50,
    };
    try {
      const res = await api.get(`/comments/tour/${tourId}`, { params: query });
      const items = res.data?.items ?? [];
      return { items: items.map(mapComment), meta: pickMeta(res.data) };
    } catch {
      const res = await api.get(`/tours/${tourId}/comments`, { params: query });
      const data = Array.isArray(res.data) ? { items: res.data } : res.data;
      const items = data?.items ?? data?.data ?? data ?? [];
      return { items: items.map(mapComment), meta: pickMeta(data) };
    }
  },

  async canRate(tourId) {
    const res = await api.get(`/comments/can-rate`, { params: { tour_id: Number(tourId) } });
    return Boolean(res.data?.can_rate);
  },

  async create(tourId, { content, rating }) {
    const body = { tour_id: Number(tourId), content };
    if (rating != null) body.rating = rating; // chỉ gửi khi được phép
    const res = await api.post(`/comments`, body);
    const data = res.data?.data ?? res.data;
    return mapComment(data);
  },

  async update(commentId, payload) {
    const res = await api.put(`/comments/${commentId}`, payload);
    return res.data?.data ?? { id: commentId, ...payload };
  },

  async remove(commentId) {
    const res = await api.delete(`/comments/${commentId}`);
    return res.data ?? { ok: true };
  },
    async listMyComments() {
    const res = await api.get("/comments/me");
    const items = res.data?.items ?? [];
    return items.map((r) => ({
      id: r.comment_id ?? r.CommentID,
      tour_id: r.tour_id ?? r.TourID,
      tour_title: r.tour_title ?? r.TourTitle ?? "Không rõ",
      content: r.content ?? r.Content,
      rating: Number(r.rating ?? r.Rating ?? 0),
      created_at: r.created_at ?? r.CreatedAt,
    }));
  },

};


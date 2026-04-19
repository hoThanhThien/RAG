import { api } from "../../client/services/api";

export async function getTours({ page = 1, page_size = 8, q = "", limit_photos = 1 } = {}) {
  const res = await api.get("/tours", {
    params: {
      page,
      page_size,
      limit_photos,
      active_only: false,
      ...(q ? { q } : {}),
    },
  });

  return {
    items: Array.isArray(res.data?.items) ? res.data.items : [],
    meta: {
      page: res.data?.page ?? page,
      page_size: res.data?.page_size ?? page_size,
      total: res.data?.total ?? 0,
      total_pages: res.data?.total_pages ?? 1,
      has_next: !!res.data?.has_next,
      has_prev: !!res.data?.has_prev,
    },
  };
}

export const createTour = (data) => api.post("/tours/", data);
export const updateTour = (id, data) => api.put(`/tours/${id}`, data);
export const deleteTour = (id) => api.delete(`/tours/${id}`);

import { api } from "../../client/services/api";

export async function fetchPhotos(tourId) {
  const res = await api.get("/photos", {
    params: tourId ? { tour_id: tourId } : undefined,
  });
  return Array.isArray(res.data) ? res.data : [];
}

export const getTourPhotos = (tourId) => api.get(`/photos/tour/${tourId}`);
export const addTourPhoto = (tourId, data) => api.post(`/photos/tour/${tourId}`, data);
export const updateTourPhoto = (photoId, data) => api.patch(`/photos/${photoId}`, data);
export const deleteTourPhoto = (photoId) => api.delete(`/photos/${photoId}`);

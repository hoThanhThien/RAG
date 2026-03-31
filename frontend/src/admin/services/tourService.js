import { api } from "../../client/services/api"; // nếu bạn đã có instance axios ở đây

export const getTours = () => api.get("/tours");
export const createTour = (data) => api.post("/tours/", data); // 👈 thêm dấu "/"

export const updateTour = (id, data) => api.put(`/tours/${id}`, data);
export const deleteTour = (id) => api.delete(`/tours/${id}`);

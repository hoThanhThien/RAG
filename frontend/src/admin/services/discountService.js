import { api } from "../../client/services/api"; // nếu bạn đã có instance axios ở đây

export async function fetchDiscounts() {
  const res = await api.get("/discounts");
  return res.data;
}

export async function createDiscount(data) {
  const res = await api.post("/discounts", data);
  return res.data;
}

export async function updateDiscount(id, data) {
  const res = await api.put(`/discounts/${id}`, data);
  return res.data;
}

export async function deleteDiscount(id) {
  const res = await api.delete(`/discounts/${id}`);
  return res.data;
}

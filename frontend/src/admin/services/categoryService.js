import { api } from "../../client/services/api"; // nếu bạn đã có instance axios ở đây

export const fetchCategories = async () => {
  const res = await api.get("/categories");
  return res.data.items || [];
};

export const createCategory = async (data) => {
  await api.post("/categories", data);
};

export const updateCategory = async (id, data) => {
  await api.put(`/categories/${id}`, data);
};

export const deleteCategory = async (id) => {
  await api.delete(`/categories/${id}`);
};

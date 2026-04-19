// userService.js
import { api } from "../../client/services/api";

export const fetchUsers = async ({
  page = 1,
  page_size = 8,
  q = "",
  sort = "user_id:desc",
  returnMeta = false,
} = {}) => {
  try {
    const res = await api.get("/users", {
      params: { page, page_size, q: q || undefined, sort },
    });
    return returnMeta ? res.data : (res.data.items || []);
  } catch (err) {
    console.error("❌ Failed to fetch users", err);
    return returnMeta
      ? { items: [], page: 1, page_size, total: 0, total_pages: 1, has_next: false, has_prev: false }
      : [];
  }
};

export const deleteUser = async (id) => {
  try {
    await api.delete(`/users/${id}`);
  } catch (err) {
    console.error("❌ Failed to delete user", err);
  }
};

// ✅ Gọi đúng API update user
export const updateUser = async (id, data) => {
  try {
    await api.put(`/users/${id}`, data);
  } catch (err) {
    console.error("❌ Failed to update user", err);
  }
};



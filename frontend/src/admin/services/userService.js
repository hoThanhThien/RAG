// userService.js
import { api } from "../../client/services/api";

export const fetchUsers = async () => {
  try {
    const res = await api.get("/users");
    return res.data.items;
  } catch (err) {
    console.error("❌ Failed to fetch users", err);
    return [];
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



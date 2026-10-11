import { api, setAuthToken } from "./api";

// Đăng ký
export const register = async ({ first_name, last_name, email, password, phone }) => {
  try {
    await api.post("/auth/register", {
      first_name,
      last_name,
      email,
      password,
      phone,
      role_id: 3, // default user
    });
    return { success: true };
  } catch (err) {
    return {
      success: false,
      message: err?.response?.data?.detail || "Lỗi đăng ký",
    };
  }
};

// Đăng nhập (HttpOnly Cookie được tự động lưu + Token trong RAM)
export const login = async (data) => {
  try {
    const res = await api.post("/auth/login", data);
    const token = res.data?.access_token;
    if (token) {
      setAuthToken(token);
    }

    // Gọi /auth/me để lấy thông tin người dùng
    const userRes = await api.get("/auth/me");
    return { success: true, user: userRes.data };
  } catch (err) {
    return {
      success: false,
      message: err?.response?.data?.detail || "Đăng nhập thất bại",
    };
  }
};

// Đăng xuất (Backend xóa HttpOnly Cookie + Xóa token trong RAM)
export const logout = async () => {
  try {
    await api.post("/auth/logout");
  } catch {
    // Không cần xử lý lỗi logout
  }
  setAuthToken(null);
};

// Lấy user hiện tại
export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};

export const changePassword = async (old_password, new_password) => {
  const res = await api.put("/auth/change-password", {
    old_password,
    new_password,
  });
  return res.data;
};
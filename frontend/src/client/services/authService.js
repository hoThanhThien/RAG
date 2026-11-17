import { api, clearClientStoredTokens } from "./api";

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

// Đăng nhập (JWT accessToken & refreshToken được lưu hoàn toàn trong HttpOnly Cookie)
export const login = async (data) => {
  try {
    clearClientStoredTokens();
    const res = await api.post("/auth/login", data);
    const loginPayload = res.data?.data || {};
    const message = res.data?.message || "Đăng nhập thành công";

    // Gọi /auth/me để lấy thông tin người dùng hiện tại qua HttpOnly Cookie
    const userRes = await api.get("/auth/me");
    const user = {
      ...(loginPayload.account || {}),
      ...(userRes.data || {}),
    };
    return {
      success: true,
      user,
      data: loginPayload,
      message,
    };
  } catch (err) {
    return {
      success: false,
      message: err?.response?.data?.detail || "Đăng nhập thất bại",
    };
  }
};

// Làm mới phiên đăng nhập từ refresh_token trong HttpOnly Cookie
export const refreshSession = async () => {
  const res = await api.post("/auth/refresh");
  return res.data;
};

// Đăng xuất (Backend xóa HttpOnly Cookies access_token & refresh_token)
export const logout = async () => {
  try {
    await api.post("/auth/logout");
  } catch {
    // Không cần xử lý lỗi logout
  } finally {
    clearClientStoredTokens();
  }
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

import { api, clearClientStoredTokens } from "./api";

// Đăng ký (Mã hóa mật khẩu bcrypt, tự động đăng nhập & lưu JWT vào HttpOnly Cookie)
export const register = async ({ first_name, last_name, full_name, email, password, phone }) => {
  try {
    clearClientStoredTokens();
    const res = await api.post("/auth/register", {
      first_name,
      last_name,
      full_name,
      email,
      password,
      phone,
      role_id: 3, // default user
    });
    const loginPayload = res.data?.data || {};
    const message = res.data?.message || "Đăng ký tài khoản thành công";

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

// Đăng ký / Đăng nhập bằng Google (tự tạo tài khoản nếu email chưa tồn tại & lưu JWT vào HttpOnly Cookie)
export const loginWithGoogle = async (payload) => {
  try {
    clearClientStoredTokens();
    const res = await api.post("/auth/google", payload);
    const loginPayload = res.data?.data || {};
    const message = res.data?.message || "Đăng nhập bằng Google thành công";

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
      message: err?.response?.data?.detail || "Đăng nhập Google thất bại",
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

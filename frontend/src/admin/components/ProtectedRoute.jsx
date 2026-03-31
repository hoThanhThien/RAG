// src/admin/components/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../../client/context/AuthContext"; // path đúng rồi

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  // ✅ Loading thì chưa render gì cả
  if (loading) return null;

  // ✅ Chưa đăng nhập thì về trang auth
  if (!user) return <Navigate to="/auth" />;

  // ✅ Kiểm tra role
  const roleId = Number(user.role_id); // ép kiểu rõ ràng
  if (!allowedRoles.includes(roleId)) return <Navigate to="/" />;

  return children;
}

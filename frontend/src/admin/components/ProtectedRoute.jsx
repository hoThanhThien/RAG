// src/admin/components/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../../client/context/AuthContext"; // path đúng rồi

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();


  if (loading) return null;

  if (!user) return <Navigate to="/auth" />;


  const roleId = Number(user.role_id); // ép kiểu rõ ràng
  if (!allowedRoles.includes(roleId)) return <Navigate to="/" />;

  return children;
}

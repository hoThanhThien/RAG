// UserTable.jsx
import React from "react";

export default function UserTable({ users, onDelete, onEdit, loading = false }) {
  const visibleUsers = (users || []).filter(
    (u) => String(u?.role_name || "").toLowerCase() !== "admin"
  );

  return (
    <table className="table table-bordered table-striped align-middle">
      <thead className="table-dark">
        <tr>
          <th>ID</th>
          <th>Full Name</th>
          <th>Email</th>
          <th>Phone</th>
          <th>Hành động</th>
        </tr>
      </thead>
      <tbody>
        {loading ? (
          <tr>
            <td colSpan="5" className="text-center py-4">
              Đang tải dữ liệu...
            </td>
          </tr>
        ) : visibleUsers.length === 0 ? (
          <tr>
            <td colSpan="5" className="text-center py-4 text-muted">
              Không có người dùng nào
            </td>
          </tr>
        ) : (
          visibleUsers.map((u) => (
            <tr key={u.user_id}>
              <td>{u.user_id}</td>
              <td>{u.full_name}</td>
              <td>{u.email}</td>
              <td>{u.phone || "—"}</td>
              <td>
                <button className="btn btn-sm btn-primary me-2" onClick={() => onEdit(u)}>
                  Sửa
                </button>
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(u.user_id)}>
                  Xoá
                </button>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

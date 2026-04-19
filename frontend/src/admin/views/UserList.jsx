import React, { useCallback, useEffect, useState } from "react";
import { fetchUsers, deleteUser, updateUser } from "../services/userService";
import UserTable from "../components/tables/UserTable";

const PAGE_SIZE = 8;

export default function UserList() {
  const [users, setUsers] = useState([]);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState({
    page: 1,
    page_size: PAGE_SIZE,
    total: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });

  const loadUsers = useCallback(async (targetPage = page, keyword = searchTerm) => {
    setLoading(true);
    try {
      const data = await fetchUsers({
        page: targetPage,
        page_size: PAGE_SIZE,
        q: keyword.trim(),
        returnMeta: true,
      });
      setUsers(data.items || []);
      setMeta({
        page: data.page || 1,
        page_size: data.page_size || PAGE_SIZE,
        total: data.total || 0,
        total_pages: data.total_pages || 1,
        has_next: !!data.has_next,
        has_prev: !!data.has_prev,
      });
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm]);

  useEffect(() => {
    loadUsers(page, searchTerm);
  }, [page, searchTerm, loadUsers]);

  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá user này không?")) {
      await deleteUser(id);
      const nextPage = users.length === 1 && page > 1 ? page - 1 : page;
      setPage(nextPage);
      loadUsers(nextPage, searchTerm);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setForm({
      full_name: user.full_name,
      email: user.email,
      phone: user.phone,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await updateUser(editingUser.user_id, form);
    setEditingUser(null);
    loadUsers(page, searchTerm);
  };

  const goToPage = (nextPage) => {
    if (nextPage >= 1 && nextPage <= (meta.total_pages || 1)) {
      setPage(nextPage);
    }
  };

  return (
    <div className="container mt-4">
      {/* Tiêu đề + tìm kiếm */}
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-3">
        <h2 className="mb-0">
          <i className="bi bi-people-fill me-2"></i>
          Danh sách người dùng
        </h2>
        <div className="input-group" style={{ maxWidth: "320px" }}>
          <span className="input-group-text bg-white">
            <i className="bi bi-search text-secondary"></i>
          </span>
          <input
            type="text"
            className="form-control"
            placeholder="Tìm kiếm tên hoặc email..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      <div className="d-flex justify-content-between align-items-center mb-2 text-muted small flex-wrap gap-2">
        <span>Hiển thị {users.length} / {meta.total} người dùng</span>
        <span>Trang {meta.page} / {meta.total_pages}</span>
      </div>

      {/* Bảng danh sách */}
      <UserTable
        users={users}
        onDelete={handleDelete}
        onEdit={handleEdit}
        loading={loading}
      />

      <div className="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={!meta.has_prev || loading}
          onClick={() => goToPage(page - 1)}
        >
          ← Trang trước
        </button>

        <div className="d-flex align-items-center gap-2 flex-wrap">
          {Array.from({ length: meta.total_pages || 1 }, (_, i) => i + 1)
            .filter((p) => Math.abs(p - page) <= 2 || p === 1 || p === meta.total_pages)
            .map((p, index, arr) => (
              <React.Fragment key={p}>
                {index > 0 && arr[index - 1] !== p - 1 ? (
                  <span className="px-1 text-muted">...</span>
                ) : null}
                <button
                  className={`btn btn-sm ${p === page ? "btn-primary" : "btn-outline-primary"}`}
                  onClick={() => goToPage(p)}
                  disabled={loading}
                >
                  {p}
                </button>
              </React.Fragment>
            ))}
        </div>

        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={!meta.has_next || loading}
          onClick={() => goToPage(page + 1)}
        >
          Trang sau →
        </button>
      </div>

      {/* Form sửa */}
      {editingUser && (
        <form onSubmit={handleSubmit} className="mt-4 border p-3 rounded bg-light">
          <h4 className="mb-3">Chỉnh sửa người dùng #{editingUser.user_id}</h4>
          <div className="mb-2">
            <label>Full Name:</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="form-control"
              required
            />
          </div>
          <div className="mb-2">
            <label>Email:</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="form-control"
              required
            />
          </div>
          <div className="mb-3">
            <label>Phone:</label>
            <input
              type="text"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="form-control"
            />
          </div>
          <button className="btn btn-success" type="submit">
            Lưu
          </button>
          <button
            type="button"
            className="btn btn-secondary ms-2"
            onClick={() => setEditingUser(null)}
          >
            Huỷ
          </button>
        </form>
      )}
    </div>
  );
}

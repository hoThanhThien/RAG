import React, { useEffect, useState } from "react";
import { fetchUsers, deleteUser, updateUser } from "../services/userService";
import UserTable from "../components/tables/UserTable";

export default function UserList() {
  const [users, setUsers] = useState([]);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
  });
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    const data = await fetchUsers();
    setUsers(data);
  };

  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá user này không?")) {
      await deleteUser(id);
      loadUsers();
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
    loadUsers();
  };

  // Lọc theo tên hoặc email
  const filteredUsers = users.filter((user) =>
    `${user.full_name} ${user.email}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mt-4">
      {/* Tiêu đề + tìm kiếm */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">
          <i className="bi bi-people-fill me-2"></i>
          Danh sách người dùng
        </h2>
        <div className="input-group w-25">
  <span className="input-group-text bg-white">
    <i className="bi bi-search text-secondary"></i>
  </span>
  <input
    type="text"
    className="form-control"
    placeholder="Tìm kiếm tên hoặc email..."
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
  />
</div>

      </div>

      {/* Bảng danh sách */}
      <UserTable
        users={filteredUsers}
        onDelete={handleDelete}
        onEdit={handleEdit}
      />

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

// UserTable.jsx
import React from "react";

export default function UserTable({ users, onDelete, onEdit }) {
  return (
    <table className="table table-bordered table-striped">
      <thead className="table-dark">
        <tr>
          <th>ID</th>
          <th>Full Name</th>
          <th>Email</th>
          <th>Phone</th>
          {/* <th>Role</th> */}
          <th>Hành động</th>
        </tr>
      </thead>
      <tbody>
        {users
          .filter((u) => u.role_name.toLowerCase() !== "admin")
          .map((u) => (
            <tr key={u.user_id}>
              <td>{u.user_id}</td>
              <td>{u.full_name}</td>
              <td>{u.email}</td>
              <td>{u.phone}</td>
              {/* <td>{u.role_name}</td> */}
              <td>
                <button className="btn btn-sm btn-primary me-2" onClick={() => onEdit(u)}>
                  Sửa
                </button>
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(u.user_id)}>
                  Xoá
                </button>
              </td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}

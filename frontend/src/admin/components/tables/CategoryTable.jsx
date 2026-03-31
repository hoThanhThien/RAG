
import React from "react";

export default function CategoryTable({ categories, onEdit, onDelete }) {
  return (
    <table className="table table-bordered table-striped">
      <thead className="table-dark">
        <tr>
          <th>ID</th>
          <th>Tên danh mục</th>
          <th>Mô tả</th>
          <th>Hành động</th>
        </tr>
      </thead>
      <tbody>
        {categories.map((cat) => (
          <tr key={cat.category_id}>
            <td>{cat.category_id}</td>
            <td>{cat.name}</td>
            <td>{cat.description}</td>
            <td>
              <button
                className="btn btn-sm btn-primary me-2"
                onClick={() => onEdit(cat)}
              >
                Sửa
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => onDelete(cat.category_id)}
              >
                Xoá
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

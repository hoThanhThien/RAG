
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
              <div className="d-flex flex-column gap-1" style={{ minWidth: "70px" }}>
                <button
                  className="btn btn-sm btn-primary"
                  style={{ width: "100%" }}
                  onClick={() => onEdit(cat)}
                >
                  Sửa
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  style={{ width: "100%" }}
                  onClick={() => onDelete(cat.category_id)}
                >
                  Xoá
                </button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

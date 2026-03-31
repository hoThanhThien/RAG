import React, { useEffect, useState } from "react";
import {
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from "../services/categoryService";
import CategoryTable from "../components/tables/CategoryTable";

export default function CategoryList() {
  const [categories, setCategories] = useState([]);
  const [formVisible, setFormVisible] = useState(false);
  const [editing, setEditing] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const [form, setForm] = useState({
    name: "",
    description: "",
  });

  const loadCategories = async () => {
    const data = await fetchCategories();
    setCategories(data);
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (editing) {
      await updateCategory(editing.category_id, form);
    } else {
      await createCategory(form);
    }
    setForm({ name: "", description: "" });
    setEditing(null);
    setFormVisible(false);
    loadCategories();
  };

  const handleEdit = (category) => {
    setEditing(category);
    setForm({
      name: category.name,
      description: category.description,
    });
    setFormVisible(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá danh mục này không?")) {
      try {
        await deleteCategory(id);
        loadCategories();
      } catch (error) {
        const msg = error?.response?.data?.detail || "Đã có lỗi xảy ra khi xoá danh mục.";
        alert(msg);
      }
    }
  };

  const handleCancel = () => {
    setEditing(null);
    setForm({ name: "", description: "" });
    setFormVisible(false);
  };

  // ✅ Lọc danh mục theo từ khoá
  const filteredCategories = categories.filter((cat) =>
    `${cat.name} ${cat.description}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mt-4 category-list">
      {/* Tiêu đề và tìm kiếm */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">
          <i className="bi bi-tags-fill me-2"></i>
          Danh sách danh mục
        </h2>
        <div className="input-group w-25">
          <span className="input-group-text bg-white">
            <i className="bi bi-search text-secondary"></i>
          </span>
          <input
            type="text"
            className="form-control"
            placeholder="Tìm kiếm tên hoặc mô tả..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Nút thêm danh mục */}
      <div className="mb-3">
        <button className="btn btn-success" onClick={() => setFormVisible(!formVisible)}>
  {formVisible ? "Ẩn form" : "➕ Thêm danh mục"}
</button>

      </div>

      {/* Bảng danh sách */}
      <CategoryTable
        categories={filteredCategories}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {/* Form thêm/sửa danh mục */}
      {formVisible && (
        <form onSubmit={handleSubmit} className="mt-4 border p-3 rounded bg-light">
          <h4 className="mb-3">
            {editing ? `Chỉnh sửa danh mục #${editing.category_id}` : "Thêm danh mục mới"}
          </h4>
          <div className="mb-2">
            <label>Tên danh mục:</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="form-control"
              required
            />
          </div>
          <div className="mb-3">
            <label>Mô tả:</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="form-control"
              rows={3}
            />
          </div>
          <button type="submit" className="btn btn-success">
            {editing ? "Lưu thay đổi" : "Thêm"}
          </button>
          <button type="button" onClick={handleCancel} className="btn btn-secondary ms-2">
            Huỷ
          </button>
        </form>
      )}
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { getTours, createTour, updateTour, deleteTour } from '../services/tourService';
import TourTable from '../components/tables/TourTable';
import TourForm from '../components/forms/TourForm';

export default function TourList() {
  const [tours, setTours] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingTour, setEditingTour] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  // 📥 Load danh sách tour
  const loadData = async () => {
    try {
      const res = await getTours();
      setTours(res.data.items || []);
    } catch (err) {
      console.error("❌ Lỗi tải tour:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 📝 Thêm/Sửa tour
  const handleFormSubmit = async (formData) => {
    try {
      if (editingTour) {
        await updateTour(editingTour.tour_id, formData);
      } else {
        await createTour(formData);
      }
      await loadData();
      setShowForm(false);
      setEditingTour(null);
    } catch (error) {
      console.error("❌ Lỗi xử lý form:", error);
    }
  };

  // 🗑 Xoá tour
  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá tour này không?")) {
      try {
        await deleteTour(id);
        await loadData();
      } catch (err) {
        console.error("❌ Lỗi xoá tour:", err);
      }
    }
  };

  // ✏️ Sửa tour
  const handleEdit = (tour) => {
    setEditingTour(tour);
    setShowForm(true);
  };

  // 🔍 Lọc tour theo tên/mô tả/địa điểm
  const filteredTours = tours.filter((tour) =>
    `${tour.name} ${tour.description} ${tour.location} ${tour.price}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mt-4">
      {/* Tiêu đề + tìm kiếm */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">
          <i className="bi bi-map-fill me-2"></i>
          Danh sách Tour
        </h2>
        {!showForm && (
          <div className="input-group w-25">
            <span className="input-group-text bg-white">
              <i className="bi bi-search text-secondary"></i>
            </span>
            <input
              type="text"
              className="form-control"
              placeholder="Tìm kiếm theo tên, địa điểm..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Hiển thị form hoặc bảng */}
      {showForm ? (
        <TourForm
          initialData={editingTour}
          onSubmit={() => {
            loadData();
            setShowForm(false);
            setEditingTour(null);
          }}
          onCancel={() => {
            setShowForm(false);
            setEditingTour(null);
          }}
        />
      ) : (
        <>
          <button className="btn btn-success mb-3" onClick={() => setShowForm(true)}>
            ➕ Thêm tour
          </button>
          <TourTable
            tours={filteredTours}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
}

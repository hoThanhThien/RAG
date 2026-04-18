import React, { useEffect, useState } from "react";
import { getTours, deleteTour } from "../services/tourService";
import TourTable from "../components/tables/TourTable";
import TourForm from "../components/forms/TourForm";

const PAGE_SIZE = 8;

export default function TourList() {
  const [tours, setTours] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingTour, setEditingTour] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState({
    page: 1,
    page_size: PAGE_SIZE,
    total: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });

  const loadData = async ({ page = 1, q = searchTerm } = {}) => {
    try {
      setLoading(true);
      const res = await getTours({
        page,
        page_size: PAGE_SIZE,
        q,
        limit_photos: 1,
      });
      setTours(res.items || []);
      setMeta(res.meta);
    } catch (err) {
      console.error("❌ Lỗi tải tour:", err);
      setTours([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (showForm) return;
    const timer = setTimeout(() => {
      loadData({ page: 1, q: searchTerm });
    }, 250);
    return () => clearTimeout(timer);
  }, [searchTerm, showForm]);

  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá tour này không?")) {
      try {
        await deleteTour(id);
        const nextPage = tours.length === 1 && meta.page > 1 ? meta.page - 1 : meta.page;
        await loadData({ page: nextPage, q: searchTerm });
      } catch (err) {
        console.error("❌ Lỗi xoá tour:", err);
      }
    }
  };

  const handleEdit = (tour) => {
    setEditingTour(tour);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingTour(null);
  };

  const goToPage = (page) => {
    if (page < 1 || page > meta.total_pages || loading) return;
    loadData({ page, q: searchTerm });
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h2 className="mb-0">
          <i className="bi bi-map-fill me-2"></i>
          Danh sách Tour
        </h2>
        {!showForm && (
          <div className="input-group" style={{ maxWidth: 320 }}>
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

      {showForm ? (
        <TourForm
          initialData={editingTour}
          onSubmit={async () => {
            await loadData({ page: meta.page, q: searchTerm });
            closeForm();
          }}
          onCancel={closeForm}
        />
      ) : (
        <>
          <button className="btn btn-success mb-3" onClick={() => setShowForm(true)}>
            ➕ Thêm tour
          </button>

          {loading && <div className="alert alert-info">Đang tải danh sách tour...</div>}

          <TourTable tours={tours} onEdit={handleEdit} onDelete={handleDelete} />

          <div className="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
            <div className="text-muted small">
              Đang hiển thị trang {meta.page}/{meta.total_pages} • Tổng {meta.total} tour
            </div>

            <div className="d-flex gap-2">
              <button
                className="btn btn-outline-secondary btn-sm"
                disabled={!meta.has_prev || loading}
                onClick={() => goToPage(meta.page - 1)}
              >
                ← Trước
              </button>
              <button
                className="btn btn-outline-secondary btn-sm"
                disabled={!meta.has_next || loading}
                onClick={() => goToPage(meta.page + 1)}
              >
                Sau →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

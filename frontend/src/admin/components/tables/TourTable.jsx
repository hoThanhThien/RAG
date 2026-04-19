import React from "react";
import { toAbsoluteUrl } from "../../../client/services/api";

export default function TourTable({ tours, onEdit, onDelete }) {
  const safeTours = Array.isArray(tours)
    ? tours.filter((tour) => tour && typeof tour === "object")
    : [];

  return (
    <div className="table-responsive">
      <table className="table table-striped table-bordered align-middle">
        <thead className="table-dark">
          <tr>
            <th>ID</th>
            <th>Ảnh</th>
            <th>Tiêu đề</th>
            <th>Địa điểm</th>
            <th>Mô tả</th>
            <th>Số chỗ</th>
            <th>Giá</th>
            <th>Ngày bắt đầu</th>
            <th>Ngày kết thúc</th>
            <th>Trạng thái</th>
            <th>Danh mục</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          {safeTours.length === 0 ? (
            <tr>
              <td colSpan="12" className="text-center text-muted py-4">
                Không có tour phù hợp
              </td>
            </tr>
          ) : (
            safeTours.map((tour, index) => {
              const safeTour = tour || {};
              const title = safeTour.title || "Chưa có tiêu đề";
              const firstPhoto = safeTour.photos?.[0]?.image_url
                ? toAbsoluteUrl(String(safeTour.photos[0].image_url).trim())
                : "";

              return (
                <tr key={safeTour.tour_id ?? `tour-${index}`}>
                  <td>{safeTour.tour_id ?? "—"}</td>
                  <td>
                    {firstPhoto ? (
                      <img
                        src={firstPhoto}
                        alt={title}
                        style={{ width: "80px", height: "60px", objectFit: "cover", borderRadius: 6 }}
                      />
                    ) : (
                      <span className="text-muted">Không có ảnh</span>
                    )}
                  </td>
                  <td>{title}</td>
                  <td>{safeTour.location || "—"}</td>
                  <td>{safeTour.description || "—"}</td>
                  <td>{safeTour.capacity ?? "—"}</td>
                  <td>${Number(safeTour.price || 0).toLocaleString()}</td>
                  <td>{safeTour.start_date || "—"}</td>
                  <td>{safeTour.end_date || "—"}</td>
                  <td>{safeTour.status || "—"}</td>
                  <td>{safeTour.category_name || safeTour.category_id || "—"}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-primary me-2"
                      onClick={() => onEdit(safeTour)}
                    >
                      Sửa
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => onDelete(safeTour.tour_id)}
                    >
                      Xoá
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

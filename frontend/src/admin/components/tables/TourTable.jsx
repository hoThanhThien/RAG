import React from "react";
import { toAbsoluteUrl } from "../../../client/services/api";

export default function TourTable({ tours, onEdit, onDelete }) {
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
          {tours.length === 0 ? (
            <tr>
              <td colSpan="12" className="text-center text-muted py-4">
                Không có tour phù hợp
              </td>
            </tr>
          ) : (
            tours.map((tour) => {
              const firstPhoto = tour.photos?.[0]?.image_url
                ? toAbsoluteUrl(String(tour.photos[0].image_url).trim())
                : "";

              return (
                <tr key={tour.tour_id}>
                  <td>{tour.tour_id}</td>
                  <td>
                    {firstPhoto ? (
                      <img
                        src={firstPhoto}
                        alt={tour.title}
                        style={{ width: "80px", height: "60px", objectFit: "cover", borderRadius: 6 }}
                      />
                    ) : (
                      <span className="text-muted">Không có ảnh</span>
                    )}
                  </td>
                  <td>{tour.title}</td>
                  <td>{tour.location}</td>
                  <td>{tour.description}</td>
                  <td>{tour.capacity}</td>
                  <td>${Number(tour.price || 0).toLocaleString()}</td>
                  <td>{tour.start_date}</td>
                  <td>{tour.end_date}</td>
                  <td>{tour.status}</td>
                  <td>{tour.category_name || tour.category_id}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-primary me-2"
                      onClick={() => onEdit(tour)}
                    >
                      Sửa
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => onDelete(tour.tour_id)}
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

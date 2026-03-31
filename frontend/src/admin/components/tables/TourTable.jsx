import React from "react";

export default function TourTable({ tours, onEdit, onDelete }) {
  return (
    <div className="table-responsive">
      <table className="table table-striped table-bordered">
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
          {tours.map((tour) => (
            <tr key={tour.tour_id}>
              <td>{tour.tour_id}</td>
              <td>
  {tour.photos?.length > 0 ? (
    <img
      src={
        tour.photos[0].image_url.startsWith("http")
          ? tour.photos[0].image_url
          : `http://localhost:8000${tour.photos[0].image_url.trim()}`
      }
      alt="tour"
      style={{ width: "80px", height: "60px", objectFit: "cover" }}
    />
  ) : (
    <span className="text-muted">Không có ảnh</span>
  )}
</td>

              <td>{tour.title}</td>
              <td>{tour.location}</td>
              <td>{tour.description}</td>
              <td>{tour.capacity}</td>
              <td>${tour.price}</td>
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
          ))}
        </tbody>
      </table>
    </div>
  );
}

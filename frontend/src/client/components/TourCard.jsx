// src/client/components/TourCard.jsx
import React from "react";
import { Link } from "react-router-dom";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

function diffDays(start, end) {
  try {
    const s = new Date(start);
    const e = new Date(end);
    const ms = e - s;
    if (isNaN(ms)) return null;
    const days = Math.max(1, Math.round(ms / (1000 * 60 * 60 * 24)) + 1);
    return days;
  } catch {
    return null;
  }
}

export default function TourCard({ tour }) {
  const days = tour.duration_days ?? diffDays(tour.start_date, tour.end_date);
  const badge = days ? `${days} days` : "Schedule TBA";
  // Nếu chưa có rating thì mặc định 5.0, nếu có rồi thì lấy giá trị rating
  const rating = tour.rating !== null && tour.rating !== undefined 
    ? Math.max(0, Math.min(5, Math.round(tour.rating))) 
    : 5;
  const img = tour.image_url || "/no-image.png";
  const priceLabel =
    typeof tour.price === "number" ? fmtVND.format(tour.price) : tour.price ?? "Liên hệ";

  const renderStars = (val) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <i
          key={i}
          className={`bi ${i <= val ? "bi-star-fill" : "bi-star"} text-warning`}
          aria-hidden="true"
        />
      );
    }
    return stars;
  };

  return (
    <div
      className="card border-0 shadow-lg h-100 d-flex flex-column"
      style={{ borderRadius: "20px", transition: "all 0.3s ease", overflow: "hidden" }}
    >
      {/* Hình ảnh */}
      <figure className="position-relative overflow-hidden m-0">
        <Link to={`/tours/${tour.id}`} className="d-block">
          <img
            src={img}
            className="card-img-top"
            style={{ height: "280px", objectFit: "cover", transition: "transform 0.3s ease" }}
            alt={tour.title}
            loading="lazy"
            onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.1)")}
            onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
            onError={(e) => {
              e.currentTarget.onerror = null;
              e.currentTarget.src = "/no-image.png";
            }}
          />
        </Link>

        <span className="position-absolute top-0 end-0 m-3 bg-danger text-white px-3 py-1 rounded-pill d-flex align-items-center gap-1 shadow-sm small">
          <i className="bi bi-clock" />
          {badge}
        </span>
      </figure>

      {/* Thân card */}
      <div className="card-body d-flex flex-column justify-content-between p-4">
        <div>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <span className="text-primary fw-bold">
              Giá: <span className="text-primary">{priceLabel}</span>
            </span>
            <span className="d-flex align-items-center gap-1" aria-label={`Rating ${rating}/5`}>
              {renderStars(rating)}
            </span>
          </div>

          <h5 className="card-title mb-2" style={{ lineHeight: "1.4" }}>
            <Link to={`/tours/${tour.id}`} className="text-dark text-decoration-none fw-semibold">
              {tour.title}
            </Link>
          </h5>

          <address className="card-location text-muted d-flex align-items-center gap-2 mb-3">
            <i className="bi bi-geo-alt-fill text-danger" />
            <span className="small">{tour.location}</span>
          </address>
        </div>

        {/* Nút */}
        <div className="text-end mt-auto">
          <Link to={`/tours/${tour.id}`} className="btn btn-outline-primary btn-sm rounded-pill">
            View details
          </Link>
        </div>
      </div>
    </div>
  );
}

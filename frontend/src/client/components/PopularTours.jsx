// src/client/components/PopularTours.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { tourService } from "../services/tourService"; // chú ý path (ra ngoài client 1 cấp)

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

function diffDays(start, end) {
  const s = new Date(start);
  const e = new Date(end);
  const ms = e - s;
  if (isNaN(ms)) return null;
  return Math.max(1, Math.round(ms / (1000 * 60 * 60 * 24)) + 1); // ví dụ “4 ngày 3 đêm” -> 4
}

export default function PopularTours() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const { items } = await tourService.getAll({ page: 1, page_size: 6 });
        // items đã được mapTour trong service: {id, title, location, price, start_date, end_date, image_url, ...}
        if (!alive) return;

        const mapped = items.map((t) => ({
          id: t.id,
          title: t.title,
          location: t.location,
          priceLabel: typeof t.price === "number" ? `Giá: ${fmtVND.format(t.price)}` : t.price,
          durationLabel: (() => {
            const d = diffDays(t.start_date, t.end_date);
            return d ? `${d} Days` : "Schedule TBA";
          })(),
          // Nếu chưa có rating (null/undefined) hoặc review_count = 0 thì mặc định 5.0
          rating: (t.rating !== null && t.rating !== undefined && t.review_count > 0) ? t.rating : 5.0,
          reviews: t.review_count ?? 0,
          image: t.image_url || "/no-image.png",
        }));

        setTours(mapped);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const renderStars = (rating) => {
    const r = Math.max(0, Math.min(5, Math.round(rating)));
    return Array.from({ length: 5 }, (_, i) => (
      <i key={i} className={`bi ${i + 1 <= r ? "bi-star-fill" : "bi-star"} text-warning`} />
    ));
  };

  if (loading) {
    return (
      <section id="tours" className="section popular py-5 bg-white">
        <div className="container text-center">
          <div className="spinner-border text-primary" role="status" />
          <p className="mt-3 text-muted">Đang tải tour nổi bật…</p>
        </div>
      </section>
    );
  }

  return (
    <section id="tours" className="section popular py-5 bg-white">
      <div className="container">
        <div className="text-center mb-5">
          <p
            className="section-subtitle text-primary mb-2"
            style={{ fontSize: "1rem", letterSpacing: "2px", textTransform: "uppercase" }}
          >
            Featured Tours
          </p>
          <h2 className="section-title display-5 fw-bold mb-3">Most Popular Tours</h2>
        </div>

        <div className="row g-4 justify-content-center">
          {tours.map((tour) => (
            <div key={tour.id} className="col-lg-4 col-md-6 col-sm-12">
              <div
                className="popular-card card border-0 shadow-lg h-100"
                style={{ borderRadius: "20px", transition: "all 0.3s ease", overflow: "hidden" }}
              >
                <figure className="card-banner position-relative overflow-hidden m-0">
                  <Link to={`/tours/${tour.id}`} className="d-block">
                    <img
                      src={tour.image}
                      className="card-img-top"
                      style={{ height: "280px", objectFit: "cover", transition: "transform 0.3s ease" }}
                      loading="lazy"
                      alt={tour.title}
                      onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.1)")}
                      onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = "/no-image.png";
                      }}
                    />
                  </Link>

                  <span className="card-badge position-absolute top-0 end-0 m-3 bg-primary text-white px-3 py-2 rounded-pill d-flex align-items-center gap-1 shadow">
                    <i className="bi bi-clock" />
                    <time className="small fw-semibold">{tour.durationLabel}</time>
                  </span>
                </figure>

                <div className="card-body p-4">
                  <div className="card-wrapper d-flex justify-content-between align-items-start mb-3">
                    <div className="card-price fw-bold text-primary" style={{ fontSize: "1.3rem" }}>
                      {tour.priceLabel}
                    </div>

                    <div className="card-rating d-flex align-items-center gap-1">
                      <div className="d-flex">{renderStars(tour.rating)}</div>
                      {tour.reviews ? <span className="text-muted small ms-1">({tour.reviews})</span> : null}
                    </div>
                  </div>

                  <h3 className="card-title mb-3" style={{ fontSize: "1.1rem", lineHeight: "1.4" }}>
                    <Link to={`/tours/${tour.id}`} className="text-decoration-none text-dark fw-semibold">
                      {tour.title}
                    </Link>
                  </h3>

                  <address className="card-location text-muted d-flex align-items-center gap-2 mb-0">
                    <i className="bi bi-geo-alt-fill text-danger" />
                    <span className="small">{tour.location}</span>
                  </address>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Nút tới trang tất cả tours */}
        <div className="text-center mt-4">
          <Link to="/tours" className="btn btn-outline-primary rounded-pill px-4">
            Xem tất cả tour
          </Link>
        </div>
      </div>
    </section>
  );
}

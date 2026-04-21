import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { tourService } from "../services/tourService";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

function diffDays(start, end) {
  const s = new Date(start);
  const e = new Date(end);
  const ms = e - s;
  if (isNaN(ms)) return null;
  return Math.max(1, Math.round(ms / (1000 * 60 * 60 * 24)) + 1);
}

export default function PopularTours() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        const { items } = await tourService.getAll({ page: 1, page_size: 6 });
        if (!alive) return;

        const mapped = items.map((t) => ({
          id: t.id,
          title: t.title,
          location: t.location,
          priceLabel:
            typeof t.price === "number" ? `Giá: ${fmtVND.format(t.price)}` : t.price,
          durationLabel: (() => {
            const d = diffDays(t.start_date, t.end_date);
            return d ? `${d} Days` : "Schedule TBA";
          })(),
          rating:
            t.rating !== null && t.rating !== undefined && t.review_count > 0
              ? Number(t.rating)
              : 5.0,
          reviews: Number(t.review_count ?? 0),
          image: t.image_url || "/no-image.png",
        }));

        setTours(mapped);
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => (alive = false);
  }, []);

  const renderStars = (rating) => {
    const r = Math.round(rating);
    return Array.from({ length: 5 }, (_, i) => (
      <i key={i} className={`bi ${i < r ? "bi-star-fill" : "bi-star"} text-warning`} />
    ));
  };

  if (loading) {
    return (
      <section id="tours" className="section popular py-5 bg-white">
        <div className="container text-center">
          <div className="spinner-border text-primary" />
        </div>
      </section>
    );
  }

  return (
    <section id="tours" className="section popular py-5 bg-white">
      <div className="container">
        <div className="text-center mb-5">
          <p className="text-primary text-uppercase small mb-2">Featured Tours</p>
          <h2 className="fw-bold">Most Popular Tours</h2>
        </div>

        <div className="row g-4">
          {tours.map((tour) => (
            <div key={tour.id} className="col-lg-4 col-md-6">
              <div className="card border-0 shadow-sm h-100 rounded-4 overflow-hidden">

                {/* IMAGE */}
                <div
                  style={{
                    height: "280px",
                    background: "#f3f3f3",
                    overflow: "hidden",
                  }}
                >
                  <Link to={`/tours/${tour.id}`}>
                    <img
                      src={tour.image}
                      alt={tour.title}
                      loading="lazy"
                      decoding="async"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        transition: "0.4s ease",
                        filter: "blur(8px)",
                      }}
                      onLoad={(e) => {
                        e.currentTarget.style.filter = "blur(0)";
                      }}
                      onError={(e) => {
                        e.currentTarget.src = "/no-image.png";
                      }}
                    />
                  </Link>
                </div>

                {/* BODY */}
                <div className="card-body p-3">
                  <div className="d-flex justify-content-between mb-2">
                    <strong className="text-primary">{tour.priceLabel}</strong>
                    <div className="small">
                      {renderStars(tour.rating)}{" "}
                      ({tour.reviews})
                    </div>
                  </div>

                  <h6 className="fw-semibold">
                    <Link to={`/tours/${tour.id}`} className="text-dark text-decoration-none">
                      {tour.title}
                    </Link>
                  </h6>

                  <small className="text-muted d-flex align-items-center gap-1">
                    <i className="bi bi-geo-alt-fill text-danger"></i>
                    {tour.location}
                  </small>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-4">
          <Link to="/tours" className="btn btn-outline-primary rounded-pill">
            Xem tất cả tour
          </Link>
        </div>
      </div>
    </section>
  );
}
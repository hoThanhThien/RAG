// src/client/components/Destinations.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, createSearchParams } from "react-router-dom";
import { recommendationService } from "../services/recommendationService";

const MAX_DESTINATIONS = 5;
const ADDRESS_LEVEL_PREFIXES = ["thôn", "xóm", "ấp", "bản", "buôn", "khu phố", "địa phận"];
const DISTRICT_LEVEL_PREFIXES = ["huyện", "quận", "thị xã", "thị trấn"];

const normalizeText = (value) => String(value || "").trim().toLowerCase();

const shouldHideDestination = (name) => {
  const normalizedName = normalizeText(name);
  if (!normalizedName) return true;

  if (ADDRESS_LEVEL_PREFIXES.some((prefix) => normalizedName.startsWith(prefix))) {
    return true;
  }

  if (DISTRICT_LEVEL_PREFIXES.some((prefix) => normalizedName.startsWith(prefix))) {
    return true;
  }

  const segments = String(name)
    .split(",")
    .map((segment) => segment.trim())
    .filter(Boolean);

  if (segments.length >= 4) {
    return true;
  }

  return false;
};

export default function Destinations() {
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const data = await recommendationService.getFeaturedDestinations({
          limit: MAX_DESTINATIONS,
          activeOnly: true,
        });
        if (!alive) return;
        const safeItems = (Array.isArray(data?.items) ? data.items : []).filter(
          (item) => !shouldHideDestination(item?.name)
        );
        setDestinations(safeItems);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const goToLocation = (loc) => {
    // Link tới trang /tours và truyền query location
    navigate({
      pathname: "/tours",
      search: `?${createSearchParams({ location: loc })}`,
    });
  };

  if (loading) {
    return (
      <section id="destinations" className="section destination py-5 bg-light">
        <div className="container text-center">
          <div className="spinner-border text-primary" role="status" />
          <p className="mt-3 text-muted">Đang chọn điểm đến nổi bật…</p>
        </div>
      </section>
    );
  }

  if (destinations.length === 0) {
    return null; // hoặc render trạng thái rỗng tuỳ bạn
  }

  // 2 cái đầu to, các cái sau nhỏ như UI cũ
  const firstTwo = destinations.slice(0, 2);
  const rest = destinations.slice(2);

  return (
    <section id="destinations" className="section destination py-5 bg-light">
      <div className="container">
        <div className="text-center mb-5">
          <p
            className="section-subtitle text-primary mb-2"
            style={{ fontSize: "1rem", letterSpacing: "2px", textTransform: "uppercase" }}
          >
            Destinations
          </p>
          <h2 className="section-title display-5 fw-bold mb-3">Choose Your Place</h2>
        </div>

        <div className="row g-4">
          {firstTwo.map((d) => (
            <div key={d.name} className="col-md-6">
              <button
                type="button"
                onClick={() => goToLocation(d.name)}
                className="destination-card card border-0 shadow-lg overflow-hidden h-100 text-start text-decoration-none w-100"
                style={{ borderRadius: "20px", transition: "all 0.3s ease" }}
              >
                <figure className="card-banner position-relative overflow-hidden m-0" style={{ height: "400px" }}>
                  <img
                    src={d.image}
                    className="img-cover w-100 h-100"
                    style={{ objectFit: "cover", transition: "transform 0.3s ease" }}
                    loading="lazy"
                    alt={d.name}
                    onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
                    onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = "/no-image.png";
                    }}
                  />
                  <div
                    className="position-absolute bottom-0 start-0 w-100 p-4"
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.8))" }}
                  >
                    <div className="card-content text-white">
                      <p className="card-subtitle mb-1 opacity-75 small">{d.name}</p>
                      <h3 className="card-title h4 mb-0 fw-bold">{d.country || d.name}</h3>
                    </div>
                  </div>
                </figure>
              </button>
            </div>
          ))}

          {rest.map((d) => (
            <div key={d.name} className="col-lg-4 col-md-6">
              <button
                type="button"
                onClick={() => goToLocation(d.name)}
                className="destination-card card border-0 shadow-lg overflow-hidden h-100 text-start text-decoration-none w-100"
                style={{ borderRadius: "20px", transition: "all 0.3s ease" }}
              >
                <figure className="card-banner position-relative overflow-hidden m-0" style={{ height: "280px" }}>
                  <img
                    src={d.image}
                    className="img-cover w-100 h-100"
                    style={{ objectFit: "cover", transition: "transform 0.3s ease" }}
                    loading="lazy"
                    alt={d.name}
                    onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
                    onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = "/no-image.png";
                    }}
                  />
                  <div
                    className="position-absolute bottom-0 start-0 w-100 p-3"
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.8))" }}
                  >
                    <div className="card-content text-white">
                      <p className="card-subtitle mb-1 opacity-75 small">{d.name}</p>
                      <h3 className="card-title h6 mb-0 fw-bold">{d.country || d.name}</h3>
                    </div>
                  </div>
                </figure>
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

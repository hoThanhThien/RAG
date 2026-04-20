import React, { useEffect, useRef, useState } from "react";

export default function Hero() {
  const slides = [
    {
      image: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
      place: "Thụy Sĩ",
      title: "Chạm tới bình minh trên dãy Alps",
      subtitle: "Hành trình thư giãn, cảnh sắc điện ảnh và trải nghiệm cao cấp.",
    },
    {
      image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
      place: "Maldives",
      title: "Kỳ nghỉ biển sang trọng và riêng tư",
      subtitle: "Biển xanh, resort đẹp và lịch trình tối ưu cho cặp đôi, gia đình.",
    },
    {
      image: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
      place: "Na Uy",
      title: "Săn cảnh sắc Bắc Âu đầy mê hoặc",
      subtitle: "Những điểm đến nổi bật được chọn lọc cho chuyến đi đáng nhớ.",
    },
  ];

  const [active, setActive] = useState(0);
  const timerRef = useRef(null);

  const next = () => setActive((p) => (p + 1) % slides.length);
  const prev = () => setActive((p) => (p - 1 + slides.length) % slides.length);

  const startAuto = () => {
    stopAuto();
    timerRef.current = setInterval(next, 5000);
  };

  const stopAuto = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  useEffect(() => {
    startAuto();
    return stopAuto;
  }, []);

  const current = slides[active];

  return (
    <section id="home" className="hero-section d-flex align-items-center">
      <div className="floating-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
        <div className="shape shape-5"></div>
      </div>

      <div className="container">
        <div className="row align-items-center gy-5">
          {/* LEFT */}
          <div className="col-lg-6 text-white">
            <div className="hero-content">
              <div className="hero-badge mb-3">
                <i className="bi bi-stars"></i>
                <span>Tour tuyển chọn • Trải nghiệm tinh gọn</span>
              </div>

              <h1 className="hero-title mb-3">
                Du lịch đẹp hơn, dễ chọn hơn, đáng nhớ hơn
              </h1>

              <p className="hero-text mb-4">
                Khám phá những hành trình được thiết kế chỉn chu với lịch trình hợp lý,
                điểm đến nổi bật và mức giá rõ ràng cho chuyến đi tiếp theo của bạn.
              </p>

              <div className="hero-buttons d-flex gap-3 mb-4">
                <a href="#tours" className="btn-hero btn-primary-glow">
                  Khám phá tour
                </a>
                <a href="#about" className="btn-hero btn-secondary-glow">
                  Xem thêm
                </a>
              </div>

              <div className="hero-metrics">
                <div className="metric-card">
                  <strong>500+</strong>
                  <span>Hành trình nổi bật</span>
                </div>
                <div className="metric-card">
                  <strong>24/7</strong>
                  <span>Hỗ trợ nhanh</span>
                </div>
                <div className="metric-card">
                  <strong>4.9/5</strong>
                  <span>Khách hàng hài lòng</span>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT */}
          <div className="col-lg-6 d-none d-lg-block">
            <div
              className="hero-banner carousel-card"
              onMouseEnter={stopAuto}
              onMouseLeave={startAuto}
            >
              <div className="slides-wrap">
                {slides.map((slide, i) => (
                  <img
                    key={i}
                    src={slide.image}
                    alt=""
                    className={`slide ${i === active ? "active" : ""}`}
                  />
                ))}
              </div>

              <div className="slide-overlay">
                <span className="slide-place">{current.place}</span>
                <h3>{current.title}</h3>
                <p>{current.subtitle}</p>
              </div>

              <button className="nav prev" onClick={prev}>‹</button>
              <button className="nav next" onClick={next}>›</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
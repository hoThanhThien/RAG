import React, { useEffect, useRef, useState } from "react";

const HEADER_H = 80;

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
  const goTo = (i) => setActive(i);

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
    <section
      id="home"
      className="hero-section d-flex align-items-center"
      style={{
        background: "linear-gradient(135deg, #5b63f6 0%, #7b4cc2 50%, #5d4fd8 100%)",
        minHeight: "100vh",
        marginTop: `-${HEADER_H}px`,
        paddingTop: `${HEADER_H}px`,
        paddingBottom: "32px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div className="floating-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
        <div className="shape shape-5"></div>
      </div>

      <div className="container">
        <div className="row align-items-center gy-5">
          <div className="col-lg-6 text-white">
            <div className="hero-content">
              <div className="hero-badge mb-3">
                <i className="bi bi-stars"></i>
                <span>Tour tuyển chọn • Trải nghiệm tinh gọn</span>
              </div>

              <h1 className="hero-title mb-3">Du lịch đẹp hơn, dễ chọn hơn, đáng nhớ hơn</h1>

              <p className="hero-text mb-4">
                Khám phá những hành trình được thiết kế chỉn chu với lịch trình hợp lý,
                điểm đến nổi bật và mức giá rõ ràng cho chuyến đi tiếp theo của bạn.
              </p>

              <div className="hero-buttons d-flex flex-column flex-sm-row gap-3 mb-4">
                <a href="#tours" className="btn-hero btn-primary-glow text-decoration-none">
                  <span>Khám phá tour</span>
                  <i className="bi bi-arrow-right"></i>
                </a>
                <a href="#about" className="btn-hero btn-secondary-glow text-decoration-none">
                  <span>Xem thêm</span>
                  <i className="bi bi-play-circle"></i>
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

          <div className="col-lg-6 d-none d-lg-block">
            <div
              className="hero-banner carousel-card"
              onMouseEnter={stopAuto}
              onMouseLeave={startAuto}
            >
              <div className="slides-wrap">
                {slides.map((slide, i) => (
                  <img
                    key={slide.image}
                    src={slide.image}
                    alt={slide.title}
                    className={`slide ${i === active ? "active" : ""}`}
                    loading="lazy"
                  />
                ))}
              </div>

              <div className="slide-overlay">
                <span className="slide-place">{current.place}</span>
                <h3>{current.title}</h3>
                <p>{current.subtitle}</p>
              </div>

              <div className="hero-float-card">
                <i className="bi bi-geo-alt-fill"></i>
                <div>
                  <strong>Điểm đến nổi bật</strong>
                  <span>Cập nhật liên tục mỗi tuần</span>
                </div>
              </div>

              <button className="nav prev" aria-label="Previous" onClick={prev}>
                ‹
              </button>
              <button className="nav next" aria-label="Next" onClick={next}>
                ›
              </button>

              <div className="dots">
                {slides.map((_, i) => (
                  <button
                    key={i}
                    className={`dot ${i === active ? "active" : ""}`}
                    onClick={() => goTo(i)}
                    aria-label={`Go to slide ${i + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="scroll-indicator position-absolute bottom-0 start-50 translate-middle-x mb-4">
          <div className="scroll-mouse">
            <div className="scroll-wheel"></div>
          </div>
          <span className="scroll-text text-white small">Scroll Down</span>
        </div>
      </div>
    </section>
  );
}

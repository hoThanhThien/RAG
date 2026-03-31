import React, { useEffect, useRef, useState } from "react";

const HEADER_H = 80; // phải khớp với ClientLayout

export default function Hero() {
  // ===== Slides cho banner (có thể sửa URL tuỳ ý) =====
  const slides = [
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1559827260-dc66d52bef19?auto=format&fit=crop&w=1600&q=80",
  ];

  const [active, setActive] = useState(0);
  const timerRef = useRef(null);

  const next = () => setActive((p) => (p + 1) % slides.length);
  const prev = () => setActive((p) => (p - 1 + slides.length) % slides.length);
  const goTo = (i) => setActive(i);

  const startAuto = () => {
    stopAuto();
    timerRef.current = setInterval(next, 5000); // 5s đổi ảnh
  };
  const stopAuto = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  useEffect(() => {
    startAuto();
    return stopAuto;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section
      id="home"
      className="hero-section d-flex align-items-center"
      style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        // Chiếm full viewport
        minHeight: "100vh",
        // Kéo section lên để không bị đẩy xuống
        marginTop: `-${HEADER_H}px`,
        // Bù lại phần bị header che
        paddingTop: `${HEADER_H}px`,
        // Thêm chút khoảng thở dưới cho đẹp
        paddingBottom: "24px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Floating Shapes */}
      <div className="floating-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
        <div className="shape shape-5"></div>
      </div>

      <div className="container">
        <div className="row align-items-center">
          {/* Left content */}
          <div className="col-lg-6 text-white">
            <div className="hero-content">
              <p
                className="section-subtitle mb-3"
                style={{
                  fontSize: "1.1rem",
                  letterSpacing: "3px",
                  textTransform: "uppercase",
                  opacity: "0.9",
                  fontWeight: "500",
                }}
              >
                KHÁM PHÁ CHUYẾN DU LỊCH CỦA BẠN
              </p>

              <h1
                className="hero-title mb-4"
                style={{
                  fontSize: "clamp(2.5rem, 6vw, 5rem)",
                  fontWeight: "800",
                  lineHeight: "1.1",
                  background:
                    "linear-gradient(45deg, #ffffff, #f8f9fa, #e9ecef)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  textShadow: "0 0 30px rgba(255,255,255,0.5)",
                }}
              >
               Khám phá thế giới
              </h1>

              <p
                className="hero-text mb-5"
                style={{
                  fontSize: "1.3rem",
                  opacity: "0.9",
                  lineHeight: "1.6",
                  fontWeight: "300",
                }}
              >
                Cuộc phiêu lưu của bạn bắt đầu từ đây. Khám phá những điểm đến ngoạn mục và tạo nên những kỷ niệm khó quên với những trải nghiệm du lịch được thiết kế chuyên nghiệp của chúng tôi.
              </p>

              <div className="hero-buttons d-flex flex-column flex-sm-row gap-4">
                <a
                  href="#tours"
                  className="btn-hero btn-primary-glow text-decoration-none"
                >
                  <span>Explore Tours</span>
                  <i className="bi bi-arrow-right ms-2"></i>
                </a>
                <a
                  href="#about"
                  className="btn-hero btn-secondary-glow text-decoration-none"
                >
                  <span>Learn More</span>
                  <i className="bi bi-play-circle ms-2"></i>
                </a>
              </div>
            </div>
          </div>

          {/* Right banner: CAROUSEL */}
          <div className="col-lg-6 d-none d-lg-block">
            <div
              className="hero-banner carousel-card"
              onMouseEnter={stopAuto}
              onMouseLeave={startAuto}
            >
              <div className="slides-wrap">
                {slides.map((src, i) => (
                  <img
                    key={src}
                    src={src}
                    alt={`slide-${i}`}
                    className={`slide ${i === active ? "active" : ""}`}
                    loading="lazy"
                  />
                ))}
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

        {/* Scroll Indicator */}
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

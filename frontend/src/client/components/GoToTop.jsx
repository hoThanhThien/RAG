import React, { useEffect } from 'react';

export default function GoToTop() {
  useEffect(() => {
    const goTopBtn = document.querySelector('[data-go-top]');

    const handleScroll = () => {
      if (goTopBtn) {
        if (window.scrollY > 100) {
          goTopBtn.classList.add('active');
        } else {
          goTopBtn.classList.remove('active');
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // ✅ Inline CSS object cho hiệu ứng go-top
  const style = {
    bottom: '20px',
    right: '20px',
    width: '50px',
    height: '50px',
    zIndex: 1000,
    opacity: 0,
    visibility: 'hidden',
    transition: 'all 0.3s ease'
  };

  // ✅ Inject CSS thủ công nếu vẫn muốn .go-top.active có hiệu ứng
  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      .go-top.active {
        opacity: 1 !important;
        visibility: visible !important;
      }

      .go-top:hover {
        transform: translateY(-3px);
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <button
      onClick={scrollToTop}
      className="go-top position-fixed btn btn-primary rounded-circle shadow-lg d-flex align-items-center justify-content-center"
      data-go-top
      aria-label="Go To Top"
      style={style}
    >
      <i className="bi bi-chevron-up" style={{ fontSize: '1.2rem' }}></i>
    </button>
  );
}

import React from 'react'

export default function Footer() {
  const footerData = {
    topDestinations: [
      'Indonesia, Jakarta',
      'Maldives, Malé', 
      'Australia, Canberra',
      'Thailand, Bangkok',
      'Morocco, Rabat'
    ],
    categories: [
      'Travel',
      'Lifestyle', 
      'Fashion',
      'Education',
      'Food & Drink'
    ],
    quickLinks: [
      'About',
      'Contact',
      'Tours', 
      'Booking',
      'Terms & Conditions'
    ],
    socialLinks: [
      { icon: 'bi-facebook', name: 'facebook' },
      { icon: 'bi-twitter', name: 'twitter' },
      { icon: 'bi-instagram', name: 'instagram' },
      { icon: 'bi-linkedin', name: 'linkedin' },
      { icon: 'bi-google', name: 'google' }
    ]
  }

  return (
    <footer className="footer bg-dark text-light py-5" style={{
      backgroundImage: `linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1920&q=80')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }}>
      <div className="container">
        
        <div className="footer-top row g-4 mb-5">
          
          {/* Top Destinations */}
          <div className="col-lg-3 col-md-6">
            <div className="footer-list">
              <p className="footer-list-title h6 fw-bold mb-3 text-primary">Top destination</p>
              <ul className="list-unstyled">
                {footerData.topDestinations.map((destination, index) => (
                  <li key={index} className="mb-2">
                    <a href="#" className="footer-link text-light text-decoration-none small opacity-75">
                      {destination}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Categories */}
          <div className="col-lg-3 col-md-6">
            <div className="footer-list">
              <p className="footer-list-title h6 fw-bold mb-3 text-primary">Categories</p>
              <ul className="list-unstyled">
                {footerData.categories.map((category, index) => (
                  <li key={index} className="mb-2">
                    <a href="#" className="footer-link text-light text-decoration-none small opacity-75">
                      {category}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Quick Links */}
          <div className="col-lg-3 col-md-6">
            <div className="footer-list">
              <p className="footer-list-title h6 fw-bold mb-3 text-primary">Quick links</p>
              <ul className="list-unstyled">
                {footerData.quickLinks.map((link, index) => (
                  <li key={index} className="mb-2">
                    <a href="#" className="footer-link text-light text-decoration-none small opacity-75">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Newsletter */}
          <div className="col-lg-3 col-md-6">
            <div className="footer-list">
              <p className="footer-list-title h6 fw-bold mb-3 text-primary">Get a newsletter</p>
              
              <p className="newsletter-text small text-light opacity-75 mb-4">
                For the latest deals and tips, travel no further than your inbox
              </p>

              <form className="newsletter-form">
                <div className="input-group mb-3">
                  <input 
                    type="email" 
                    name="email" 
                    required 
                    placeholder="Email address" 
                    className="form-control newsletter-input bg-transparent border-light text-light"
                    style={{borderRadius: '25px 0 0 25px'}}
                  />
                  <button 
                    type="submit" 
                    className="btn btn-primary px-4"
                    style={{borderRadius: '0 25px 25px 0'}}
                  >
                    Subscribe
                  </button>
                </div>
              </form>

            </div>
          </div>

        </div>

        {/* Footer Bottom */}
        <div className="footer-bottom border-top border-secondary pt-4">
          <div className="row align-items-center">
            
            <div className="col-md-4 mb-3 mb-md-0">
              <a href="#" className="logo text-decoration-none">
                <h4 className="text-primary fw-bold">Tourest</h4>
              </a>
            </div>

            <div className="col-md-4 mb-3 mb-md-0 text-center">
              <p className="copyright mb-0 small text-light opacity-75">
                © 2025 <a href="#" className="text-primary text-decoration-none">Tourest</a>. All Rights Reserved
              </p>
            </div>

            <div className="col-md-4">
              <ul className="social-list d-flex justify-content-md-end justify-content-center gap-2 list-unstyled mb-0">
                {footerData.socialLinks.map((social, index) => (
                  <li key={index}>
                    <a 
                      href="#" 
                      className="social-link d-flex align-items-center justify-content-center bg-primary text-white rounded-circle text-decoration-none"
                      style={{width: '36px', height: '36px'}}
                    >
                      <i className={social.icon}></i>
                    </a>
                  </li>
                ))}
              </ul>
            </div>

          </div>
        </div>

      </div>
    </footer>
  )
}

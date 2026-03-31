import React, { useState, useEffect } from 'react'

export default function Blog() {
  const [blogs, setBolgs] = useState([])

  useEffect(() => {
    setBolgs([
      {
        id: 1,
        title: 'A good traveler has no fixed plans and is not intent on arriving.',
        author: 'Jony bristow',
        authorTitle: 'Admin',
        publishTime: '10:30 AM',
        date: '04 Dec',
        image: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?auto=format&fit=crop&w=740&h=518&q=80',
        authorAvatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=30&h=30&q=80'
      },
      {
        id: 2,
        title: 'Ultimate Vietnam Travel Guide for Adventurers',
        author: 'Sarah Johnson',
        authorTitle: 'Admin',
        publishTime: '09:15 AM',
        date: '03 Dec',
        image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=740&h=518&q=80',
        authorAvatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=30&h=30&q=80'
      },
      {
        id: 3,
        title: 'Hidden Gems in Southeast Asia You Must Visit',
        author: 'Mike Chen',
        authorTitle: 'Admin',
        publishTime: '08:45 AM',
        date: '02 Dec',
        image: 'https://images.unsplash.com/photo-1583417267826-aebc4d1542e1?auto=format&fit=crop&w=740&h=518&q=80',
        authorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=30&h=30&q=80'
      }
    ])
  }, [])

  return (
    <section id="blog" className="section blog py-5 bg-white">
      <div className="container">
        
        <div className="text-center mb-5">
          <p className="section-subtitle text-primary mb-2" style={{fontSize: '1rem', letterSpacing: '2px', textTransform: 'uppercase'}}>
            From The Blog Post
          </p>
          <h2 className="section-title display-5 fw-bold mb-3">Latest News & Articles</h2>
        </div>

        <div className="row g-4">
          {blogs.map((blog) => (
            <div key={blog.id} className="col-lg-4 col-md-6">
              <div className="blog-card card border-0 shadow-sm h-100">
                
                <figure className="card-banner position-relative overflow-hidden">
                  <a href="#">
                    <img 
                      src={blog.image} 
                      className="card-img-top"
                      style={{height: '250px', objectFit: 'cover', transition: 'transform 0.3s ease'}}
                      loading="lazy" 
                      alt={blog.title}
                      onMouseOver={e => e.target.style.transform = 'scale(1.05)'}
                      onMouseOut={e => e.target.style.transform = 'scale(1)'}
                    />
                  </a>

                  <span className="card-badge position-absolute top-0 end-0 m-3 bg-primary text-white px-3 py-2 rounded-pill d-flex align-items-center gap-1">
                    <i className="bi bi-clock"></i>
                    <time>{blog.date}</time>
                  </span>
                </figure>

                <div className="card-body p-4">
                  
                  <div className="card-wrapper d-flex justify-content-between align-items-center mb-3">
                    
                    <div className="author-wrapper d-flex align-items-center">
                      <figure className="author-avatar me-2">
                        <img 
                          src={blog.authorAvatar} 
                          width="30" 
                          height="30" 
                          alt={blog.author}
                          className="rounded-circle"
                        />
                      </figure>

                      <div>
                        <a href="#" className="author-name text-decoration-none text-dark fw-semibold small">
                          {blog.author}
                        </a>
                        <p className="author-title text-muted small mb-0">
                          {blog.authorTitle}
                        </p>
                      </div>
                    </div>

                    <time className="publish-time text-muted small">
                      {blog.publishTime}
                    </time>

                  </div>

                  <h3 className="card-title mb-3">
                    <a href="#" className="text-decoration-none text-dark fw-semibold">
                      {blog.title}
                    </a>
                  </h3>

                  <a href="#" className="btn-link text-primary text-decoration-none fw-semibold d-flex align-items-center gap-2">
                    <span>Read More</span>
                    <i className="bi bi-arrow-right"></i>
                  </a>

                </div>

              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}

import React from "react";

export default function Contact() {
  return (
    <div className="container py-5" style={{ minHeight: "70vh" }}>
      <h2 className="mb-4">Contact Us</h2>
      <p className="text-muted mb-4">We'd love to hear from you!</p>

      <form className="row g-3">
        <div className="col-md-6">
          <label className="form-label">Name</label>
          <input type="text" className="form-control" placeholder="Your name" required />
        </div>
        <div className="col-md-6">
          <label className="form-label">Email</label>
          <input type="email" className="form-control" placeholder="you@example.com" required />
        </div>
        <div className="col-12">
          <label className="form-label">Subject</label>
          <input type="text" className="form-control" placeholder="Subject..." required />
        </div>
        <div className="col-12">
          <label className="form-label">Message</label>
          <textarea className="form-control" rows="5" placeholder="Your message..." required></textarea>
        </div>
        <div className="col-12">
          <button type="submit" className="btn btn-primary px-4">Send Message</button>
        </div>
      </form>
    </div>
  );
}

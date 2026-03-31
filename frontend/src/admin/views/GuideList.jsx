import React, { useEffect, useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

export default function GuideList() {
  const [guides, setGuides] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/guides')
      .then(res => res.json())
      .then(setGuides);
  }, []);

  return (
    <div className="container py-5">
      <h2 className="mb-4 text-center">Danh sách Hướng dẫn viên</h2>
      <div className="row justify-content-center">
        {guides.map(g => (
          <div className="col-md-4 mb-4" key={g.guide_id}>
            <div className="card shadow border-0 h-100">
              <img src={`https://randomuser.me/api/portraits/men/${g.guide_id}.jpg`} className="card-img-top" alt={g.name} />
              <div className="card-body text-center">
                <h5 className="card-title">{g.name}</h5>
                <p className="card-text">Hướng dẫn viên chuyên nghiệp, tận tâm và giàu kinh nghiệm.</p>
                <button className="btn btn-primary">Xem chi tiết</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

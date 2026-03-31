import React, { useEffect, useState } from 'react';
import { fetchTourGuides } from '../services/tourGuideService';

export default function TourGuideList() {
  const [tourGuides, setTourGuides] = useState([]);
  useEffect(() => {
    fetchTourGuides().then(setTourGuides);
  }, []);
  return (
    <div>
      <h2>Tour Guide List</h2>
      <ul>
        {tourGuides.map(tg => <li key={tg.tour_id + '-' + tg.guide_id}>{tg.tour_id} - {tg.guide_id}</li>)}
      </ul>
    </div>
  );
}

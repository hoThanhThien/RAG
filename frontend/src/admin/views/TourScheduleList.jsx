import React, { useEffect, useState } from 'react';
import { fetchTourSchedules } from '../services/tourscheduleService';

export default function TourScheduleList() {
  const [schedules, setSchedules] = useState([]);
  useEffect(() => {
    fetchTourSchedules().then(setSchedules);
  }, []);
  return (
    <div>
      <h2>Tour Schedule List</h2>
      <ul>
        {schedules.map(s => <li key={s.schedule_id}>{s.day_number}</li>)}
      </ul>
    </div>
  );
}

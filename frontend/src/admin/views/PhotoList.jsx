import React, { useEffect, useState } from 'react';
import { fetchPhotos } from '../services/photoService';

export default function PhotoList() {
  const [photos, setPhotos] = useState([]);
  useEffect(() => {
    fetchPhotos().then(setPhotos);
  }, []);
  return (
    <div>
      <h2>Photo List</h2>
      <ul>
        {photos.map(p => <li key={p.photo_id}>{p.image_url}</li>)}
      </ul>
    </div>
  );
}

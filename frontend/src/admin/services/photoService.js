export async function fetchPhotos() {
  const response = await fetch('/api/photos');
  return response.json();
}

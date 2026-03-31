export async function fetchTourGuides() {
  const response = await fetch('/api/tour_guides');
  return response.json();
}

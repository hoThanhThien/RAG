export async function fetchTourSchedules() {
  const response = await fetch('/api/tourschedules');
  return response.json();
}

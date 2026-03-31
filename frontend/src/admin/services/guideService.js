export async function fetchGuides() {
  const response = await fetch('/api/guides');
  return response.json();
}

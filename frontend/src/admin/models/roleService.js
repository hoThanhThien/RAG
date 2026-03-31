export async function fetchRoles() {
  const response = await fetch('/api/roles');
  return response.json();
}

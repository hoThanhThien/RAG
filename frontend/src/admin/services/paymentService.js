// Payment service for FE
export async function fetchPayments() {
  const response = await fetch('/api/payments');
  return response.json();
}

# PayPal Integration Setup

This document describes how to set up PayPal payment integration for the Tour Booking system.

## Required Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# PayPal Configuration
PAYPAL_MODE=sandbox  # Use "sandbox" for testing, "live" for production
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here

# Exchange Rate API (Optional)
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here  # Get free key from exchangerate-api.com
```

## Database Migration

Run the following SQL script to add PayPal support columns to the payment table:

```sql
USE tourbookingdb;

-- Add PayPal specific columns to payment table
ALTER TABLE `payment` 
ADD COLUMN `PaidAt` DATETIME NULL DEFAULT NULL AFTER `Status`,
ADD COLUMN `PaypalOrderID` VARCHAR(255) NULL DEFAULT NULL AFTER `PaidAt`,
ADD COLUMN `PaypalTransactionID` VARCHAR(255) NULL DEFAULT NULL AFTER `PaypalOrderID`,
ADD COLUMN `UpdatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `PaypalTransactionID`;

-- Add indexes for faster lookups
CREATE INDEX `idx_paypal_order_id` ON `payment` (`PaypalOrderID`);
CREATE INDEX `idx_paypal_transaction_id` ON `payment` (`PaypalTransactionID`);
```

## API Endpoints

### 1. Create PayPal Payment
**POST** `/api/payments/paypal/create`

Request body:
```json
{
  "booking_id": 123
}
```

Response:
```json
{
  "orderID": "8X012345AB678901C",
  "amount_vnd": 5000000.0,
  "amount_usd": 200.00,
  "exchange_rate": 25000.0
}
```

### 2. Capture PayPal Payment
**POST** `/api/payments/paypal/capture`

Request body:
```json
{
  "orderID": "8X012345AB678901C",
  "bookingID": 123
}
```

Response:
```json
{
  "status": "success",
  "payment_id": "8X012345AB678901C",
  "transaction_id": "1234567890ABCDEF",
  "booking_status": "Confirmed"
}
```

## Frontend Integration

The backend is designed to work with PayPal JavaScript SDK on the frontend. Example frontend code:

```javascript
// Create order
const createOrder = async (bookingId) => {
  const response = await fetch('/api/payments/paypal/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ booking_id: bookingId })
  });
  const data = await response.json();
  return data.orderID;
};

// Approve payment
const onApprove = async (data) => {
  const response = await fetch('/api/payments/paypal/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      orderID: data.orderID, 
      bookingID: currentBookingId 
    })
  });
  const result = await response.json();
  if (result.status === 'success') {
    // Redirect to success page
    window.location.href = '/booking-success';
  }
};
```

## Exchange Rate Service

The system automatically converts VND prices to USD using:
1. Real-time exchange rates from exchangerate-api.com (if API key provided)
2. Fallback to a fixed rate of 25,000 VND = 1 USD

## Testing

1. Use PayPal sandbox credentials for testing
2. Create test accounts at developer.paypal.com
3. Use sandbox buyer accounts to test payments

## Security Notes

- All PayPal credentials should be kept secure in environment variables
- The system validates user permissions before creating/capturing payments
- Transaction IDs are stored for audit purposes
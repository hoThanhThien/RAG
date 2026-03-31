import React, { useEffect, useState } from 'react';
import { fetchPayments } from '../services/paymentService';

export default function PaymentList() {
  const [payments, setPayments] = useState([]);
  useEffect(() => {
    fetchPayments().then(setPayments);
  }, []);
  return (
    <div>
      <h2>Payment List</h2>
      <ul>
        {payments.map(p => <li key={p.payment_id}>{p.amount}</li>)}
      </ul>
    </div>
  );
}

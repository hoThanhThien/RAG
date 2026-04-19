// src/client/components/PayPalButton.jsx
import React, { useEffect, useRef } from "react";
import { PayPalService } from "../services/paypalService";

const PayPalButton = ({ bookingId, onSuccess, onError, onCancel }) => {
  const paypalRef = useRef(null);
  const isRendered = useRef(false);

  useEffect(() => {
    if (!window.paypal || !bookingId || isRendered.current) {
      return;
    }

    const renderPayPalButton = () => {
      // Clear container trước khi render
      if (paypalRef.current) {
        paypalRef.current.innerHTML = '';
      }

      window.paypal.Buttons({
        createOrder: async () => {
          try {
            console.log("[PayPal Button] Creating order for booking:", bookingId);
            
            const response = await PayPalService.createPayPalOrder(bookingId);
            console.log("[PayPal Button] Order response:", response);

            if (!response) {
              throw new Error("Order ID not received from server");
            }

            return response;
          } catch (error) {
            console.error("[PayPal Button] Error creating order:", error);
            const message = PayPalService.handlePaymentError(error);
            if (onError) onError(message);
            throw error;
          }
        },

        onApprove: async (data) => {
          try {
            console.log("[PayPal Button] Payment approved, capturing order:", data.orderID);
            
            const captureResponse = await PayPalService.capturePayPalPayment(data.orderID, bookingId);
            console.log("[PayPal Button] Payment captured:", captureResponse);
            
            if (onSuccess) {
              await Promise.resolve(onSuccess(captureResponse));
            }

            return captureResponse;
          } catch (error) {
            console.error("[PayPal Button] Error capturing payment:", error);
            const message = PayPalService.handlePaymentError(error);
            if (onError) onError(message);
            throw error;
          }
        },

        onError: (err) => {
          console.error("[PayPal Button] Payment error:", err);
          const message = PayPalService.handlePaymentError(err);
          if (onError) onError(message);
        },

        onCancel: (data) => {
          console.log("[PayPal Button] Payment cancelled:", data);
          if (onCancel) onCancel(data);
        }
      }).render(paypalRef.current);

      isRendered.current = true;
    };

    renderPayPalButton();

    // Cleanup function
    return () => {
      if (paypalRef.current) {
        paypalRef.current.innerHTML = '';
      }
      isRendered.current = false;
    };
  }, [bookingId]);

  return (
    <div>
      <div ref={paypalRef}></div>
    </div>
  );
};

export default PayPalButton;
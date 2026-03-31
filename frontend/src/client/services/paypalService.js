// src/client/services/paypalService.js

// Thay thế dòng code cũ của bạn bằng logic if/else
const API_BASE_URL = import.meta.env.PROD
  ? 'https://52.64.184.203:8000'
  : 'http://52.64.184.203:8000'



export class PayPalService {
  /**
   * Tạo PayPal order thông qua backend
   * @param {number} bookingId - ID của booking cần thanh toán
   * @returns {Promise<string>} - PayPal Order ID
   */
  static async createPayPalOrder(bookingId) {
    try {
      const token = localStorage.getItem('access_token');
      console.log('PayPal Service - Token found:', !!token, 'BookingId:', bookingId); // Debug log
      if (!token) {
        throw new Error('Bạn cần đăng nhập để thực hiện thanh toán');
      }

      const response = await fetch(`${API_BASE_URL}/payments/paypal/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ booking_id: bookingId })
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          console.error('Failed to parse error response:', e);
        }
        console.error('PayPal API Error:', {
          status: response.status,
          statusText: response.statusText,
          url: `${API_BASE_URL}/payments/paypal/create`,
          bookingId,
          errorMessage
        });
        throw new Error(errorMessage);
      }

      const data = await response.json();
      return data.orderID;
    } catch (error) {
      console.error('Lỗi khi tạo PayPal order:', error);
      throw error;
    }
  }

  /**
   * Xác nhận thanh toán PayPal thông qua backend
   * @param {string} orderID - PayPal Order ID
   * @param {number} bookingID - ID của booking
   * @returns {Promise<Object>} - Kết quả thanh toán
   */
  static async capturePayPalPayment(orderID, bookingID) {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Bạn cần đăng nhập để thực hiện thanh toán');
      }

      const response = await fetch(`${API_BASE_URL}/payments/paypal/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          orderID: orderID, 
          bookingID: bookingID 
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Không thể xác nhận thanh toán');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Lỗi khi capture PayPal payment:', error);
      throw error;
    }
  }

  /**
   * Xử lý lỗi thanh toán
   * @param {Error} error - Lỗi từ PayPal hoặc backend
   * @returns {string} - Thông báo lỗi người dùng có thể hiểu
   */
  static handlePaymentError(error) {
    if (error.message.includes('INSTRUMENT_DECLINED')) {
      return 'Phương thức thanh toán bị từ chối. Vui lòng thử phương thức khác.';
    } else if (error.message.includes('INSUFFICIENT_FUNDS')) {
      return 'Tài khoản không đủ số dư. Vui lòng kiểm tra lại.';
    } else if (error.message.includes('INVALID_REQUEST')) {
      return 'Yêu cầu không hợp lệ. Vui lòng thử lại.';
    } else if (error.message.includes('NETWORK')) {
      return 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
    } else {
      return error.message || 'Đã xảy ra lỗi trong quá trình thanh toán. Vui lòng thử lại.';
    }
  }
}

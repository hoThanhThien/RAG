// src/client/services/paypalService.js
import { api } from "./api";

const getErrorMessage = (error) =>
  error?.response?.data?.detail ||
  error?.response?.data?.message ||
  error?.message ||
  "Đã xảy ra lỗi trong quá trình thanh toán.";



export class PayPalService {
  /**
   * Tạo PayPal order thông qua backend
   * @param {number} bookingId - ID của booking cần thanh toán
   * @returns {Promise<string>} - PayPal Order ID
   */
  static async createPayPalOrder(bookingId) {
    try {
      const token = localStorage.getItem('access_token');
      console.log('PayPal Service - Token found:', !!token, 'BookingId:', bookingId);
      if (!token) {
        throw new Error('Bạn cần đăng nhập để thực hiện thanh toán');
      }

      const { data } = await api.post('/payments/paypal/create', {
        booking_id: bookingId,
      });

      return data?.orderID;
    } catch (error) {
      console.error('Lỗi khi tạo PayPal order:', error);
      throw new Error(getErrorMessage(error));
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

      const { data } = await api.post('/payments/paypal/capture', {
        orderID,
        bookingID,
      });

      return data;
    } catch (error) {
      console.error('Lỗi khi capture PayPal payment:', error);
      throw new Error(getErrorMessage(error));
    }
  }

  /**
   * Xử lý lỗi thanh toán
   * @param {Error} error - Lỗi từ PayPal hoặc backend
   * @returns {string} - Thông báo lỗi người dùng có thể hiểu
   */
  static handlePaymentError(error) {
    const message = getErrorMessage(error);

    if (message.includes('INSTRUMENT_DECLINED')) {
      return 'Phương thức thanh toán bị từ chối. Vui lòng thử phương thức khác.';
    } else if (message.includes('INSUFFICIENT_FUNDS')) {
      return 'Tài khoản không đủ số dư. Vui lòng kiểm tra lại.';
    } else if (message.includes('INVALID_REQUEST')) {
      return 'Yêu cầu không hợp lệ. Vui lòng thử lại.';
    } else if (message.includes('NETWORK') || message.includes('Failed to fetch')) {
      return 'Không kết nối được máy chủ thanh toán. Vui lòng thử lại.';
    } else {
      return message;
    }
  }
}

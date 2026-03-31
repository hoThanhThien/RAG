import axios from 'axios';

// Thay thế dòng code cũ của bạn bằng dòng này
const API_URL = import.meta.env.PROD
  ? 'http:52.64.184.203:8000/payments' // 👈 Giá trị khi chạy trên HOSTING
  : 'http://52.64.184.203:8000/payments';

/**
 * Tạo payment request với MoMo
 * @param {number} bookingID - ID của booking cần thanh toán
 * @param {string} paymentMethod - Phương thức thanh toán (captureWallet, payWithATM)
 * @returns {Promise} - Promise chứa thông tin payment (payUrl, orderId, amount)
 */
export const createMoMoPayment = async (bookingID, paymentMethod = 'captureWallet') => {
    try {
        const token = localStorage.getItem('access_token');
        const response = await axios.post(
            `${API_URL}/momo/create`,
            { 
                bookingID,
                paymentMethod 
            },
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error creating MoMo payment:', error);
        throw error.response?.data || error.message;
    }
};

/**
 * Xử lý callback từ MoMo sau khi user thanh toán
 * @param {URLSearchParams} searchParams - Query parameters từ MoMo callback
 * @returns {Object} - Thông tin kết quả thanh toán
 */
export const handleMoMoCallback = (searchParams) => {
    const resultCode = parseInt(searchParams.get('resultCode'));
    const orderId = searchParams.get('orderId');
    const transId = searchParams.get('transId');
    const amount = parseInt(searchParams.get('amount'));
    const message = searchParams.get('message');

    return {
        success: resultCode === 0,
        orderId,
        transId,
        amount,
        message,
        resultCode
    };
};

/**
 * Format số tiền VND
 * @param {number} amount - Số tiền cần format
 * @returns {string} - Chuỗi đã format (ví dụ: "1.000.000 ₫")
 */
export const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
};

/**
 * Lấy danh sách phương thức thanh toán MoMo khả dụng
 * @returns {Promise} - Promise chứa thông tin về các phương thức thanh toán
 */
export const getAvailableMethods = async () => {
    try {
        const token = localStorage.getItem('access_token');
        const response = await axios.get(
            `${API_URL}/momo/available-methods`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error fetching available methods:', error);
        // Fallback nếu API lỗi: chỉ hỗ trợ captureWallet
        return {
            available_methods: ['captureWallet'],
            environment: 'test'
        };
    }
};

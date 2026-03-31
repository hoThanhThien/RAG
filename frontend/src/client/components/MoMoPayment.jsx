import React, { useState } from 'react';
import { createMoMoPayment, formatCurrency } from '../services/momoService.js';
import './MoMoPayment.css';
import './MoMoPaymentMethod.css';

const MoMoPayment = ({ bookingID, amount, onCancel }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('captureWallet');

    const handleMoMoPayment = async () => {
        try {
            setLoading(true);
            setError(null);

            // Gọi API backend để tạo MoMo payment
            const result = await createMoMoPayment(bookingID, paymentMethod);

            if (result.status === 'success' && result.payUrl) {
                // Redirect user đến trang thanh toán MoMo
                window.location.href = result.payUrl;
            } else {
                setError('Không thể tạo thanh toán MoMo');
            }
        } catch (err) {
            console.error('MoMo payment error:', err);
            setError(err.detail || 'Có lỗi xảy ra khi tạo thanh toán');
            setLoading(false);
        }
    };

    return (
        <div className="momo-payment-container">
            <div className="payment-method-card">
                <div className="payment-header">
                    <img 
                        src="https://developers.momo.vn/v3/assets/images/logo.svg" 
                        alt="MoMo" 
                        className="momo-logo"
                    />
                    <h3>Thanh toán qua MoMo</h3>
                </div>

                <div className="payment-details">
                    <div className="detail-row">
                        <span className="label">Số tiền:</span>
                        <span className="value">{formatCurrency(amount)}</span>
                    </div>
                    <div className="detail-row">
                        <span className="label">Mã booking:</span>
                        <span className="value">#{bookingID}</span>
                    </div>
                </div>

                {/* Chọn phương thức thanh toán MoMo */}
                <div className="payment-method-selection">
                    <h4 className="mb-3">Chọn phương thức thanh toán</h4>
                    <div className="method-options">
                        <label className={`method-option ${paymentMethod === 'captureWallet' ? 'active' : ''}`}>
                            <input
                                type="radio"
                                name="momoMethod"
                                value="captureWallet"
                                checked={paymentMethod === 'captureWallet'}
                                onChange={(e) => setPaymentMethod(e.target.value)}
                            />
                            <div className="method-content">
                                <i className="bi bi-qr-code fs-3 text-primary"></i>
                                <div className="method-text">
                                    <strong>Ví MoMo</strong>
                                    <small>Quét mã QR để thanh toán</small>
                                </div>
                            </div>
                        </label>

                        <label className={`method-option ${paymentMethod === 'payWithATM' ? 'active' : ''}`}>
                            <input
                                type="radio"
                                name="momoMethod"
                                value="payWithATM"
                                checked={paymentMethod === 'payWithATM'}
                                onChange={(e) => setPaymentMethod(e.target.value)}
                            />
                            <div className="method-content">
                                <i className="bi bi-credit-card fs-3 text-success"></i>
                                <div className="method-text">
                                    <strong>Thẻ ATM/Internet Banking</strong>
                                    <small>Liên kết thẻ ngân hàng để thanh toán</small>
                                </div>
                            </div>
                        </label>
                    </div>
                </div>

                {error && (
                    <div className="error-message">
                        <i className="fas fa-exclamation-circle"></i>
                        {error}
                    </div>
                )}

                <div className="payment-actions">
                    <button 
                        className="btn-pay-momo"
                        onClick={handleMoMoPayment}
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <i className="fas fa-spinner fa-spin"></i>
                                Đang xử lý...
                            </>
                        ) : (
                            <>
                                <i className="fas fa-wallet"></i>
                                Thanh toán với MoMo
                            </>
                        )}
                    </button>

                    {onCancel && (
                        <button 
                            className="btn-cancel"
                            onClick={onCancel}
                            disabled={loading}
                        >
                            Hủy
                        </button>
                    )}
                </div>

                <div className="payment-note">
                    <i className="fas fa-info-circle"></i>
                    <p>Bạn sẽ được chuyển đến trang thanh toán MoMo. Vui lòng hoàn tất thanh toán trong 15 phút.</p>
                </div>
            </div>
        </div>
    );
};

export default MoMoPayment;

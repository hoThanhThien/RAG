import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handleMoMoCallback, formatCurrency } from '../services/momoService.js';
import './MoMoCallback.css';

const MoMoCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(null);

    useEffect(() => {
        // Xử lý callback từ MoMo
        const paymentResult = handleMoMoCallback(searchParams);
        setResult(paymentResult);

        // Tự động redirect sau 5 giây
        const timer = setTimeout(() => {
            if (paymentResult.success) {
                navigate('/bookings'); // Redirect đến trang danh sách booking
            } else {
                navigate('/'); // Redirect về trang chủ
            }
        }, 5000);

        return () => clearTimeout(timer);
    }, [searchParams, navigate]);

    if (!result) {
        return (
            <div className="callback-container">
                <div className="loading">
                    <i className="fas fa-spinner fa-spin"></i>
                    <p>Đang xử lý kết quả thanh toán...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="callback-container">
            <div className={`callback-card ${result.success ? 'success' : 'failed'}`}>
                <div className="callback-icon">
                    {result.success ? (
                        <i className="fas fa-check-circle"></i>
                    ) : (
                        <i className="fas fa-times-circle"></i>
                    )}
                </div>

                <h2 className="callback-title">
                    {result.success ? 'Thanh toán thành công!' : 'Thanh toán thất bại'}
                </h2>

                <div className="callback-details">
                    <div className="detail-item">
                        <span className="label">Mã đơn hàng:</span>
                        <span className="value">{result.orderId}</span>
                    </div>

                    {result.transId && (
                        <div className="detail-item">
                            <span className="label">Mã giao dịch:</span>
                            <span className="value">{result.transId}</span>
                        </div>
                    )}

                    <div className="detail-item">
                        <span className="label">Số tiền:</span>
                        <span className="value amount">{formatCurrency(result.amount)}</span>
                    </div>

                    <div className="detail-item">
                        <span className="label">Trạng thái:</span>
                        <span className={`status ${result.success ? 'success' : 'failed'}`}>
                            {result.success ? 'Thành công' : 'Thất bại'}
                        </span>
                    </div>

                    {result.message && (
                        <div className="detail-item message">
                            <span className="label">Thông báo:</span>
                            <span className="value">{result.message}</span>
                        </div>
                    )}
                </div>

                <div className="callback-actions">
                    {result.success ? (
                        <>
                            <button 
                                className="btn-primary"
                                onClick={() => navigate('/bookings')}
                            >
                                <i className="fas fa-list"></i>
                                Xem danh sách booking
                            </button>
                            <button 
                                className="btn-secondary"
                                onClick={() => navigate('/')}
                            >
                                <i className="fas fa-home"></i>
                                Về trang chủ
                            </button>
                        </>
                    ) : (
                        <>
                            <button 
                                className="btn-primary"
                                onClick={() => navigate('/')}
                            >
                                <i className="fas fa-home"></i>
                                Về trang chủ
                            </button>
                            <button 
                                className="btn-secondary"
                                onClick={() => window.history.back()}
                            >
                                <i className="fas fa-arrow-left"></i>
                                Quay lại
                            </button>
                        </>
                    )}
                </div>

                <p className="auto-redirect">
                    Bạn sẽ được chuyển hướng tự động sau 5 giây...
                </p>
            </div>
        </div>
    );
};

export default MoMoCallback;

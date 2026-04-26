import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { confirmMoMoCallback, handleMoMoCallback, formatCurrency } from '../services/momoService.js';
import './MoMoCallback.css';

const MoMoCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(null);
    const [syncMessage, setSyncMessage] = useState('Đang đồng bộ trạng thái thanh toán...');

    useEffect(() => {
        let alive = true;
        let timer;

        const process = async () => {
            const paymentResult = handleMoMoCallback(searchParams);
            if (!alive) return;
            setResult(paymentResult);

            try {
                const confirmRes = await confirmMoMoCallback(searchParams);
                if (!alive) return;

                if (confirmRes?.status === 'success') {
                    setSyncMessage('Đồng bộ thành công. Trạng thái booking đã được cập nhật.');
                } else {
                    setSyncMessage(confirmRes?.message || 'Chưa thể đồng bộ tự động. Vui lòng kiểm tra lại sau.');
                }
            } catch (err) {
                if (!alive) return;
                setSyncMessage(
                    err?.response?.data?.message ||
                    err?.response?.data?.detail ||
                    'Chưa thể đồng bộ với hệ thống. Vui lòng kiểm tra lại trang thanh toán.'
                );
            }

            timer = setTimeout(() => {
                if (paymentResult.success) {
                    navigate('/bookings');
                } else {
                    navigate('/');
                }
            }, 5000);
        };

        process();
        return () => {
            alive = false;
            if (timer) clearTimeout(timer);
        };
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

                <p className="auto-redirect" style={{ marginBottom: 4 }}>
                    {syncMessage}
                </p>

                <p className="auto-redirect">
                    Bạn sẽ được chuyển hướng tự động sau 5 giây...
                </p>
            </div>
        </div>
    );
};

export default MoMoCallback;

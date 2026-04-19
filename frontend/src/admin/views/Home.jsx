import React, { useCallback, useEffect, useRef, useState } from "react";
import { adminService } from "../services/adminService";
import { connectAdminDashboardWS } from "../../client/services/ws";
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Dashboard admin với biểu đồ doanh thu theo địa điểm
const AdminHome = () => {
  const [stats, setStats] = useState({
    users: 0,
    tours: 0,
    categories: 0,
    discounts: 0,
    bookings: 0,
    revenue: 0
  });
  const [topCustomers, setTopCustomers] = useState([]);
  const [bookingStatus, setBookingStatus] = useState([]);
  const [locationRevenue, setLocationRevenue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [isAdmin, setIsAdmin] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [locationFilter, setLocationFilter] = useState('all'); // 'all', 'domestic', 'international'
  const wsRef = useRef(null);
  const hasLoadedRef = useRef(false);

  // Load dashboard data
  const loadDashboardData = useCallback(async ({ source = 'background' } = {}) => {
    const showFullLoader = source === 'initial' && !hasLoadedRef.current;
    const showManualRefresh = source === 'manual';

    try {
      if (showFullLoader) {
        setLoading(true);
      }
      if (showManualRefresh) {
        setRefreshing(true);
      }
      
      // Thử gọi API admin mới trước
      try {
        const [statsData, locationData, customers, statusData] = await Promise.all([
          adminService.getDashboardStats(),
          adminService.getRevenueByLocation(locationFilter !== 'all' ? locationFilter : null),
          adminService.getTopCustomers(),
          adminService.getBookingStatus()
        ]);

        setIsAdmin(true);
        setErrorMessage('');
        setStats(statsData);
        setLocationRevenue(locationData);
        setTopCustomers(customers);
        setBookingStatus(statusData);
        setLastUpdate(new Date());
      } catch (adminError) {
        // Nếu lỗi 403, có thể không phải admin - dùng dữ liệu cơ bản
        console.warn("Cannot load admin dashboard data, user may not be admin:", adminError);
        
        if (adminError.response?.status === 403) {
          setIsAdmin(false);
          setErrorMessage('Bạn không có quyền truy cập dashboard admin. Vui lòng đăng nhập bằng tài khoản admin.');
        }
        
        // Load basic stats from old endpoints
        const { fetchUsers } = await import("../services/userService");
        const { getTours } = await import("../services/tourService");
        const { fetchCategories } = await import("../services/categoryService");
        const { fetchDiscounts } = await import("../services/discountService");
        
        const [users, toursRes, categories, discounts] = await Promise.all([
          fetchUsers(),
          getTours(),
          fetchCategories(),
          fetchDiscounts(),
        ]);

        setStats({
          users: users.length,
          tours: toursRes.data?.items?.length || 0,
          categories: categories.length,
          discounts: discounts.length,
          bookings: 0,
          revenue: 0
        });
        setLastUpdate(new Date());
        
        // Empty arrays for charts since we don't have data
        setLocationRevenue([]);
        setTopCustomers([]);
        setBookingStatus([]);
      }
    } catch (error) {
      console.error("❌ Lỗi khi load dữ liệu dashboard:", error);
    } finally {
      hasLoadedRef.current = true;
      setLoading(false);
      setRefreshing(false);
    }
  }, [locationFilter]);

  // Load data on mount and when filter changes
  useEffect(() => {
    loadDashboardData({ source: 'initial' });
  }, [loadDashboardData]);

  // Realtime updates via WebSocket without reloading the page
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const ws = connectAdminDashboardWS(token);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg?.type === 'dashboard:refresh') {
          loadDashboardData({ source: 'background' });
        }
      } catch (err) {
        console.warn('Dashboard WS parse error:', err);
      }
    };

    return () => {
      setWsConnected(false);
      try {
        ws.close();
      } catch {
        // ignore close error
      }
    };
  }, [loadDashboardData]);

  // Fallback polling in case WS is temporarily unavailable
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData({ source: 'background' });
    }, 20000);

    return () => clearInterval(interval);
  }, [loadDashboardData]);

  // Refresh again when the tab becomes active
  useEffect(() => {
    const handleVisible = () => {
      if (document.visibilityState === 'visible') {
        loadDashboardData({ source: 'background' });
      }
    };

    window.addEventListener('focus', handleVisible);
    document.addEventListener('visibilitychange', handleVisible);

    return () => {
      window.removeEventListener('focus', handleVisible);
      document.removeEventListener('visibilitychange', handleVisible);
    };
  }, [loadDashboardData]);


  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(value);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
  const STATUS_COLORS = {
    'Pending': '#ffc107',
    'Confirmed': '#28a745',
    'Paid': '#007bff',
    'Cancelled': '#dc3545'
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid mt-4 px-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold text-primary mb-0">
          <i className="bi bi-speedometer2 me-2"></i>
          Bảng điều khiển Admin
        </h2>
        <div className="d-flex align-items-center gap-3">
          <small className="text-muted d-flex align-items-center gap-2">
            <span>
              <i className="bi bi-clock me-1"></i>
              Cập nhật: {lastUpdate.toLocaleTimeString('vi-VN')}
            </span>
            <span className={`badge ${wsConnected ? 'text-bg-success' : 'text-bg-warning'}`}>
              {wsConnected ? 'Live' : 'Đang đồng bộ'}
            </span>
          </small>
          <button 
            className="btn btn-sm btn-outline-primary"
            onClick={() => loadDashboardData({ source: 'manual' })}
            disabled={loading || refreshing}
          >
            <i className={`bi bi-arrow-clockwise me-1 ${(loading || refreshing) ? 'spin' : ''}`}></i>
            {refreshing ? 'Đang cập nhật...' : 'Làm mới'}
          </button>
        </div>
      </div>

      {/* Hiển thị cảnh báo nếu không phải admin */}
      {!isAdmin && errorMessage && (
        <div className="alert alert-warning alert-dismissible fade show" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          <strong>Cảnh báo:</strong> {errorMessage}
          <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      )}

      {/* Thống kê tổng quan */}
      <div className="row g-4 mb-4">
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #007bff' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Người dùng
                  </h6>
                  <h3 className="fw-bold mb-0 text-primary">{stats.users}</h3>
                </div>
                <div className="bg-primary bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-people-fill fs-3 text-primary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #28a745' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Tour
                  </h6>
                  <h3 className="fw-bold mb-0 text-success">{stats.tours}</h3>
                </div>
                <div className="bg-success bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-globe fs-3 text-success"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #ffc107' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Danh mục
                  </h6>
                  <h3 className="fw-bold mb-0 text-warning">{stats.categories}</h3>
                </div>
                <div className="bg-warning bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-tag-fill fs-3 text-warning"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #dc3545' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Giảm giá
                  </h6>
                  <h3 className="fw-bold mb-0 text-danger">{stats.discounts}</h3>
                </div>
                <div className="bg-danger bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-percent fs-3 text-danger"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #17a2b8' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Đặt tour
                  </h6>
                  <h3 className="fw-bold mb-0 text-info">{stats.bookings}</h3>
                </div>
                <div className="bg-info bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-calendar-check fs-3 text-info"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #6f42c1' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Doanh thu
                  </h6>
                  <h4 className="fw-bold mb-0" style={{ color: '#6f42c1', fontSize: '1.5rem' }}>
                    {formatCurrency(stats.revenue).split('₫')[0]}đ
                  </h4>
                </div>
                <div className="rounded-circle p-3" style={{ backgroundColor: 'rgba(111, 66, 193, 0.1)' }}>
                  <i className="bi bi-cash-stack fs-3" style={{ color: '#6f42c1' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Biểu đồ và thống kê - hiển thị khi là admin */}
      {isAdmin && (
        <div className="row g-4 mb-4">
        {/* Biểu đồ doanh thu theo địa điểm */}
        <div className="col-lg-8">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0 fw-bold">
                  <i className="bi bi-geo-alt-fill me-2 text-primary"></i>
                  Doanh thu theo địa điểm
                </h5>
                <div className="btn-group btn-group-sm" role="group">
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'all' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('all')}
                  >
                    <i className="bi bi-globe me-1"></i>
                    Tất cả
                  </button>
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'domestic' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('domestic')}
                  >
                    <i className="bi bi-flag me-1"></i>
                    Trong nước
                  </button>
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'international' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('international')}
                  >
                    <i className="bi bi-airplane me-1"></i>
                    Ngoài nước
                  </button>
                </div>
              </div>
            </div>
            <div className="card-body">
              {locationRevenue.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={locationRevenue} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="location" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                    />
                    <YAxis tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'revenue') return [formatCurrency(value), 'Doanh thu'];
                        if (name === 'total_bookings') return [value, 'Số lần booking'];
                        return [value, name];
                      }}
                      labelFormatter={(label) => `Địa điểm: ${label}`}
                    />
                    <Legend 
                      formatter={(value) => {
                        if (value === 'revenue') return 'Doanh thu';
                        if (value === 'total_bookings') return 'Số lần booking';
                        return value;
                      }}
                    />
                    <Bar dataKey="revenue" fill="#8884d8" radius={[8, 8, 0, 0]} name="Doanh thu" />
                    <Bar dataKey="total_bookings" fill="#82ca9d" radius={[8, 8, 0, 0]} name="Số lần booking" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-5 text-muted">
                  <i className="bi bi-inbox fs-1 d-block mb-2"></i>
                  <p>Chưa có dữ liệu doanh thu theo địa điểm</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Biểu đồ tròn trạng thái booking */}
        <div className="col-lg-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <h5 className="mb-0 fw-bold">
                <i className="bi bi-pie-chart me-2 text-success"></i>
                Trạng thái đặt tour
              </h5>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={bookingStatus}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="status"
                  >
                    {bookingStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Top 5 khách hàng chi tiêu nhiều nhất */}
      {isAdmin && (
        <div className="row g-4">
        <div className="col-12">
          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white border-0 py-3">
              <h5 className="mb-0 fw-bold">
                <i className="bi bi-trophy-fill me-2 text-warning"></i>
                Top 5 khách hàng chi tiêu nhiều nhất
              </h5>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th className="border-0 py-3" style={{ width: '50px' }}>
                        <i className="bi bi-hash"></i>
                      </th>
                      <th className="border-0 py-3">Tên khách hàng</th>
                      <th className="border-0 py-3">Email</th>
                      <th className="border-0 py-3">Số điện thoại</th>
                      <th className="border-0 py-3 text-end">Số lượng đặt</th>
                      <th className="border-0 py-3 text-end">Tổng chi tiêu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topCustomers.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="text-center py-4 text-muted">
                          <i className="bi bi-inbox fs-1 d-block mb-2"></i>
                          Chưa có dữ liệu khách hàng
                        </td>
                      </tr>
                    ) : (
                      topCustomers.map((customer, index) => (
                        <tr key={customer.user_id}>
                          <td className="align-middle">
                            <div 
                              className="d-flex align-items-center justify-content-center rounded-circle fw-bold text-white"
                              style={{
                                width: '35px',
                                height: '35px',
                                background: index === 0 ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)' :
                                          index === 1 ? 'linear-gradient(135deg, #C0C0C0 0%, #808080 100%)' :
                                          index === 2 ? 'linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)' :
                                          'linear-gradient(135deg, #6c757d 0%, #495057 100%)'
                              }}
                            >
                              {index + 1}
                            </div>
                          </td>
                          <td className="align-middle">
                            <div className="d-flex align-items-center">
                              <div 
                                className="rounded-circle bg-primary bg-opacity-10 d-flex align-items-center justify-content-center me-2"
                                style={{ width: '40px', height: '40px' }}
                              >
                                <i className="bi bi-person-fill text-primary"></i>
                              </div>
                              <span className="fw-semibold">{customer.name}</span>
                            </div>
                          </td>
                          <td className="align-middle text-muted">
                            <i className="bi bi-envelope me-1"></i>
                            {customer.email}
                          </td>
                          <td className="align-middle text-muted">
                            <i className="bi bi-telephone me-1"></i>
                            {customer.phone}
                          </td>
                          <td className="align-middle text-end">
                            <span className="badge bg-info">
                              {customer.total_bookings} tour
                            </span>
                          </td>
                          <td className="align-middle text-end">
                            <span className="fw-bold text-success fs-6">
                              {formatCurrency(customer.total_spent)}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default AdminHome;

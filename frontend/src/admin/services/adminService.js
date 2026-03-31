// src/admin/services/adminService.js
import { api } from '../../client/services/api';

export const adminService = {
  // Lấy thống kê tổng quan
  getDashboardStats: async () => {
    try {
      const response = await api.get('/admin/dashboard/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  },

  // Lấy dữ liệu biểu đồ doanh thu
  getRevenueChart: async (period = 'month') => {
    try {
      const response = await api.get(`/admin/dashboard/revenue-chart?period=${period}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue chart:', error);
      throw error;
    }
  },

  // Lấy top 5 khách hàng
  getTopCustomers: async () => {
    try {
      const response = await api.get('/admin/dashboard/top-customers');
      return response.data;
    } catch (error) {
      console.error('Error fetching top customers:', error);
      throw error;
    }
  },

  // Lấy thống kê booking theo status
  getBookingStatus: async () => {
    try {
      const response = await api.get('/admin/dashboard/booking-status');
      return response.data;
    } catch (error) {
      console.error('Error fetching booking status:', error);
      throw error;
    }
  },

  // Lấy doanh thu theo địa điểm
  getRevenueByLocation: async (locationType = null) => {
    try {
      const url = locationType 
        ? `/admin/dashboard/revenue-by-location?location_type=${locationType}`
        : '/admin/dashboard/revenue-by-location';
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue by location:', error);
      throw error;
    }
  },
};

// src/admin/services/adminService.js
import { api } from '../../client/services/api';

const liveConfig = () => ({
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    Pragma: 'no-cache',
    Expires: '0',
  },
  params: {
    _ts: Date.now(),
  },
});

export const adminService = {
  // Lấy thống kê tổng quan
  getDashboardStats: async () => {
    try {
      const response = await api.get('/admin/dashboard/stats', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  },

  // Lấy dữ liệu biểu đồ doanh thu
  getRevenueChart: async (period = 'month') => {
    try {
      const response = await api.get('/admin/dashboard/revenue-chart', {
        ...liveConfig(),
        params: {
          period,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue chart:', error);
      throw error;
    }
  },

  // Lấy top 5 khách hàng
  getTopCustomers: async () => {
    try {
      const response = await api.get('/admin/dashboard/top-customers', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching top customers:', error);
      throw error;
    }
  },

  // Lấy thống kê booking theo status
  getBookingStatus: async () => {
    try {
      const response = await api.get('/admin/dashboard/booking-status', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching booking status:', error);
      throw error;
    }
  },

  // Lấy doanh thu theo địa điểm
  getRevenueByLocation: async (locationType = null) => {
    try {
      const response = await api.get('/admin/dashboard/revenue-by-location', {
        ...liveConfig(),
        params: {
          ...(locationType ? { location_type: locationType } : {}),
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue by location:', error);
      throw error;
    }
  },

  // Lấy dữ liệu K-Means phân cụm điểm đến để hiển thị biểu đồ admin
  getKmeansDestinations: async (nClusters = 0) => {
    try {
      const response = await api.get('/admin/kmeans/destinations', {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching K-Means destinations:', error);
      throw error;
    }
  },

  rebuildCustomerSegments: async (nClusters = 0) => {
    try {
      const response = await api.post('/segments/rebuild', null, {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error rebuilding customer segments:', error);
      throw error;
    }
  },

  rebuildTourClusters: async (nClusters = 0) => {
    try {
      const response = await api.post('/admin/kmeans/tours/rebuild', null, {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error rebuilding tour clusters:', error);
      throw error;
    }
  },

  getCustomerSegment: async (userId) => {
    try {
      const response = await api.get(`/segments/${userId}`, liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching customer segment:', error);
      throw error;
    }
  },
};

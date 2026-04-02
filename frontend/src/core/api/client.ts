import axios from 'axios';
import { message } from 'ant-design-vue';

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
});

// Request Interceptor: Inject Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle Errors (401/403) and standard envelope
api.interceptors.response.use(
  (response) => {
    const resData = response.data;
    
    // 统一处理 {code, data, message} 标准外壳
    if (resData && typeof resData === 'object' && 'code' in resData) {
      if (resData.code === 200 || resData.code === 0) {
        // 剥离外壳，替换为真实数据
        response.data = resData.data;
      } else {
        // 业务级错误
        const errMsg = resData.message || resData.msg || '业务处理失败';
        message.error(errMsg);
        return Promise.reject(new Error(errMsg));
      }
    }
    
    return response;
  },
  (error) => {
    const { response } = error;
    if (response) {
      if (response.status === 401) {
        // 401 Unauthorized
        console.error('API Unauthorized (401)');
        // message.error('API 鉴权失败'); // Optional: show generic error
      } else if (response.status === 403) {
        console.error('API Forbidden (403)');
      }
    }
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

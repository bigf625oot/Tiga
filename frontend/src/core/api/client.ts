import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

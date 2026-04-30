import axios from 'axios';
import { clearAuthSession, readStoredToken } from './authSession';
import { getApiBaseUrl } from './env';

const baseURL = getApiBaseUrl();

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = readStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthSession();
      const path = window.location.pathname;
      if (path !== '/login' && !path.startsWith('/login')) {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  }
);

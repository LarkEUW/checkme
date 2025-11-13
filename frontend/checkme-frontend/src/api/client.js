import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 30000
});

let authToken = null;

export const setAuthToken = (token) => {
  authToken = token;
};

client.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.detail || data?.message || error.message;
      return Promise.reject(new Error(`(${status}) ${message}`));
    }
    return Promise.reject(error);
  }
);

export default client;

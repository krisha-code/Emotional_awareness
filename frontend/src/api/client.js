import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.dispatchEvent(new Event('unauthorized'));
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => client.post('/auth/login', { email, password }),
  register: (email, username, password) => client.post('/auth/register', { email, username, password }),
  logout: () => client.post('/auth/logout'),
  me: () => client.get('/auth/me'),
  consent: (flags) => client.put('/auth/consent', flags)
};

export const predictAPI = {
  face: (image_base64) => client.post('/predict/face', { image_base64 }),
  text: (text) => client.post('/predict/text', { text }),
  speech: (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    return client.post('/predict/speech', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  physiological: (data) => client.post('/predict/physiological', data)
};

export const fusionAPI = {
  analyze: (payload) => client.post('/fusion/analyze', payload),
  getSession: (id) => client.get(`/fusion/session/${id}`)
};

export const historyAPI = {
  getHistory: (page = 1, perPage = 10) => client.get(`/history/?page=${page}&per_page=${perPage}`),
  getTrends: (days = 7) => client.get(`/history/trends?days=${days}`),
  getSummary: () => client.get('/history/summary'),
  deleteSession: (id) => client.delete(`/history/${id}`)
};

export const exportAPI = {
  csv: () => client.get('/export/csv', { responseType: 'blob' }),
  journal: () => client.get('/export/journal', { responseType: 'blob' })
};

export default client;

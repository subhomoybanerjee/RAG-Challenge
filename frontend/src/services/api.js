import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
// const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = async (query, history = [], useReranking = false) => {
  return api.post('/chat', { query, history, use_reranking: useReranking });
};

export const ingestAPI = async (apiKey, docPath, modelName = 'llama-3.3-70b-versatile') => {
  return api.post('/ingest', { api_key: apiKey, doc_path: docPath, model_name: modelName });
};

export const statusAPI = async () => {
  return api.get('/status');
};

export const clearHistoryAPI = async () => {
  return api.post('/clear-history');
};

export const clearVectorDBAPI = async () => {
  return api.post('/clear-vector-db');
};

export const healthCheckAPI = async () => {
  return api.get('/health');
};

export default api;


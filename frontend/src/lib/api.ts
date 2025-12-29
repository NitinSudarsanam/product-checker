import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface URL {
  id: string;
  url: string;
  created_at: string;
  group_name?: string;
}

export interface ScanResult {
  id: string;
  url: string;
  scanned_at: string;
  add_to_cart: boolean;
  buy_now: boolean;
  status: 'available' | 'unavailable' | 'error';
  error_message?: string;
  response_time?: number;
}

export interface Stats {
  total_urls: number;
  total_scans: number;
  available_count: number;
  unavailable_count: number;
  error_count: number;
}

// URL Management
export const addURLs = async (urls: string[], group_name?: string) => {
  const response = await api.post('/api/urls/add', { urls, group_name });
  return response.data;
};

export const getURLs = async (group_name?: string) => {
  const response = await api.get<URL[]>('/api/urls', {
    params: { group_name },
  });
  return response.data;
};

export const deleteURL = async (id: string) => {
  const response = await api.delete(`/api/urls/${id}`);
  return response.data;
};

export const deleteAllURLs = async () => {
  const response = await api.delete('/api/urls');
  return response.data;
};

// Scanning
export const runScan = async (url_ids?: string[]) => {
  const response = await api.post('/api/scan/run', { url_ids });
  return response.data;
};

export const getScanResults = async (url?: string, status_filter?: string) => {
  const response = await api.get<ScanResult[]>('/api/scan/results', {
    params: { url, status_filter },
  });
  return response.data;
};

export const getLatestResults = async (limit: number = 50) => {
  const response = await api.get<ScanResult[]>('/api/scan/results/latest', {
    params: { limit },
  });
  return response.data;
};

export const clearScanResults = async () => {
  const response = await api.delete('/api/scan/results');
  return response.data;
};

// Stats
export const getStats = async () => {
  const response = await api.get<Stats>('/api/logs/stats');
  return response.data;
};

export default api;

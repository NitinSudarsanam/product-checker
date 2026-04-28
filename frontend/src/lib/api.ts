import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || (() => {
  if (typeof window !== 'undefined' && !process.env.NEXT_PUBLIC_API_URL) {
    console.warn('NEXT_PUBLIC_API_URL not set — falling back to http://localhost:8080. Set this in .env.local for production.');
  }
  return 'http://localhost:8080';
})();

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
  scrape_method?: string;
  /** First successful HTML fetch (playwright | scrapingbee | static) — debug */
  html_primary_source?: string;
  variants?: Record<string, 'available' | 'unavailable'>;
  variants_checked?: boolean;
  unavailability_override?: boolean;
}

export interface Stats {
  total_urls: number;
  total_scans: number;
  available_count: number;
  unavailable_count: number;
  error_count: number;
}

export interface ScanJobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled';
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  total_urls: number;
  completed: number;
  success: number;
  error: number;
  rate_urls_per_sec?: number | null;
  eta_seconds?: number | null;
  last_update_at?: string | null;
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

export const getScanStatus = async (): Promise<{ scanning: boolean }> => {
  const response = await api.get('/api/scan/status');
  return response.data;
};

export const getJobStatus = async (job_id: string) => {
  const response = await api.get<ScanJobStatus>(`/api/scan/${job_id}/status`);
  return response.data;
};

export const getScanResults = async (url?: string, status_filter?: string) => {
  const response = await api.get<ScanResult[]>('/api/scan/results', {
    params: { url, status_filter },
  });
  return response.data;
};

export const getLatestResults = async (limit: number = 500) => {
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

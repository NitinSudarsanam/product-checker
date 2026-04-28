import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import { Play, RefreshCw, ShoppingCart, X, Home as HomeIcon, Link2, BarChart3 } from 'lucide-react';
import URLInput from '@/components/URLInput';
import URLList from '@/components/URLList';
import ResultsTable from '@/components/ResultsTable';
import StatsCard from '@/components/StatsCard';
import {
  addURLs,
  getURLs,
  deleteURL,
  runScan,
  getJobStatus,
  getLatestResults,
  getStats,
  URL as URLType,
  ScanResult,
  Stats,
} from '@/lib/api';

export default function Home() {
  const [tab, setTab] = useState<'dashboard' | 'urls' | 'results'>('dashboard');
  const [urls, setUrls] = useState<URLType[]>([]);
  const [results, setResults] = useState<ScanResult[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState<{
    done: number;
    total: number;
    elapsed: number;
    rate?: number | null;
    eta?: number | null;
  } | null>(null);
  const [scanJobId, setScanJobId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error';
  } | null>(null);
  const notificationTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup all timers on unmount (7.7, 7.10)
  useEffect(() => {
    return () => {
      if (notificationTimer.current) clearTimeout(notificationTimer.current);
      if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);
      if (elapsedIntervalRef.current) clearInterval(elapsedIntervalRef.current);
    };
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [urlsData, resultsData, statsData] = await Promise.all([
        getURLs(),
        getLatestResults(),
        getStats(),
      ]);
      setUrls(urlsData);
      setResults(resultsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching data:', error);
      showNotification('Failed to fetch data from backend', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    if (notificationTimer.current) clearTimeout(notificationTimer.current);
    setNotification({ message, type });
    notificationTimer.current = setTimeout(() => setNotification(null), 8000);
  };

  const dismissNotification = () => {
    if (notificationTimer.current) clearTimeout(notificationTimer.current);
    setNotification(null);
  };

  const handleAddURLs = async (urlList: string[], groupName?: string) => {
    setLoading(true);
    try {
      const result = await addURLs(urlList, groupName);
      showNotification(result.message, 'success');
      await fetchData();
    } catch (error: any) {
      showNotification(
        error.response?.data?.detail || 'Failed to add URLs',
        'error'
      );
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteURL = async (id: string) => {
    if (!confirm('Delete this URL and its scan history?')) return;

    setLoading(true);
    try {
      await deleteURL(id);
      showNotification('URL deleted', 'success');
      await fetchData();
    } catch (error) {
      showNotification('Failed to delete URL', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    if (urls.length === 0) {
      showNotification('Add some URLs before scanning', 'error');
      return;
    }

    setScanning(true);
    setScanProgress({ done: 0, total: urls.length, elapsed: 0 });
    setScanJobId(null);

    const startMs = Date.now();

    try {
      const result = await runScan();
      showNotification(result.message, 'success');

      const expectedCount = result.url_count;
      const jobId = result.job_id as string | undefined;
      if (!jobId) {
        throw new Error('Backend did not return job_id');
      }
      setScanJobId(jobId);
      let attempts = 0;
      const maxAttempts = 360; // 30 min max (360 × 5s)

      elapsedIntervalRef.current = setInterval(() => {
        setScanProgress(prev => prev ? { ...prev, elapsed: Math.floor((Date.now() - startMs) / 1000) } : null);
      }, 1000);

      const stopPolling = () => {
        if (elapsedIntervalRef.current) { clearInterval(elapsedIntervalRef.current); elapsedIntervalRef.current = null; }
        if (pollTimeoutRef.current) { clearTimeout(pollTimeoutRef.current); pollTimeoutRef.current = null; }
        setScanning(false);
        setScanProgress(null);
      };

      // Poll job status for progress + ETA
      const poll = async () => {
        attempts++;
        try {
          const [job, latest] = await Promise.all([
            getJobStatus(jobId),
            getLatestResults(500),
          ]);

          setScanProgress({
            done: job.completed ?? latest.length,
            total: job.total_urls ?? expectedCount,
            elapsed: Math.floor((Date.now() - startMs) / 1000),
            rate: job.rate_urls_per_sec ?? null,
            eta: job.eta_seconds ?? null,
          });
          await fetchData();

          const isDone = job.status === 'done' || job.status === 'failed' || job.status === 'cancelled';
          if (isDone || attempts >= maxAttempts) {
            stopPolling();
            showNotification(
              isDone
                ? `Scan ${job.status} — ${job.completed}/${job.total_urls} completed`
                : 'Scan timed out waiting for results',
              isDone && job.status === 'done' ? 'success' : 'error'
            );
          } else {
            pollTimeoutRef.current = setTimeout(poll, 5000);
          }
        } catch (err) {
          stopPolling();
          showNotification('Error polling scan results', 'error');
        }
      };

      pollTimeoutRef.current = setTimeout(poll, 5000);
    } catch (error: any) {
      const msg = 'Failed to start scan';
      showNotification(msg, 'error');
      setScanning(false);
      setScanProgress(null);
    }
  };

  const handleRefresh = async () => {
    await fetchData();
    showNotification('Data refreshed', 'success');
  };

  return (
    <>
      <Head>
        <title>Ubique Product Checker</title>
        <meta name="description" content="Detect buy buttons on e-commerce websites" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[216px] flex-shrink-0 bg-white border-r border-primary-100 flex flex-col">
          <div className="px-[18px] py-5 flex items-center gap-3 border-b border-gray-100">
            <div className="w-[34px] h-[34px] rounded-[10px] bg-gradient-to-br from-primary-600 to-fuchsia-500 flex items-center justify-center flex-shrink-0">
              <ShoppingCart size={16} className="text-white" />
            </div>
            <div>
              <div className="text-[14px] font-bold text-gray-900 leading-tight">Product Checker</div>
              <div className="text-[10px] font-medium text-primary-400">Buy Button Detector</div>
            </div>
          </div>

          <div className="flex-1 p-3 flex flex-col gap-1">
            <div className="text-[10px] font-semibold text-primary-300 uppercase tracking-[.8px] px-2 py-1">Menu</div>

            <button
              className={`nav-item ${tab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setTab('dashboard')}
            >
              <HomeIcon size={16} />
              Dashboard
            </button>
            <button
              className={`nav-item ${tab === 'urls' ? 'active' : ''}`}
              onClick={() => setTab('urls')}
            >
              <Link2 size={16} />
              URL Manager
              <span className="nav-badge">{urls.length}</span>
            </button>
            <button
              className={`nav-item ${tab === 'results' ? 'active' : ''}`}
              onClick={() => setTab('results')}
            >
              <BarChart3 size={16} />
              Results
              <span className="nav-badge">{results.length}</span>
            </button>
          </div>

          <div className="px-[18px] py-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-[11px] text-gray-500 font-medium">
              <span className="w-[7px] h-[7px] rounded-full bg-emerald-500 shadow-[0_0_0_2px_#d1fae5]" />
              System online
            </div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Topbar */}
          <div className="bg-white border-b border-gray-100 h-[58px] px-7 flex items-center justify-between flex-shrink-0">
            <div>
              <div className="text-[16px] font-bold text-gray-900">
                {tab === 'dashboard' ? 'Dashboard' : tab === 'urls' ? 'URL Manager' : 'Scan Results'}
              </div>
              <div className="text-[12px] text-gray-400 mt-[1px]">
                {tab === 'dashboard'
                  ? 'Overview of your monitoring activity'
                  : tab === 'urls'
                    ? 'Manage URLs to monitor'
                    : 'Latest scan results'}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button onClick={handleRefresh} disabled={loading || scanning} className="pc-btn-ghost pc-btn-sm">
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                Refresh
              </button>
              <button onClick={handleRunScan} disabled={scanning || loading || urls.length === 0} className="pc-btn-primary pc-btn-sm">
                <Play size={13} className={scanning ? 'animate-pulse' : ''} />
                {scanning ? 'Scanning…' : 'Run Scan'}
              </button>
            </div>
          </div>

          {/* Scan progress */}
          {scanning && scanProgress && (
            <div className="bg-white border-b border-primary-100 px-7 py-2.5 flex-shrink-0">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-primary-600">
                  Scanning {scanProgress.done} / {scanProgress.total} URLs
                </span>
                <div className="text-[11px] text-gray-400 flex gap-4">
                  <span>{scanProgress.elapsed}s elapsed</span>
                  <span>{scanProgress.rate != null ? `${scanProgress.rate.toFixed(1)} url/s` : '— url/s'}</span>
                  <span>{scanProgress.eta != null ? `ETA ${scanProgress.eta}s` : 'ETA —'}</span>
                  {scanJobId && <span className="text-primary-300">#{scanJobId.slice(-8)}</span>}
                </div>
              </div>
              <div className="h-1.5 bg-primary-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-600 to-fuchsia-500 rounded-full transition-[width] duration-500 ease-out"
                  style={{ width: scanProgress.total > 0 ? `${Math.min(100, (scanProgress.done / scanProgress.total) * 100)}%` : '5%' }}
                />
              </div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-7 py-6">
            {tab === 'dashboard' && (
              <>
                <StatsCard stats={stats} loading={loading} />
                <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5 mt-5">
                  <URLInput onAdd={handleAddURLs} loading={loading} />
                  <URLList urls={urls} onDelete={handleDeleteURL} loading={loading} />
                </div>
                <div className="mt-5">
                  <ResultsTable results={results} loading={scanning} />
                </div>
              </>
            )}

            {tab === 'urls' && (
              <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
                <URLInput onAdd={handleAddURLs} loading={loading} />
                <URLList urls={urls} onDelete={handleDeleteURL} loading={loading} />
              </div>
            )}

            {tab === 'results' && (
              <>
                <StatsCard stats={stats} loading={loading} />
                <div className="mt-5">
                  <ResultsTable results={results} loading={scanning} />
                </div>
              </>
            )}
          </div>
        </div>

        {/* Toast */}
        {notification && (
          <div className="fixed top-5 right-6 z-[999]">
            <div className="bg-white rounded-xl px-4 py-3 min-w-[280px] shadow-[0_8px_30px_rgba(0,0,0,0.12),0_2px_6px_rgba(0,0,0,0.06)] flex items-center gap-3 text-[13px] font-medium">
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                  notification.type === 'success' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                }`}
              >
                {notification.type === 'success' ? '✓' : '×'}
              </div>
              <span className="text-gray-800">{notification.message}</span>
              <button onClick={dismissNotification} className="ml-auto text-gray-400 hover:text-gray-600 p-1">
                <X size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

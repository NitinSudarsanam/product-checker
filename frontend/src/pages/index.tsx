import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import { Play, RefreshCw, ShoppingCart, X } from 'lucide-react';
import URLInput from '@/components/URLInput';
import URLList from '@/components/URLList';
import ResultsTable from '@/components/ResultsTable';
import StatsCard from '@/components/StatsCard';
import {
  addURLs,
  getURLs,
  deleteURL,
  runScan,
  getScanStatus,
  getLatestResults,
  getStats,
  URL as URLType,
  ScanResult,
  Stats,
} from '@/lib/api';

export default function Home() {
  const [urls, setUrls] = useState<URLType[]>([]);
  const [results, setResults] = useState<ScanResult[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState<{ done: number; total: number; elapsed: number } | null>(null);
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

    const startMs = Date.now();

    try {
      const result = await runScan();
      showNotification(result.message, 'success');

      const expectedCount = result.url_count;
      let attempts = 0;
      const maxAttempts = 72; // 6 min max (72 × 5s)

      elapsedIntervalRef.current = setInterval(() => {
        setScanProgress(prev => prev ? { ...prev, elapsed: Math.floor((Date.now() - startMs) / 1000) } : null);
      }, 1000);

      const stopPolling = () => {
        if (elapsedIntervalRef.current) { clearInterval(elapsedIntervalRef.current); elapsedIntervalRef.current = null; }
        if (pollTimeoutRef.current) { clearTimeout(pollTimeoutRef.current); pollTimeoutRef.current = null; }
        setScanning(false);
        setScanProgress(null);
      };

      // Use /api/scan/status to detect completion — no timezone-sensitive timestamp comparison (7.1, 7.4)
      const poll = async () => {
        attempts++;
        try {
          const [statusRes, latest] = await Promise.all([
            getScanStatus(),
            getLatestResults(500),
          ]);

          setScanProgress({ done: latest.length, total: expectedCount, elapsed: Math.floor((Date.now() - startMs) / 1000) });
          await fetchData();

          if (!statusRes.scanning || attempts >= maxAttempts) {
            stopPolling();
            showNotification(
              !statusRes.scanning
                ? `Scan complete — ${expectedCount} URLs scanned`
                : 'Scan timed out waiting for results',
              !statusRes.scanning ? 'success' : 'error'
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
      const msg = error?.response?.status === 409
        ? 'A scan is already in progress'
        : 'Failed to start scan';
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

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShoppingCart size={32} className="text-primary-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Ubique Product Checker
                  </h1>
                  <p className="text-sm text-gray-600">
                    Buy Button Detection System
                  </p>
                </div>
              </div>

              <div className="flex gap-2 items-center">
                <button
                  onClick={handleRefresh}
                  disabled={loading || scanning}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                  Refresh
                </button>

                <button
                  onClick={handleRunScan}
                  disabled={scanning || loading || urls.length === 0}
                  className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
                >
                  <Play size={16} className={scanning ? 'animate-pulse' : ''} />
                  {scanning ? 'Scanning...' : 'Run Scan'}
                </button>
              </div>
            </div>

            {/* Scan Progress Bar */}
            {scanning && scanProgress && (
              <div className="mt-3">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>
                    Scanning {scanProgress.done}/{scanProgress.total} URLs
                  </span>
                  <span>{scanProgress.elapsed}s elapsed</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: scanProgress.total > 0 ? `${Math.min(100, (scanProgress.done / scanProgress.total) * 100)}%` : '5%' }}
                  />
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Notification */}
        {notification && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
            <div
              className={`p-4 rounded-md flex items-center justify-between ${
                notification.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-800'
                  : 'bg-red-50 border border-red-200 text-red-800'
              }`}
            >
              <span>{notification.message}</span>
              <button onClick={dismissNotification} className="ml-4 opacity-60 hover:opacity-100">
                <X size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8">
            <StatsCard stats={stats} loading={loading} />
            <URLInput onAdd={handleAddURLs} loading={loading} />
            <URLList urls={urls} onDelete={handleDeleteURL} loading={loading} />
            <ResultsTable results={results} loading={scanning} />
          </div>
        </main>

        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-600">
              © 2024 Ubique Product Checker. Built for efficient e-commerce monitoring.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}

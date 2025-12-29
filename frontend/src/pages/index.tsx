import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { Play, RefreshCw, ShoppingCart } from 'lucide-react';
import URLInput from '@/components/URLInput';
import URLList from '@/components/URLList';
import ResultsTable from '@/components/ResultsTable';
import StatsCard from '@/components/StatsCard';
import {
  addURLs,
  getURLs,
  deleteURL,
  runScan,
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
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error';
  } | null>(null);

  // Fetch initial data
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
      showNotification('Failed to fetch data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
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
    if (!confirm('Are you sure you want to delete this URL?')) return;
    
    setLoading(true);
    try {
      await deleteURL(id);
      showNotification('URL deleted successfully', 'success');
      await fetchData();
    } catch (error) {
      showNotification('Failed to delete URL', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    if (urls.length === 0) {
      showNotification('Please add some URLs first', 'error');
      return;
    }

    setScanning(true);
    try {
      const result = await runScan();
      showNotification(result.message, 'success');
      
      // Poll for results
      setTimeout(async () => {
        await fetchData();
        setScanning(false);
      }, 5000);
    } catch (error) {
      showNotification('Failed to start scan', 'error');
      setScanning(false);
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
              
              <div className="flex gap-2">
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
                  <Play size={16} />
                  {scanning ? 'Scanning...' : 'Run Scan'}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Notification */}
        {notification && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
            <div
              className={`p-4 rounded-md ${
                notification.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-800'
                  : 'bg-red-50 border border-red-200 text-red-800'
              }`}
            >
              {notification.message}
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8">
            {/* Stats */}
            <StatsCard stats={stats} loading={loading} />

            {/* URL Input */}
            <URLInput onAdd={handleAddURLs} loading={loading} />

            {/* URL List */}
            <URLList urls={urls} onDelete={handleDeleteURL} loading={loading} />

            {/* Results */}
            <ResultsTable results={results} loading={scanning} />
          </div>
        </main>

        {/* Footer */}
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

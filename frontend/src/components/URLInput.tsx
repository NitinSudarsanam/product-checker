import React, { useState } from 'react';
import { Plus } from 'lucide-react';

interface URLInputProps {
  onAdd: (urls: string[], groupName?: string) => Promise<void>;
  loading: boolean;
}

const URLInput: React.FC<URLInputProps> = ({ onAdd, loading }) => {
  const [singleURL, setSingleURL] = useState('');
  const [bulkURLs, setBulkURLs] = useState('');
  const [groupName, setGroupName] = useState('');
  const [mode, setMode] = useState<'single' | 'bulk'>('single');
  const [error, setError] = useState('');

  const validateURL = (url: string): boolean => {
    try {
      new URL(url);
      return url.startsWith('http://') || url.startsWith('https://');
    } catch {
      return false;
    }
  };

  const handleSubmit = async () => {
    setError('');
    
    let urlsToAdd: string[] = [];
    
    if (mode === 'single') {
      if (!singleURL.trim()) {
        setError('Please enter a URL');
        return;
      }
      if (!validateURL(singleURL.trim())) {
        setError('Please enter a valid URL starting with http:// or https://');
        return;
      }
      urlsToAdd = [singleURL.trim()];
    } else {
      const urls = bulkURLs
        .split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
      
      if (urls.length === 0) {
        setError('Please enter at least one URL');
        return;
      }
      
      const invalidURLs = urls.filter(url => !validateURL(url));
      if (invalidURLs.length > 0) {
        setError(`Invalid URLs found: ${invalidURLs.slice(0, 3).join(', ')}${invalidURLs.length > 3 ? '...' : ''}`);
        return;
      }
      
      urlsToAdd = urls;
    }
    
    try {
      await onAdd(urlsToAdd, groupName.trim() || undefined);
      
      // Clear inputs on success
      setSingleURL('');
      setBulkURLs('');
      setGroupName('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add URLs');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Add URLs</h2>
      
      {/* Mode Toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('single')}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            mode === 'single'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Single URL
        </button>
        <button
          onClick={() => setMode('bulk')}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            mode === 'bulk'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Bulk Import
        </button>
      </div>
      
      {/* Input Fields */}
      {mode === 'single' ? (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Product URL
          </label>
          <input
            type="text"
            value={singleURL}
            onChange={(e) => setSingleURL(e.target.value)}
            placeholder="https://www.example.com/product"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={loading}
          />
        </div>
      ) : (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            URLs (one per line)
          </label>
          <textarea
            value={bulkURLs}
            onChange={(e) => setBulkURLs(e.target.value)}
            placeholder="https://www.example.com/product1&#10;https://www.example.com/product2&#10;https://www.example.com/product3"
            rows={6}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
            disabled={loading}
          />
        </div>
      )}
      
      {/* Group Name */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Group Name (Optional)
        </label>
        <input
          type="text"
          value={groupName}
          onChange={(e) => setGroupName(e.target.value)}
          placeholder="e.g., Electronics, Clothing"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          disabled={loading}
        />
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
      
      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full bg-primary-600 text-white px-6 py-3 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        <Plus size={20} />
        {loading ? 'Adding...' : 'Add URLs'}
      </button>
    </div>
  );
};

export default URLInput;

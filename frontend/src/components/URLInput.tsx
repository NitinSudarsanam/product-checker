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
    <div className="pc-card">
      <div className="pc-card-head">
        <div className="pc-card-title">Add URLs</div>
        <div className="pc-mode-group">
          <button
            onClick={() => setMode('single')}
            className={`pc-mode-btn ${mode === 'single' ? 'pc-mode-btn-active' : ''}`}
            type="button"
          >
            Single
          </button>
          <button
            onClick={() => setMode('bulk')}
            className={`pc-mode-btn ${mode === 'bulk' ? 'pc-mode-btn-active' : ''}`}
            type="button"
          >
            Bulk
          </button>
        </div>
      </div>

      <div className="px-6 py-5 flex flex-col gap-4">
        <div>
          <label className="pc-flabel">{mode === 'single' ? 'Product URL' : 'URLs (one per line)'}</label>
          {mode === 'single' ? (
            <input
              type="text"
              value={singleURL}
              onChange={(e) => setSingleURL(e.target.value)}
              placeholder="https://example.com/product"
              className="pc-field"
              disabled={loading}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
          ) : (
            <textarea
              value={bulkURLs}
              onChange={(e) => setBulkURLs(e.target.value)}
              placeholder={'https://example.com/product1\nhttps://example.com/product2'}
              rows={5}
              className="pc-field font-mono text-xs leading-relaxed"
              disabled={loading}
            />
          )}
        </div>

        <div>
          <label className="pc-flabel">
            Group <span className="font-normal text-primary-300">(optional)</span>
          </label>
          <input
            type="text"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            placeholder="e.g. Footwear, Electronics"
            className="pc-field"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="pc-btn-primary justify-center"
          type="button"
        >
          <Plus size={16} />
          {loading ? 'Adding…' : 'Add URLs'}
        </button>
      </div>
    </div>
  );
};

export default URLInput;

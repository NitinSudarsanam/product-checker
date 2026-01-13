import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, ExternalLink, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { ScanResult } from '@/lib/api';

interface ResultsTableProps {
  results: ScanResult[];
  loading: boolean;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, loading }) => {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const formatDate = (s: string) => new Date(s).toLocaleString();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':   return <CheckCircle className="text-green-500" size={20} />;
      case 'unavailable': return <XCircle className="text-red-500" size={20} />;
      case 'error':       return <AlertCircle className="text-yellow-500" size={20} />;
      default:            return <Clock className="text-gray-400" size={20} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const m: Record<string, string> = {
      available:   'bg-green-100 text-green-800',
      unavailable: 'bg-red-100 text-red-800',
      error:       'bg-yellow-100 text-yellow-800',
    };
    return m[status] || 'bg-gray-100 text-gray-800';
  };

  const getRowBg = (status: string) =>
    status === 'error' ? 'bg-yellow-50 hover:bg-yellow-100' : 'hover:bg-gray-50';

  const getMethodBadge = (method?: string) => {
    if (!method) return null;
    const colors: Record<string, string> = {
      scrapingbee: 'bg-purple-100 text-purple-700',
      playwright:  'bg-blue-100 text-blue-700',
      static:      'bg-gray-100 text-gray-600',
    };
    return (
      <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${colors[method] || 'bg-gray-100 text-gray-600'}`}>
        {method}
      </span>
    );
  };

  /** Compact variant summary: "3/5 avail" or "none" or "—" */
  const getVariantSummary = (result: ScanResult) => {
    const variants = result.variants;
    if (!variants || Object.keys(variants).length === 0) {
      return (
        <span className="text-xs text-gray-400">
          {result.variants_checked ? 'none found' : '—'}
        </span>
      );
    }
    const total     = Object.keys(variants).length;
    const available = Object.values(variants).filter(v => v === 'available').length;
    const color     = available > 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50';
    return (
      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${color}`}>
        {available}/{total} avail
      </span>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
        <p className="mt-4 text-gray-600">Scanning in progress...</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <p className="text-gray-500">No scan results yet. Run a scan to see results!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-800">Scan Results ({results.length})</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-2 py-3 w-8" />
              <th className="px-4 py-3 text-left   text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Cart</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Buy Now</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Variants</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
              <th className="px-4 py-3 text-left   text-xs font-medium text-gray-500 uppercase tracking-wider">Scanned</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((result) => {
              const hasVariants = result.variants && Object.keys(result.variants).length > 0;
              const isExpanded  = expandedRows.has(result.id);

              return (
                <React.Fragment key={result.id}>
                  {/* Main row */}
                  <tr className={`transition-colors ${getRowBg(result.status)}`}>
                    {/* Expand toggle */}
                    <td className="px-2 py-4 text-center">
                      {hasVariants ? (
                        <button onClick={() => toggleRow(result.id)} className="text-gray-400 hover:text-gray-700">
                          {isExpanded
                            ? <ChevronDown size={16} />
                            : <ChevronRight size={16} />}
                        </button>
                      ) : <span className="w-4 inline-block" />}
                    </td>

                    <td className="px-4 py-4 max-w-xs">
                      <div className="flex items-center gap-2">
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-800 hover:underline truncate block text-sm"
                          title={result.url}
                        >
                          {result.url}
                        </a>
                        <ExternalLink size={12} className="text-gray-400 flex-shrink-0" />
                      </div>
                      {result.error_message && (
                        <p className="text-xs text-red-600 mt-1 break-words">
                          {result.error_message}
                        </p>
                      )}
                      {result.unavailability_override && (
                        <p className="text-xs text-orange-600 mt-1" title="Button found in HTML but out-of-stock signal detected">
                          ⚠ OOS signal overrode button detection
                        </p>
                      )}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {result.add_to_cart
                        ? <CheckCircle className="text-green-500 mx-auto" size={20} />
                        : <XCircle className="text-gray-300 mx-auto" size={20} />}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {result.buy_now
                        ? <CheckCircle className="text-green-500 mx-auto" size={20} />
                        : <XCircle className="text-gray-300 mx-auto" size={20} />}
                    </td>

                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {getStatusIcon(result.status)}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(result.status)}`}>
                          {result.status}
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      <button
                        onClick={() => hasVariants && toggleRow(result.id)}
                        className={hasVariants ? 'cursor-pointer' : 'cursor-default'}
                      >
                        {getVariantSummary(result)}
                      </button>
                    </td>

                    <td className="px-4 py-4 text-center">
                      {getMethodBadge(result.scrape_method)}
                    </td>

                    <td className="px-4 py-4 text-center text-sm text-gray-600 whitespace-nowrap">
                      {result.response_time ? `${result.response_time}s` : '—'}
                    </td>

                    <td className="px-4 py-4 text-sm text-gray-600 whitespace-nowrap">
                      {formatDate(result.scanned_at)}
                    </td>
                  </tr>

                  {/* Variant detail row — expanded */}
                  {hasVariants && isExpanded && (
                    <tr className="bg-gray-50">
                      <td colSpan={9} className="px-8 py-4">
                        <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                          Per-variant availability
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(result.variants!).map(([label, status]) => (
                            <span
                              key={label}
                              className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                                status === 'available'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {status === 'available'
                                ? <CheckCircle size={12} />
                                : <XCircle size={12} />}
                              {label}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultsTable;

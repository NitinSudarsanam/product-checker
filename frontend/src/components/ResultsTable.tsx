import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, ExternalLink, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { ScanResult } from '@/lib/api';

interface ResultsTableProps {
  results: ScanResult[];
  loading: boolean;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, loading }) => {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<'all' | 'available' | 'unavailable' | 'error'>('all');

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
    status === 'error' ? 'bg-yellow-50/40 hover:bg-yellow-50' : 'hover:bg-[#faf8ff]';

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

  /** Debug: which backend produced HTML first vs final scrape_method on the row */
  const getMethodDebugCell = (result: ScanResult) => {
    const primary = result.html_primary_source;
    const finalM = result.scrape_method;
    if (!primary && !finalM) {
      return <span className="text-xs text-gray-300">—</span>;
    }
    const mismatch = primary && finalM && primary !== finalM;
    return (
      <div className="flex flex-col items-center gap-0.5 max-w-[140px] mx-auto">
        {primary && (
          <span className="text-[10px] text-gray-500 leading-tight text-center" title="First successful HTML fetch used for detection">
            HTML: <span className="font-mono text-gray-700">{primary}</span>
          </span>
        )}
        {finalM && (
          <span title="Final method stored on this result (after verify / overrides)">
            {getMethodBadge(finalM)}
          </span>
        )}
        {mismatch && (
          <span className="text-[9px] text-amber-700 bg-amber-50 px-1 rounded">final changed</span>
        )}
      </div>
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
      <div className="pc-card">
        <div className="px-6 py-12 text-center">
          <div className="w-9 h-9 border-[3px] border-primary-100 border-t-primary-600 rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-primary-600 font-semibold text-sm">Scanning in progress…</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="pc-card">
        <div className="px-6 py-12 text-center">
          <div className="text-2xl mb-2">📊</div>
          <p className="text-gray-400 text-sm">No results yet — run a scan.</p>
        </div>
      </div>
    );
  }

  const filteredResults =
    statusFilter === 'all' ? results : results.filter(r => r.status === statusFilter);

  return (
    <div className="pc-card">
      <div className="pc-card-head">
        <div className="pc-card-title">Scan Results</div>
        <div className="flex items-center gap-2">
          {(['all', 'available', 'unavailable', 'error'] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setStatusFilter(k)}
              className={`pc-tag ${statusFilter === k ? 'pc-tag-on' : ''}`}
            >
              {k === 'all' ? 'All' : k}
            </button>
          ))}
          <span className="pc-card-count">{filteredResults.length}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr>
              <th className="px-3 py-3 w-10 bg-gray-50 border-b border-gray-100" />
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">URL</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Cart</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Buy Now</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Status</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Variants</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100" title="HTML = first fetch; badge = final method">Fetch / method</th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Time</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Scanned</th>
            </tr>
          </thead>
          <tbody>
            {filteredResults.map((result) => {
              const hasVariants = result.variants && Object.keys(result.variants).length > 0;
              const isExpanded  = expandedRows.has(result.id);

              return (
                <React.Fragment key={result.id}>
                  {/* Main row */}
                  <tr className={`border-b border-gray-50 transition-colors ${getRowBg(result.status)}`}>
                    {/* Expand toggle */}
                    <td className="px-3 py-4 text-center">
                      {hasVariants ? (
                        <button onClick={() => toggleRow(result.id)} className="text-primary-300 hover:text-primary-600" type="button">
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
                          className="text-[12px] text-gray-700 font-medium hover:text-primary-600 truncate block"
                          title={result.url}
                        >
                          {result.url}
                        </a>
                        <ExternalLink size={11} className="text-primary-300 hover:text-primary-600 flex-shrink-0" />
                      </div>
                      {result.error_message && (
                        <p className="text-[11px] text-red-600 mt-1 break-words">
                          {result.error_message}
                        </p>
                      )}
                      {result.unavailability_override && (
                        <p className="text-[11px] text-yellow-700 mt-1" title="Button found in HTML but out-of-stock signal detected">
                          OOS signal detected
                        </p>
                      )}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {result.add_to_cart
                        ? <CheckCircle className="text-green-500 mx-auto" size={20} />
                        : <XCircle className="text-gray-200 mx-auto" size={20} />}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {result.buy_now
                        ? <CheckCircle className="text-green-500 mx-auto" size={20} />
                        : <XCircle className="text-gray-200 mx-auto" size={20} />}
                    </td>

                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {getStatusIcon(result.status)}
                        <span className={`pc-pill ${getStatusBadge(result.status)}`}>
                          {result.status}
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      <button
                        onClick={() => hasVariants && toggleRow(result.id)}
                        className={hasVariants ? 'cursor-pointer' : 'cursor-default'}
                        type="button"
                      >
                        {getVariantSummary(result)}
                      </button>
                    </td>

                    <td className="px-4 py-4 text-center">
                      {getMethodDebugCell(result)}
                    </td>

                    <td className="px-4 py-4 text-center text-[12px] text-gray-400 whitespace-nowrap">
                      {result.response_time ? `${result.response_time}s` : '—'}
                    </td>

                    <td className="px-4 py-4 text-[12px] text-gray-400 whitespace-nowrap">
                      {formatDate(result.scanned_at)}
                    </td>
                  </tr>

                  {/* Variant detail row — expanded */}
                  {hasVariants && isExpanded && (
                    <tr className="bg-[#faf8ff]">
                      <td colSpan={9} className="px-8 py-4">
                        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-2">
                          Per-variant availability
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(result.variants!).map(([label, status]) => (
                            <span
                              key={label}
                              className={status === 'available' ? 'pc-pill-green' : 'pc-pill-red'}
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

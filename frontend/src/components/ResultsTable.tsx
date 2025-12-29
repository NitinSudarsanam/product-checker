import React from 'react';
import { CheckCircle, XCircle, AlertCircle, ExternalLink, Clock } from 'lucide-react';
import { ScanResult } from '@/lib/api';

interface ResultsTableProps {
  results: ScanResult[];
  loading: boolean;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, loading }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'unavailable':
        return <XCircle className="text-red-500" size={20} />;
      case 'error':
        return <AlertCircle className="text-yellow-500" size={20} />;
      default:
        return <Clock className="text-gray-400" size={20} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      available: 'bg-green-100 text-green-800',
      unavailable: 'bg-red-100 text-red-800',
      error: 'bg-yellow-100 text-yellow-800',
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading results...</p>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                URL
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Add to Cart
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Buy Now
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Response Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scanned At
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((result) => (
              <tr key={result.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-800 hover:underline max-w-md truncate block text-sm"
                      title={result.url}
                    >
                      {result.url}
                    </a>
                    <ExternalLink size={12} className="text-gray-400 flex-shrink-0" />
                  </div>
                  {result.error_message && (
                    <p className="text-xs text-red-600 mt-1" title={result.error_message}>
                      {result.error_message.substring(0, 50)}...
                    </p>
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  {result.add_to_cart ? (
                    <CheckCircle className="text-green-500 mx-auto" size={20} />
                  ) : (
                    <XCircle className="text-gray-300 mx-auto" size={20} />
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  {result.buy_now ? (
                    <CheckCircle className="text-green-500 mx-auto" size={20} />
                  ) : (
                    <XCircle className="text-gray-300 mx-auto" size={20} />
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    {getStatusIcon(result.status)}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(result.status)}`}>
                      {result.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-center text-sm text-gray-600">
                  {result.response_time ? `${result.response_time}s` : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {formatDate(result.scanned_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultsTable;

import React from 'react';
import { Trash2, ExternalLink } from 'lucide-react';
import { URL as URLType } from '@/lib/api';

interface URLListProps {
  urls: URLType[];
  onDelete: (id: string) => Promise<void>;
  loading: boolean;
}

const URLList: React.FC<URLListProps> = ({ urls, onDelete, loading }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (urls.length === 0) {
    return (
      <div className="pc-card">
        <div className="px-6 py-10 text-center">
          <div className="text-2xl mb-2">🔗</div>
          <p className="text-gray-400 text-sm">No URLs yet — add some on the left.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pc-card">
      <div className="pc-card-head">
        <div className="pc-card-title">Stored URLs</div>
        <span className="pc-card-count">{urls.length}</span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr>
              <th className="px-6 py-3 text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">URL</th>
              <th className="px-6 py-3 text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Group</th>
              <th className="px-6 py-3 text-left text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100">Added</th>
              <th className="px-6 py-3 text-center text-[11px] font-semibold text-gray-400 uppercase tracking-wide bg-gray-50 border-b border-gray-100 w-[60px]" />
            </tr>
          </thead>
          <tbody>
            {urls.map((url) => (
              <tr key={url.id} className="border-b border-gray-50 hover:bg-[#faf8ff] transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <a
                      href={url.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-700 font-medium max-w-md truncate block text-[12px] hover:text-primary-600"
                      title={url.url}
                    >
                      {url.url}
                    </a>
                    <ExternalLink size={12} className="text-primary-300 hover:text-primary-600 flex-shrink-0" />
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {url.group_name ? (
                    <span className="pc-pill-purple">
                      {url.group_name}
                    </span>
                  ) : (
                    <span className="text-gray-200">—</span>
                  )}
                </td>
                <td className="px-6 py-4 text-[12px] text-gray-400 whitespace-nowrap">
                  {formatDate(url.created_at)}
                </td>
                <td className="px-6 py-4 text-center">
                  <button
                    onClick={() => onDelete(url.id)}
                    disabled={loading}
                    className="pc-btn-danger pc-btn-sm !px-2 !py-1.5"
                    title="Delete URL"
                    type="button"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default URLList;

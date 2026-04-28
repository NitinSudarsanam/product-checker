import React from 'react';
import { Stats } from '@/lib/api';
import { BarChart3, CheckCircle, XCircle, AlertCircle, Globe } from 'lucide-react';

interface StatsCardProps {
  stats: Stats | null;
  loading: boolean;
}

const StatsCard: React.FC<StatsCardProps> = ({ stats, loading }) => {
  if (loading || !stats) {
    return (
      <div className="pc-card p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const statItems = [
    {
      label: 'Total URLs',
      value: stats.total_urls,
      icon: <Globe size={24} />,
      color: 'text-primary-600',
      bgColor: 'bg-primary-100',
    },
    {
      label: 'Total Scans',
      value: stats.total_scans,
      icon: <BarChart3 size={24} />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      label: 'Available',
      value: stats.available_count,
      icon: <CheckCircle size={24} />,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      label: 'Unavailable',
      value: stats.unavailable_count,
      icon: <XCircle size={24} />,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      label: 'Errors',
      value: stats.error_count,
      icon: <AlertCircle size={24} />,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statItems.map((item, index) => (
          <div
            key={index}
            className="bg-white rounded-[14px] px-5 py-4 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_4px_12px_rgba(0,0,0,0.03)] flex items-center gap-3"
          >
            <div className={`${item.bgColor} ${item.color} w-10 h-10 rounded-[11px] flex items-center justify-center flex-shrink-0`}>
              {item.icon}
            </div>
            <div>
              <div className="text-[22px] font-bold leading-none text-gray-900">{item.value}</div>
              <div className="text-[11px] text-gray-400 font-medium mt-1">{item.label}</div>
            </div>
          </div>
        ))}
    </div>
  );
};

export default StatsCard;

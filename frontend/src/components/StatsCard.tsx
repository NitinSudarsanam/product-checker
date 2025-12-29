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
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
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
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      label: 'Total Scans',
      value: stats.total_scans,
      icon: <BarChart3 size={24} />,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
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
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <BarChart3 size={24} />
        Statistics
      </h2>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statItems.map((item, index) => (
          <div
            key={index}
            className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className={`${item.bgColor} ${item.color} p-3 rounded-full mb-2`}>
              {item.icon}
            </div>
            <p className="text-2xl font-bold text-gray-800">{item.value}</p>
            <p className="text-sm text-gray-600 text-center">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatsCard;

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const IndexTicker = ({ data }) => {
  const getTrendIcon = (changePercent) => {
    return changePercent >= 0 ? 
      <TrendingUp className="w-3 h-3" /> : 
      <TrendingDown className="w-3 h-3" />;
  };

  const getTrendColor = (changePercent) => {
    return changePercent >= 0 ? 'text-green-400' : 'text-red-400';
  };

  return (
    <div className="bg-gray-900 border-b border-gray-700 overflow-hidden">
      <div className="flex animate-scroll">
        {[...data, ...data].map((item, index) => (
          <div key={`${item.symbol}-${index}`} className="flex items-center space-x-4 px-8 py-3 min-w-max">
            <span className="text-white font-bold text-sm">{item.symbol}</span>
            <span className="text-white text-sm">${item.price.toFixed(2)}</span>
            <div className={`flex items-center space-x-1 ${getTrendColor(item.changePercent)}`}>
              {getTrendIcon(item.changePercent)}
              <span className="text-xs font-medium">
                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)} ({item.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
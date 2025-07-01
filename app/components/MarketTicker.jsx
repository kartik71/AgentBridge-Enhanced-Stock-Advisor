import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const MarketTicker = () => {
  const [marketData, setMarketData] = useState([
    { symbol: 'S&P 500', price: 4847.88, change: 12.45, changePercent: 0.26 },
    { symbol: 'DOW', price: 37753.31, change: -45.22, changePercent: -0.12 },
    { symbol: 'NASDAQ', price: 15181.92, change: 89.76, changePercent: 0.59 },
    { symbol: 'RUSSELL', price: 2089.44, change: 5.33, changePercent: 0.26 },
    { symbol: 'VIX', price: 13.22, change: -0.87, changePercent: -6.17 },
    { symbol: 'GOLD', price: 2034.50, change: 8.75, changePercent: 0.43 },
    { symbol: 'OIL', price: 73.25, change: -1.20, changePercent: -1.61 },
    { symbol: 'USD/EUR', price: 1.0875, change: 0.0025, changePercent: 0.23 }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketData(prev => prev.map(item => {
        const priceChange = (Math.random() - 0.5) * (item.price * 0.002); // 0.2% max change
        const newPrice = Math.max(0, item.price + priceChange);
        const newChange = item.change + priceChange;
        const newChangePercent = (newChange / (newPrice - newChange)) * 100;
        
        return {
          ...item,
          price: parseFloat(newPrice.toFixed(2)),
          change: parseFloat(newChange.toFixed(2)),
          changePercent: parseFloat(newChangePercent.toFixed(2))
        };
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 border-b border-gray-700 overflow-hidden">
      <div className="flex animate-scroll">
        {[...marketData, ...marketData].map((item, index) => (
          <div key={`${item.symbol}-${index}`} className="flex items-center space-x-4 px-8 py-3 min-w-max">
            <span className="text-white font-bold text-sm">{item.symbol}</span>
            <span className="text-white text-sm">{item.price.toFixed(item.symbol.includes('/') ? 4 : 2)}</span>
            <div className={`flex items-center space-x-1 ${
              item.change >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {item.change >= 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
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
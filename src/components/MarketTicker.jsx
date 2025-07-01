import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const MarketTicker = () => {
  const [marketData, setMarketData] = useState([
    { symbol: 'S&P 500', price: 4847.88, change: 12.45, changePercent: 0.26, volume: '2.5B' },
    { symbol: 'NASDAQ', price: 15181.92, change: 89.76, changePercent: 0.59, volume: '3.2B' },
    { symbol: 'DOW', price: 37753.31, change: -45.22, changePercent: -0.12, volume: '1.8B' },
    { symbol: 'RUSSELL 2000', price: 2089.44, change: 5.33, changePercent: 0.26, volume: '1.2B' },
    { symbol: 'VIX', price: 13.22, change: -0.87, changePercent: -6.17, volume: '800M' },
    { symbol: 'GOLD', price: 2034.50, change: 8.75, changePercent: 0.43, volume: '1.1B' },
    { symbol: 'OIL (WTI)', price: 73.25, change: -1.20, changePercent: -1.61, volume: '950M' },
    { symbol: 'USD/EUR', price: 1.0875, change: 0.0025, changePercent: 0.23, volume: '4.2B' },
    { symbol: 'BTC', price: 43250.00, change: 1250.00, changePercent: 2.98, volume: '2.8B' },
    { symbol: '10Y TREASURY', price: 4.325, change: 0.025, changePercent: 0.58, volume: '1.5B' }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketData(prev => prev.map(item => {
        const maxChange = item.price * 0.002; // 0.2% max change
        const priceChange = (Math.random() - 0.5) * maxChange;
        const newPrice = Math.max(0, item.price + priceChange);
        const newChange = item.change + priceChange;
        const newChangePercent = (newChange / (newPrice - newChange)) * 100;
        
        return {
          ...item,
          price: parseFloat(newPrice.toFixed(item.symbol.includes('USD') ? 4 : 2)),
          change: parseFloat(newChange.toFixed(item.symbol.includes('USD') ? 4 : 2)),
          changePercent: parseFloat(newChangePercent.toFixed(2))
        };
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getTrendIcon = (changePercent) => {
    if (changePercent > 0.1) return <TrendingUp className="w-3 h-3" />;
    if (changePercent < -0.1) return <TrendingDown className="w-3 h-3" />;
    return <Minus className="w-3 h-3" />;
  };

  const getTrendColor = (changePercent) => {
    if (changePercent > 0.1) return 'text-green-400';
    if (changePercent < -0.1) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <div className="bg-gray-900 border-b border-gray-700 overflow-hidden">
      <div className="flex animate-scroll">
        {[...marketData, ...marketData].map((item, index) => (
          <div key={`${item.symbol}-${index}`} className="flex items-center space-x-4 px-6 py-3 min-w-max border-r border-gray-700 last:border-r-0">
            <div className="flex flex-col">
              <span className="text-white font-bold text-sm">{item.symbol}</span>
              <span className="text-gray-400 text-xs">{item.volume}</span>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-white text-sm font-semibold">
                {item.symbol.includes('USD') ? item.price.toFixed(4) : 
                 item.symbol === 'BTC' ? `$${item.price.toLocaleString()}` :
                 item.symbol === '10Y TREASURY' ? `${item.price}%` :
                 `$${item.price.toFixed(2)}`}
              </span>
              <div className={`flex items-center space-x-1 ${getTrendColor(item.changePercent)}`}>
                {getTrendIcon(item.changePercent)}
                <span className="text-xs font-medium">
                  {item.change >= 0 ? '+' : ''}{item.change.toFixed(item.symbol.includes('USD') ? 4 : 2)} 
                  ({item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
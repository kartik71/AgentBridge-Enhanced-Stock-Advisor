import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Star, RefreshCw } from 'lucide-react';

export const PortfolioRecommendations = () => {
  const [recommendations, setRecommendations] = useState([
    {
      symbol: 'AAPL',
      action: 'BUY',
      targetPrice: 205.00,
      currentPrice: 192.35,
      confidence: 87,
      reason: 'Strong Q4 earnings, iPhone 15 cycle momentum',
      risk: 'LOW',
      sector: 'Technology',
      allocation: 25
    },
    {
      symbol: 'NVDA',
      action: 'HOLD',
      targetPrice: 480.00,
      currentPrice: 465.20,
      confidence: 72,
      reason: 'AI momentum continues, but valuation stretched',
      risk: 'HIGH',
      sector: 'Technology',
      allocation: 20
    },
    {
      symbol: 'TSLA',
      action: 'SELL',
      targetPrice: 180.00,
      currentPrice: 198.50,
      confidence: 65,
      reason: 'Overvalued, increasing EV competition',
      risk: 'HIGH',
      sector: 'Automotive',
      allocation: 15
    },
    {
      symbol: 'JNJ',
      action: 'BUY',
      targetPrice: 175.00,
      currentPrice: 165.20,
      confidence: 81,
      reason: 'Defensive play, strong dividend yield',
      risk: 'LOW',
      sector: 'Healthcare',
      allocation: 20
    },
    {
      symbol: 'MSFT',
      action: 'BUY',
      targetPrice: 415.00,
      currentPrice: 398.75,
      confidence: 83,
      reason: 'Azure growth, AI integration driving revenue',
      risk: 'MEDIUM',
      sector: 'Technology',
      allocation: 20
    }
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Simulate real-time price updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRecommendations(prev => prev.map(rec => ({
        ...rec,
        currentPrice: rec.currentPrice + (Math.random() - 0.5) * 2,
        confidence: Math.max(50, Math.min(95, rec.confidence + (Math.random() - 0.5) * 5))
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const refreshRecommendations = async () => {
    setIsRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setLastUpdated(new Date());
    setIsRefreshing(false);
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'BUY': return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'SELL': return <TrendingDown className="w-4 h-4 text-red-400" />;
      case 'HOLD': return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      default: return null;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'BUY': return 'text-green-400 bg-green-400/10 border-green-400/20';
      case 'SELL': return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'HOLD': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      default: return 'text-gray-400';
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LOW': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'HIGH': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getPotentialReturn = (current, target) => {
    return ((target - current) / current * 100).toFixed(1);
  };

  return (
    <div className="space-y-4">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs text-gray-400">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={refreshRecommendations}
          disabled={isRefreshing}
          className="flex items-center space-x-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-xs rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>{isRefreshing ? 'Updating...' : 'Refresh'}</span>
        </button>
      </div>

      {/* Recommendations */}
      {recommendations.map((rec, index) => (
        <div key={index} className="bg-gray-800 border border-gray-600 rounded-lg p-4 hover:border-gray-500 transition-all duration-200 hover:shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <span className="text-white font-bold text-lg">{rec.symbol}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 border ${getActionColor(rec.action)}`}>
                {getActionIcon(rec.action)}
                <span>{rec.action}</span>
              </span>
              <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
                {rec.sector}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Star className="w-4 h-4 text-yellow-400" />
              <span className="text-yellow-400 font-medium text-sm">{rec.confidence}%</span>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-3">
            <div>
              <span className="text-gray-400 text-xs">Current</span>
              <p className="text-white font-semibold">${rec.currentPrice.toFixed(2)}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Target</span>
              <p className="text-white font-semibold">${rec.targetPrice.toFixed(2)}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Potential</span>
              <p className={`font-semibold ${
                getPotentialReturn(rec.currentPrice, rec.targetPrice) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {getPotentialReturn(rec.currentPrice, rec.targetPrice) >= 0 ? '+' : ''}
                {getPotentialReturn(rec.currentPrice, rec.targetPrice)}%
              </p>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-3">
            <p className="text-gray-300 text-sm flex-1 mr-4">{rec.reason}</p>
            <div className="flex items-center space-x-3">
              <span className={`text-xs font-medium ${getRiskColor(rec.risk)}`}>
                {rec.risk} RISK
              </span>
              <span className="text-xs text-gray-400">
                {rec.allocation}% allocation
              </span>
            </div>
          </div>
          
          {/* Confidence bar */}
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Confidence</span>
              <span>{rec.confidence}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  rec.confidence >= 80 ? 'bg-green-500' : 
                  rec.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${rec.confidence}%` }}
              />
            </div>
          </div>
        </div>
      ))}

      {/* Portfolio Summary */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 mt-6">
        <h4 className="text-white font-semibold mb-3">Portfolio Summary</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Total Recommendations</span>
            <span className="text-white">{recommendations.length}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Avg Confidence</span>
            <span className="text-white">
              {(recommendations.reduce((acc, rec) => acc + rec.confidence, 0) / recommendations.length).toFixed(0)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Buy Signals</span>
            <span className="text-green-400">
              {recommendations.filter(rec => rec.action === 'BUY').length}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Sell Signals</span>
            <span className="text-red-400">
              {recommendations.filter(rec => rec.action === 'SELL').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Star, RefreshCw, DollarSign, Target, PieChart } from 'lucide-react';

export const PortfolioRecommendations = ({ 
  recommendations, 
  isGenerating, 
  userConfig, 
  autonomousMode 
}) => {
  const [sortBy, setSortBy] = useState('confidence');

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
      case 'Low': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'High': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getPotentialReturn = (current, target) => {
    return ((target - current) / current * 100).toFixed(1);
  };

  const sortedRecommendations = [...recommendations].sort((a, b) => {
    switch (sortBy) {
      case 'confidence': return b.confidence - a.confidence;
      case 'potential': return getPotentialReturn(b.currentPrice, b.targetPrice) - getPotentialReturn(a.currentPrice, a.targetPrice);
      case 'allocation': return b.allocation - a.allocation;
      default: return 0;
    }
  });

  const totalAllocation = recommendations.reduce((sum, rec) => sum + rec.allocation, 0);
  const avgConfidence = recommendations.length > 0 
    ? recommendations.reduce((sum, rec) => sum + rec.confidence, 0) / recommendations.length 
    : 0;

  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
        <div className="text-center">
          <h3 className="text-lg font-semibold text-white mb-2">Generating Recommendations</h3>
          <p className="text-gray-400">AI agents are analyzing market data and optimizing your portfolio...</p>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <PieChart className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">No Recommendations Yet</h3>
        <p className="text-gray-400 mb-4">
          {autonomousMode 
            ? "AI agents will automatically generate recommendations based on your configuration."
            : "Click 'Generate Recommendations' to get AI-powered portfolio suggestions."
          }
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Portfolio Recommendations</h3>
          <p className="text-sm text-gray-400">
            Based on ${userConfig.budget.toLocaleString()} budget • {userConfig.riskLevel} risk • {userConfig.timeframe}-term
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="confidence">Sort by Confidence</option>
            <option value="potential">Sort by Potential Return</option>
            <option value="allocation">Sort by Allocation</option>
          </select>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h4 className="text-white font-semibold mb-3 flex items-center">
          <PieChart className="w-4 h-4 mr-2 text-blue-400" />
          Portfolio Summary
        </h4>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{recommendations.length}</div>
            <div className="text-gray-400">Recommendations</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{avgConfidence.toFixed(0)}%</div>
            <div className="text-gray-400">Avg Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">{totalAllocation}%</div>
            <div className="text-gray-400">Total Allocation</div>
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {sortedRecommendations.map((rec, index) => (
          <div key={index} className="bg-gray-800 border border-gray-600 rounded-lg p-5 hover:border-gray-500 transition-all duration-200 hover:shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div>
                  <span className="text-white font-bold text-xl">{rec.symbol}</span>
                  <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded ml-3">
                    {rec.sector}
                  </span>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1 border ${getActionColor(rec.action)}`}>
                  {getActionIcon(rec.action)}
                  <span>{rec.action}</span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Star className="w-4 h-4 text-yellow-400" />
                <span className="text-yellow-400 font-bold text-lg">{rec.confidence}%</span>
              </div>
            </div>
            
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div>
                <span className="text-gray-400 text-xs">Current Price</span>
                <p className="text-white font-semibold text-lg">${rec.currentPrice.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-gray-400 text-xs">Target Price</span>
                <p className="text-white font-semibold text-lg">${rec.targetPrice.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-gray-400 text-xs">Potential Return</span>
                <p className={`font-semibold text-lg ${
                  getPotentialReturn(rec.currentPrice, rec.targetPrice) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {getPotentialReturn(rec.currentPrice, rec.targetPrice) >= 0 ? '+' : ''}
                  {getPotentialReturn(rec.currentPrice, rec.targetPrice)}%
                </p>
              </div>
              <div>
                <span className="text-gray-400 text-xs">Allocation</span>
                <p className="text-purple-400 font-semibold text-lg">{rec.allocation}%</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-300 text-sm flex-1 mr-4">{rec.reason}</p>
              <div className="flex items-center space-x-4">
                <span className={`text-xs font-medium px-2 py-1 rounded ${getRiskColor(rec.risk)} bg-opacity-20`}>
                  {rec.risk.toUpperCase()} RISK
                </span>
                <span className="text-xs text-gray-400">
                  ${((userConfig.budget * rec.allocation) / 100).toLocaleString()} investment
                </span>
              </div>
            </div>
            
            {/* Confidence Bar */}
            <div>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>AI Confidence Level</span>
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
      </div>

      {/* Action Summary */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
        <h4 className="text-white font-semibold mb-3">Action Summary</h4>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Buy Signals</span>
            <span className="text-green-400 font-semibold">
              {recommendations.filter(rec => rec.action === 'BUY').length}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Hold Signals</span>
            <span className="text-yellow-400 font-semibold">
              {recommendations.filter(rec => rec.action === 'HOLD').length}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Sell Signals</span>
            <span className="text-red-400 font-semibold">
              {recommendations.filter(rec => rec.action === 'SELL').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
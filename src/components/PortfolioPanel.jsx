import React from 'react';
import { WidgetPanel } from './AGUIComponents';
import { PieChart, DollarSign, Target } from 'lucide-react';

export const PortfolioPanel = ({ portfolio, budget, executionMode }) => {
  const totalAllocation = portfolio.reduce((sum, stock) => sum + stock.allocation, 0);
  const avgConfidence = portfolio.reduce((sum, stock) => sum + stock.confidence, 0) / portfolio.length;

  return (
    <WidgetPanel title="Portfolio Recommendations" status="active">
      <div className="space-y-6">
        {/* Summary */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-400">{portfolio.length}</div>
              <div className="text-gray-400 text-sm">Stocks</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">{avgConfidence.toFixed(0)}%</div>
              <div className="text-gray-400 text-sm">Avg Confidence</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400">${budget.toLocaleString()}</div>
              <div className="text-gray-400 text-sm">Total Budget</div>
            </div>
          </div>
        </div>

        {/* Mode Indicator */}
        <div className={`p-3 rounded-lg border ${
          executionMode === 'Autonomous' 
            ? 'bg-green-900/20 border-green-600' 
            : 'bg-yellow-900/20 border-yellow-600'
        }`}>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              executionMode === 'Autonomous' ? 'bg-green-400' : 'bg-yellow-400'
            }`} />
            <span className={`text-sm font-medium ${
              executionMode === 'Autonomous' ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {executionMode} Mode Active
            </span>
          </div>
        </div>

        {/* Stock Recommendations */}
        <div className="space-y-3">
          {portfolio.map((stock, index) => (
            <div key={index} className="bg-gray-800 border border-gray-600 rounded-lg p-4 hover:border-gray-500 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-white font-bold text-lg">{stock.symbol}</span>
                  <span className="text-purple-400 font-semibold">{stock.allocation}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Target className="w-4 h-4 text-yellow-400" />
                  <span className="text-yellow-400 font-medium">{stock.confidence}%</span>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Price</span>
                  <p className="text-white font-semibold">${stock.price.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-gray-400">Investment</span>
                  <p className="text-green-400 font-semibold">
                    ${((budget * stock.allocation) / 100).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-gray-400">Shares</span>
                  <p className="text-blue-400 font-semibold">
                    {Math.floor((budget * stock.allocation) / 100 / stock.price)}
                  </p>
                </div>
              </div>
              
              {/* Confidence Bar */}
              <div className="mt-3">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      stock.confidence >= 80 ? 'bg-green-500' : 
                      stock.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${stock.confidence}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </WidgetPanel>
  );
};
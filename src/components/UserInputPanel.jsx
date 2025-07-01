import React from 'react';
import { WidgetPanel, Dropdown } from './AGUIComponents';
import { DollarSign, Target, TrendingUp, Zap } from 'lucide-react';

export const UserInputPanel = ({ 
  config, 
  onChange, 
  onGenerateRecommendations, 
  autonomousMode, 
  isGenerating 
}) => {
  const handleBudgetChange = (e) => {
    const value = parseFloat(e.target.value) || 0;
    onChange({ budget: value });
  };

  const goalOptions = [
    'Growth', 
    'Income', 
    'Balanced', 
    'Conservative', 
    'Aggressive Growth'
  ];

  return (
    <WidgetPanel title="Investment Configuration" status="active">
      <div className="space-y-6">
        {/* Budget Input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
            <DollarSign className="w-4 h-4 mr-2 text-green-400" />
            Investment Budget
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">$</span>
            <input
              type="number"
              value={config.budget}
              onChange={handleBudgetChange}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-8 pr-3 py-3 text-white text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="50,000"
              min="1000"
              max="10000000"
              step="1000"
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Minimum: $1,000 • Maximum: $10,000,000
          </p>
        </div>

        {/* Timeframe Selection */}
        <Dropdown
          label="Investment Timeframe"
          options={['Short', 'Medium', 'Long']}
          value={config.timeframe}
          onChange={(value) => onChange({ timeframe: value })}
          icon={<Target className="w-4 h-4 text-blue-400" />}
        />

        {/* Risk Level Selection */}
        <Dropdown
          label="Risk Tolerance"
          options={['Low', 'Medium', 'High']}
          value={config.riskLevel}
          onChange={(value) => onChange({ riskLevel: value })}
          icon={<TrendingUp className="w-4 h-4 text-yellow-400" />}
        />

        {/* Investment Goals */}
        <Dropdown
          label="Investment Goals"
          options={goalOptions}
          value={config.goals}
          onChange={(value) => onChange({ goals: value })}
          icon={<Target className="w-4 h-4 text-purple-400" />}
        />

        {/* Generate Button (HITL Mode) */}
        {!autonomousMode && (
          <div className="pt-4">
            <button
              onClick={onGenerateRecommendations}
              disabled={isGenerating}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Generate Recommendations</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Configuration Summary */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Configuration Summary</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Budget:</span>
              <span className="text-green-400 font-semibold">${config.budget.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Timeframe:</span>
              <span className="text-blue-400">{config.timeframe}-term</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Risk Level:</span>
              <span className={`${
                config.riskLevel === 'Low' ? 'text-green-400' :
                config.riskLevel === 'Medium' ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {config.riskLevel}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Goals:</span>
              <span className="text-purple-400">{config.goals}</span>
            </div>
          </div>
        </div>
      </div>
    </WidgetPanel>
  );
};
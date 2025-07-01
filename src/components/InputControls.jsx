import React from 'react';
import { WidgetPanel, Dropdown, ToggleSwitch } from './AGUIComponents';
import { DollarSign, Clock, Shield } from 'lucide-react';

export const InputControls = ({ budget, timeframe, riskLevel, onChange }) => {
  return (
    <WidgetPanel title="Investment Configuration" status="active">
      <div className="space-y-6">
        {/* Budget Input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
            <DollarSign className="w-4 h-4 mr-2 text-green-400" />
            Budget (USD)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">$</span>
            <input
              type="number"
              value={budget}
              onChange={(e) => onChange('budget', parseInt(e.target.value) || 0)}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-8 pr-3 py-3 text-white text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="50,000"
              min="1000"
              step="1000"
            />
          </div>
        </div>

        {/* Timeframe Dropdown */}
        <Dropdown
          label="Investment Timeframe"
          options={['Short', 'Medium', 'Long']}
          value={timeframe}
          onChange={(value) => onChange('timeframe', value)}
          icon={<Clock className="w-4 h-4 text-blue-400" />}
        />

        {/* Risk Level Toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3 flex items-center">
            <Shield className="w-4 h-4 mr-2 text-yellow-400" />
            Risk Level
          </label>
          <div className="space-y-2">
            {['Low', 'Medium', 'High'].map((level) => (
              <div key={level} className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-600">
                <span className="text-white text-sm">{level} Risk</span>
                <ToggleSwitch
                  enabled={riskLevel === level}
                  onChange={() => onChange('riskLevel', level)}
                  size="sm"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Configuration Summary */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Current Configuration</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Budget:</span>
              <span className="text-green-400 font-semibold">${budget.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Timeframe:</span>
              <span className="text-blue-400">{timeframe}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Risk:</span>
              <span className={`${
                riskLevel === 'Low' ? 'text-green-400' :
                riskLevel === 'Medium' ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {riskLevel}
              </span>
            </div>
          </div>
        </div>
      </div>
    </WidgetPanel>
  );
};
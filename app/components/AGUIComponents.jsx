import React from 'react';
import { Activity, CheckCircle, XCircle, ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';

// AG-UI WidgetPanel Component
export const WidgetPanel = ({ 
  title, 
  children, 
  className = '', 
  status = 'active' 
}) => {
  const statusClasses = {
    active: 'border-l-green-400',
    inactive: 'border-l-red-400',
    warning: 'border-l-yellow-400'
  };

  return (
    <div className={`bg-gray-900 border border-gray-700 ${statusClasses[status]} border-l-4 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">{title}</h3>
        <div className={`w-2 h-2 rounded-full ${
          status === 'active' ? 'bg-green-400' : 
          status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
        }`} />
      </div>
      {children}
    </div>
  );
};

// AG-UI AgentCard Component
export const AgentCard = ({
  name,
  type,
  status,
  mcpStatus,
  onToggle,
  isActive,
  performance
}) => {
  const statusIcon = {
    connected: <CheckCircle className="w-4 h-4 text-green-400" />,
    disconnected: <XCircle className="w-4 h-4 text-red-400" />,
    processing: <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
  };

  return (
    <div className={`bg-gray-800 border border-gray-600 rounded-lg p-4 transition-all duration-200 hover:border-gray-500 hover:shadow-lg ${
      isActive ? 'ring-2 ring-blue-400' : ''
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-white font-semibold text-sm">{name}</h4>
          <p className="text-gray-400 text-xs">{type}</p>
        </div>
        {statusIcon[status]}
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">MCP Server</span>
          <span className={`${mcpStatus ? 'text-green-400' : 'text-red-400'}`}>
            {mcpStatus ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        {performance !== undefined && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Performance</span>
            <span className={`flex items-center ${performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {performance >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
              {performance.toFixed(1)}%
            </span>
          </div>
        )}
        
        <button
          onClick={onToggle}
          className={`w-full py-2 px-3 rounded text-xs font-medium transition-colors ${
            isActive 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {isActive ? 'Active' : 'Activate'}
        </button>
      </div>
    </div>
  );
};

// AG-UI ToggleSwitch Component
export const ToggleSwitch = ({
  enabled,
  onChange,
  label,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'w-8 h-4',
    md: 'w-10 h-5',
    lg: 'w-12 h-6'
  };

  const thumbSizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4', 
    lg: 'w-5 h-5'
  };

  const translateClasses = {
    sm: enabled ? 'translate-x-4' : 'translate-x-0.5',
    md: enabled ? 'translate-x-5' : 'translate-x-0.5',
    lg: enabled ? 'translate-x-6' : 'translate-x-0.5'
  };

  return (
    <div className="flex items-center space-x-3">
      <button
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex items-center ${sizeClasses[size]} rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
          enabled ? 'bg-blue-600' : 'bg-gray-600'
        }`}
      >
        <span
          className={`inline-block ${thumbSizeClasses[size]} rounded-full bg-white transition-transform ${translateClasses[size]}`}
        />
      </button>
      {label && <span className="text-white text-sm font-medium">{label}</span>}
    </div>
  );
};

// AG-UI Dropdown Component
export const Dropdown = ({
  options,
  value,
  onChange,
  label,
  className = ''
}) => {
  return (
    <div className={`${className}`}>
      <label className="block text-sm font-medium text-gray-300 mb-2">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option.charAt(0).toUpperCase() + option.slice(1).replace('_', ' ')}
          </option>
        ))}
      </select>
    </div>
  );
};

// A2A Toggle Component
export const A2AToggle = ({
  fromAgent,
  toAgent,
  enabled,
  onChange
}) => {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-800 border border-gray-600 rounded-lg hover:border-gray-500 transition-colors">
      <div className="flex items-center space-x-2">
        <span className="text-white text-sm font-medium">{fromAgent}</span>
        <ArrowUpDown className="w-4 h-4 text-gray-400" />
        <span className="text-white text-sm font-medium">{toAgent}</span>
      </div>
      <ToggleSwitch
        enabled={enabled}
        onChange={onChange}
        label=""
        size="sm"
      />
    </div>
  );
};
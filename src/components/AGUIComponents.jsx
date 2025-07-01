import React from 'react';
import { Activity, CheckCircle, XCircle, Wifi, WifiOff, ArrowUpDown, Network } from 'lucide-react';

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
  mcpConnected,
  onToggle,
  isActive,
  performance,
  lastUpdate,
  description,
  icon,
  a2aEnabled
}) => {
  const statusIcon = {
    connected: <CheckCircle className="w-4 h-4 text-green-400" />,
    disconnected: <XCircle className="w-4 h-4 text-red-400" />,
    processing: <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className={`bg-gray-800 border border-gray-600 rounded-lg p-4 transition-all duration-200 hover:border-gray-500 hover:shadow-lg ${
      isActive ? 'ring-2 ring-blue-400' : ''
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {icon && <div className="flex-shrink-0">{icon}</div>}
          <div>
            <h4 className="text-white font-semibold text-sm">{name}</h4>
            <p className="text-gray-400 text-xs">{type}</p>
          </div>
        </div>
        {statusIcon[status]}
      </div>
      
      {description && (
        <p className="text-gray-400 text-xs mb-3 leading-relaxed">{description}</p>
      )}
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">MCP Server</span>
          <div className="flex items-center space-x-1">
            {mcpConnected ? <Wifi className="w-3 h-3 text-green-400" /> : <WifiOff className="w-3 h-3 text-red-400" />}
            <span className={`${mcpConnected ? 'text-green-400' : 'text-red-400'}`}>
              {mcpConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">A2A Mode</span>
          <div className="flex items-center space-x-1">
            <Network className={`w-3 h-3 ${a2aEnabled ? 'text-blue-400' : 'text-gray-400'}`} />
            <span className={`${a2aEnabled ? 'text-blue-400' : 'text-gray-400'}`}>
              {a2aEnabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
        
        {performance !== undefined && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Performance</span>
            <span className={`flex items-center font-medium ${performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {performance >= 0 ? '+' : ''}{performance.toFixed(1)}%
            </span>
          </div>
        )}
        
        {lastUpdate && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Last Update</span>
            <span className="text-blue-400">{formatTime(lastUpdate)}</span>
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
  size = 'md',
  disabled = false
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
        onClick={() => !disabled && onChange(!enabled)}
        disabled={disabled}
        className={`relative inline-flex items-center ${sizeClasses[size]} rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
          disabled 
            ? 'bg-gray-600 cursor-not-allowed' 
            : enabled 
              ? 'bg-blue-600' 
              : 'bg-gray-600'
        }`}
      >
        <span
          className={`inline-block ${thumbSizeClasses[size]} rounded-full bg-white transition-transform ${
            disabled ? 'opacity-50' : ''
          } ${translateClasses[size]}`}
        />
      </button>
      {label && (
        <span className={`text-sm font-medium ${
          disabled ? 'text-gray-500' : 'text-white'
        }`}>
          {label}
        </span>
      )}
    </div>
  );
};

// AG-UI Dropdown Component
export const Dropdown = ({
  options,
  value,
  onChange,
  label,
  className = '',
  icon,
  disabled = false
}) => {
  return (
    <div className={`${className}`}>
      <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
        {icon && <span className="mr-2">{icon}</span>}
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => !disabled && onChange(e.target.value)}
        disabled={disabled}
        className={`w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
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
  onChange,
  status = 'active',
  disabled = false
}) => {
  const getStatusColor = () => {
    if (disabled || !enabled) return 'border-gray-600 bg-gray-600/10';
    switch (status) {
      case 'active': return 'border-green-400 bg-green-400/10';
      case 'processing': return 'border-blue-400 bg-blue-400/10';
      case 'error': return 'border-red-400 bg-red-400/10';
      default: return 'border-gray-600 bg-gray-600/10';
    }
  };

  return (
    <div className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${getStatusColor()}`}>
      <div className="flex items-center space-x-2">
        <span className={`text-sm font-medium ${disabled ? 'text-gray-500' : 'text-white'}`}>
          {fromAgent}
        </span>
        <ArrowUpDown className={`w-4 h-4 ${disabled ? 'text-gray-500' : 'text-gray-400'}`} />
        <span className={`text-sm font-medium ${disabled ? 'text-gray-500' : 'text-white'}`}>
          {toAgent}
        </span>
      </div>
      <ToggleSwitch
        enabled={enabled}
        onChange={onChange}
        size="sm"
        disabled={disabled}
      />
    </div>
  );
};
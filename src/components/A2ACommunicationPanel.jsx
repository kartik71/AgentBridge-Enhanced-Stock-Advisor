import React from 'react';
import { WidgetPanel, ToggleSwitch } from './AGUIComponents';
import { Network, Zap, ArrowRight, Activity, CheckCircle, XCircle } from 'lucide-react';

export const A2ACommunicationPanel = ({ 
  connections, 
  onToggleConnection, 
  enabled, 
  onToggleA2A,
  agentStatuses = {}
}) => {
  const activeConnections = connections.filter(conn => conn.enabled && enabled).length;
  const totalConnections = connections.length;

  const getConnectionStatus = (connection) => {
    const fromStatus = agentStatuses[connection.from] || 'disconnected';
    const toStatus = agentStatuses[connection.to] || 'disconnected';
    
    if (!enabled || !connection.enabled) return 'disabled';
    if (fromStatus === 'connected' && toStatus === 'connected') return 'active';
    if (fromStatus === 'processing' || toStatus === 'processing') return 'processing';
    return 'error';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-3 h-3 text-green-400" />;
      case 'processing': return <Activity className="w-3 h-3 text-blue-400 animate-pulse" />;
      case 'error': return <XCircle className="w-3 h-3 text-red-400" />;
      case 'disabled': return <div className="w-3 h-3 rounded-full bg-gray-600" />;
      default: return <div className="w-3 h-3 rounded-full bg-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'border-green-400 bg-green-400/10';
      case 'processing': return 'border-blue-400 bg-blue-400/10';
      case 'error': return 'border-red-400 bg-red-400/10';
      case 'disabled': return 'border-gray-600 bg-gray-600/10';
      default: return 'border-gray-600 bg-gray-600/10';
    }
  };

  return (
    <WidgetPanel title="Agent-to-Agent Communication" status={enabled ? "active" : "inactive"}>
      <div className="space-y-4">
        {/* A2A Master Toggle */}
        <div className="flex items-center justify-between p-3 bg-gray-800 border border-gray-600 rounded-lg">
          <div className="flex items-center space-x-3">
            <Network className="w-5 h-5 text-blue-400" />
            <div>
              <span className="text-white font-medium">A2A Communication</span>
              <p className="text-xs text-gray-400">Enable agent-to-agent data sharing</p>
            </div>
          </div>
          <ToggleSwitch
            enabled={enabled}
            onChange={onToggleA2A}
            size="md"
          />
        </div>

        {/* Connection Status Overview */}
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300 text-sm font-medium">Network Status</span>
            <span className={`text-sm font-semibold ${
              enabled ? 'text-green-400' : 'text-gray-400'
            }`}>
              {enabled ? `${activeConnections}/${totalConnections} Active` : 'Disabled'}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                enabled ? 'bg-green-500' : 'bg-gray-600'
              }`}
              style={{ width: enabled ? `${(activeConnections / totalConnections) * 100}%` : '0%' }}
            />
          </div>
        </div>

        {/* Individual Connections */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300 flex items-center">
            <Zap className="w-4 h-4 mr-2 text-yellow-400" />
            Communication Channels
          </h4>
          
          {connections.map((connection, index) => {
            const status = getConnectionStatus(connection);
            
            return (
              <div 
                key={index} 
                className={`p-3 rounded-lg border transition-all duration-200 ${getStatusColor(status)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(status)}
                      <span className="text-white text-sm font-medium">{connection.from}</span>
                    </div>
                    
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-white text-sm font-medium">{connection.to}</span>
                      {getStatusIcon(status)}
                    </div>
                  </div>
                  
                  <ToggleSwitch
                    enabled={connection.enabled && enabled}
                    onChange={() => onToggleConnection(index)}
                    size="sm"
                    disabled={!enabled}
                  />
                </div>
                
                {/* Connection Description */}
                <div className="mt-2 text-xs text-gray-400">
                  {connection.description || getConnectionDescription(connection.from, connection.to)}
                </div>
                
                {/* Status Indicator */}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-gray-400">Status:</span>
                  <span className={`font-medium ${
                    status === 'active' ? 'text-green-400' :
                    status === 'processing' ? 'text-blue-400' :
                    status === 'error' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* A2A Benefits */}
        <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-3">
          <h5 className="text-blue-400 font-medium text-sm mb-2">A2A Benefits</h5>
          <ul className="text-xs text-blue-300 space-y-1">
            <li>• Real-time market data integration</li>
            <li>• Enhanced timing analysis</li>
            <li>• Automated compliance checking</li>
            <li>• Improved recommendation accuracy</li>
          </ul>
        </div>

        {/* Performance Metrics */}
        {enabled && (
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
            <h5 className="text-gray-300 font-medium text-sm mb-2">A2A Performance</h5>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Latency:</span>
                <span className="text-green-400">~150ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Success Rate:</span>
                <span className="text-green-400">98.5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Data Quality:</span>
                <span className="text-green-400">High</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Last Sync:</span>
                <span className="text-blue-400">2s ago</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </WidgetPanel>
  );
};

// Helper function to get connection descriptions
const getConnectionDescription = (from, to) => {
  const descriptions = {
    'Index Scraper → Portfolio Optimizer': 'Real-time market data and price feeds',
    'Portfolio Optimizer → Timing Advisor': 'Portfolio allocation for timing analysis',
    'Timing Advisor → Compliance Logger': 'Timing recommendations for compliance review',
    'Compliance Logger → Portfolio Optimizer': 'Compliance feedback and risk alerts'
  };
  
  return descriptions[`${from} → ${to}`] || 'Data exchange and coordination';
};
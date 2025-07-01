import React from 'react';
import { WidgetPanel } from './AGUIComponents';
import { History, CheckCircle, XCircle, Clock, AlertTriangle, Bot } from 'lucide-react';

export const HITLHistoryPanel = ({ decisionHistory = [] }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'rejected': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'timeout': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'bypassed': return <Bot className="w-4 h-4 text-blue-400" />;
      default: return <AlertTriangle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-400 bg-green-400/10';
      case 'rejected': return 'text-red-400 bg-red-400/10';
      case 'timeout': return 'text-yellow-400 bg-yellow-400/10';
      case 'bypassed': return 'text-blue-400 bg-blue-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getAgentIcon = (agentId) => {
    if (agentId.includes('portfolio')) return '💼';
    if (agentId.includes('timing')) return '⏰';
    if (agentId.includes('compliance')) return '🛡️';
    if (agentId.includes('index') || agentId.includes('scraper')) return '📊';
    return '🤖';
  };

  const getDecisionTypeLabel = (type) => {
    switch (type) {
      case 'portfolio_approval': return 'Portfolio Allocation';
      case 'timing_approval': return 'Market Timing';
      case 'compliance_approval': return 'Compliance Report';
      case 'market_data_approval': return 'Market Data';
      default: return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const decisionTime = new Date(timestamp);
    const diffSeconds = Math.floor((now - decisionTime) / 1000);
    
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
    return `${Math.floor(diffSeconds / 86400)}d ago`;
  };

  return (
    <WidgetPanel title="HITL Decision History" status="active">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-300 flex items-center">
            <History className="w-4 h-4 mr-2 text-blue-400" />
            Recent Decisions
          </h4>
          <span className="text-xs text-gray-400">
            {decisionHistory.length} decisions
          </span>
        </div>
        
        {decisionHistory.length > 0 ? (
          <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
            {decisionHistory.map((decision) => (
              <div 
                key={decision.decision_id}
                className="p-3 rounded-lg border border-gray-600 bg-gray-800 hover:border-gray-500 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getAgentIcon(decision.agent_id)}</span>
                    <span className="text-white font-medium">{getDecisionTypeLabel(decision.decision_type)}</span>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded flex items-center space-x-1 ${getStatusColor(decision.status)}`}>
                    {getStatusIcon(decision.status)}
                    <span>{decision.status.charAt(0).toUpperCase() + decision.status.slice(1)}</span>
                  </span>
                </div>
                
                <p className="text-sm text-gray-300 mb-2">{decision.description}</p>
                
                {decision.user_comments && (
                  <div className="bg-gray-700 rounded p-2 mb-2">
                    <p className="text-xs text-gray-300 italic">"{decision.user_comments}"</p>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{decision.agent_id}</span>
                  <span className="text-gray-400 flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {formatTimeAgo(decision.timestamp || decision.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6">
            <History className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No decision history available</p>
          </div>
        )}
        
        {/* Summary Stats */}
        {decisionHistory.length > 0 && (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex justify-between">
                <span className="text-gray-400">Approved</span>
                <span className="text-green-400 font-medium">
                  {decisionHistory.filter(d => d.status === 'approved').length}
                </span>
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex justify-between">
                <span className="text-gray-400">Rejected</span>
                <span className="text-red-400 font-medium">
                  {decisionHistory.filter(d => d.status === 'rejected').length}
                </span>
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex justify-between">
                <span className="text-gray-400">Bypassed</span>
                <span className="text-blue-400 font-medium">
                  {decisionHistory.filter(d => d.status === 'bypassed').length}
                </span>
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex justify-between">
                <span className="text-gray-400">Timed Out</span>
                <span className="text-yellow-400 font-medium">
                  {decisionHistory.filter(d => d.status === 'timeout').length}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </WidgetPanel>
  );
};
import React, { useState, useEffect } from 'react';
import { WidgetPanel, ToggleSwitch } from './AGUIComponents';
import { AlertCircle, CheckCircle, XCircle, Clock, User, Bot, MessageSquare } from 'lucide-react';

export const HITLDecisionPanel = ({ 
  pendingDecisions = [], 
  onApprove, 
  onReject,
  autonomousMode,
  onToggleAutonomousMode
}) => {
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [comment, setComment] = useState('');
  
  // Auto-select first decision when list changes
  useEffect(() => {
    if (pendingDecisions.length > 0 && !selectedDecision) {
      setSelectedDecision(pendingDecisions[0]);
    } else if (pendingDecisions.length === 0) {
      setSelectedDecision(null);
    }
  }, [pendingDecisions]);

  const handleApprove = () => {
    if (selectedDecision) {
      onApprove(selectedDecision.decision_id, comment);
      setComment('');
    }
  };

  const handleReject = () => {
    if (selectedDecision) {
      onReject(selectedDecision.decision_id, comment);
      setComment('');
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
    <WidgetPanel 
      title="Human-in-the-Loop Decisions" 
      status={autonomousMode ? "inactive" : "active"}
    >
      <div className="space-y-4">
        {/* Autonomous Mode Toggle */}
        <div className="flex items-center justify-between p-3 bg-gray-800 border border-gray-600 rounded-lg">
          <div className="flex items-center space-x-3">
            {autonomousMode ? (
              <Bot className="w-5 h-5 text-blue-400" />
            ) : (
              <User className="w-5 h-5 text-yellow-400" />
            )}
            <div>
              <span className="text-white font-medium">Execution Mode</span>
              <p className="text-xs text-gray-400">Toggle between autonomous and HITL mode</p>
            </div>
          </div>
          <ToggleSwitch
            enabled={autonomousMode}
            onChange={onToggleAutonomousMode}
            label={autonomousMode ? "Autonomous" : "HITL"}
          />
        </div>

        {/* Mode Description */}
        <div className={`p-3 rounded-lg border ${
          autonomousMode 
            ? 'bg-blue-900/20 border-blue-600 text-blue-400' 
            : 'bg-yellow-900/20 border-yellow-600 text-yellow-400'
        }`}>
          <p className="text-sm">
            {autonomousMode 
              ? 'Autonomous Mode: Agents will make decisions without human approval' 
              : 'HITL Mode: Critical decisions require human approval'}
          </p>
        </div>

        {/* Pending Decisions List */}
        {pendingDecisions.length > 0 ? (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-300 flex items-center">
              <AlertCircle className="w-4 h-4 mr-2 text-yellow-400" />
              Pending Decisions ({pendingDecisions.length})
            </h4>
            
            <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
              {pendingDecisions.map((decision) => (
                <div 
                  key={decision.decision_id}
                  className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                    selectedDecision?.decision_id === decision.decision_id
                      ? 'bg-gray-700 border-blue-500'
                      : 'bg-gray-800 border-gray-600 hover:border-gray-500'
                  }`}
                  onClick={() => setSelectedDecision(decision)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getAgentIcon(decision.agent_id)}</span>
                      <span className="text-white font-medium">{getDecisionTypeLabel(decision.decision_type)}</span>
                    </div>
                    <span className="text-xs text-gray-400 flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatTimeAgo(decision.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{decision.description}</p>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">{decision.agent_id}</span>
                    <span className="bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">
                      Pending
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Selected Decision Details */}
            {selectedDecision && (
              <div className="border border-gray-600 rounded-lg p-4 bg-gray-800">
                <h5 className="text-white font-medium mb-3">Decision Details</h5>
                
                <div className="space-y-3 mb-4">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-400">Agent:</span>
                      <p className="text-white">{selectedDecision.agent_id}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Type:</span>
                      <p className="text-white">{getDecisionTypeLabel(selectedDecision.decision_type)}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Created:</span>
                      <p className="text-white">{new Date(selectedDecision.created_at).toLocaleTimeString()}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Timeout:</span>
                      <p className="text-white">{selectedDecision.timeout_seconds}s</p>
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-gray-400 text-sm">Description:</span>
                    <p className="text-white text-sm mt-1">{selectedDecision.description}</p>
                  </div>
                </div>
                
                {/* Comment Input */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
                    <MessageSquare className="w-4 h-4 mr-2 text-blue-400" />
                    Add Comment (Optional)
                  </label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    placeholder="Add your feedback or reasoning..."
                    rows={2}
                  />
                </div>
                
                {/* Action Buttons */}
                <div className="flex space-x-3">
                  <button
                    onClick={handleApprove}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={handleReject}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <User className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">No Pending Decisions</h3>
            <p className="text-gray-400 mb-4">
              {autonomousMode 
                ? "Autonomous mode is enabled. Agents will make decisions without human approval."
                : "When agents require human input, decisions will appear here for your approval."
              }
            </p>
          </div>
        )}
      </div>
    </WidgetPanel>
  );
};
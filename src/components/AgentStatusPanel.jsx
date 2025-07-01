import React from 'react';
import { WidgetPanel, ToggleSwitch } from './AGUIComponents';
import { Bot, Cpu, Shield, TrendingUp, User } from 'lucide-react';

export const AgentStatusPanel = ({ agents, onToggleAgent, onToggleHITL, a2aEnabled }) => {
  const getAgentIcon = (agentType) => {
    switch (agentType) {
      case 'Data Collection': return <Bot className="w-5 h-5 text-blue-400" />;
      case 'Strategy & Optimization': return <Cpu className="w-5 h-5 text-green-400" />;
      case 'Market Intelligence': return <TrendingUp className="w-5 h-5 text-purple-400" />;
      case 'Risk & Compliance': return <Shield className="w-5 h-5 text-red-400" />;
      default: return <Bot className="w-5 h-5 text-gray-400" />;
    }
  };

  const activeAgents = agents.filter(agent => agent.isActive).length;
  const connectedMCPs = agents.filter(agent => agent.mcpConnected).length;
  const avgPerformance = agents.reduce((acc, agent) => acc + agent.performance, 0) / agents.length;
  const hitlEnabledAgents = agents.filter(agent => agent.hitlEnabled).length;

  return (
    <div className="space-y-6">
      <WidgetPanel title="LangGraph Agents" status="active">
        <div className="space-y-4">
          {agents.map((agent) => (
            <div key={agent.id} className={`bg-gray-800 border border-gray-600 rounded-lg p-4 transition-all duration-200 hover:border-gray-500 hover:shadow-lg ${
              agent.isActive ? 'ring-2 ring-blue-400' : ''
            }`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {getAgentIcon(agent.type)}
                  <div>
                    <h4 className="text-white font-semibold text-sm">{agent.name}</h4>
                    <p className="text-gray-400 text-xs">{agent.type}</p>
                  </div>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  agent.status === 'connected' ? 'bg-green-400' : 
                  agent.status === 'processing' ? 'bg-blue-400 animate-pulse' : 'bg-red-400'
                }`} />
              </div>
              
              {agent.description && (
                <p className="text-gray-400 text-xs mb-3">{agent.description}</p>
              )}
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">MCP Server</span>
                  <span className={`${agent.mcpConnected ? 'text-green-400' : 'text-red-400'}`}>
                    {agent.mcpConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">A2A Mode</span>
                  <span className={`${a2aEnabled ? 'text-blue-400' : 'text-gray-400'}`}>
                    {a2aEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                
                {agent.performance !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">Performance</span>
                    <span className={`flex items-center ${agent.performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {agent.performance >= 0 ? '+' : ''}{agent.performance.toFixed(1)}%
                    </span>
                  </div>
                )}
                
                {/* HITL Override Toggle */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400 flex items-center">
                    <User className="w-3 h-3 mr-1" />
                    HITL Override
                  </span>
                  <ToggleSwitch
                    enabled={agent.hitlEnabled}
                    onChange={(enabled) => onToggleHITL(agent.id, enabled)}
                    size="sm"
                  />
                </div>
                
                <button
                  onClick={() => onToggleAgent(agent.id)}
                  className={`w-full py-2 px-3 rounded text-xs font-medium transition-colors ${
                    agent.isActive 
                      ? 'bg-blue-600 text-white hover:bg-blue-700' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {agent.isActive ? 'Active' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </WidgetPanel>

      <WidgetPanel title="System Overview" status="active">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">Active Agents</span>
                <span className="text-green-400 font-bold text-lg">{activeAgents}/{agents.length}</span>
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
              <div className="flex items-center justify-between">
                <span className="text-gray-300 text-sm">MCP Connected</span>
                <span className="text-blue-400 font-bold text-lg">{connectedMCPs}/{agents.length}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-300 text-sm">Avg Performance</span>
              <span className="text-green-400 font-bold">{avgPerformance.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${avgPerformance}%` }}
              />
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">System Status</span>
              <span className="text-green-400 font-medium">Operational</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">A2A Communication</span>
              <span className={`font-medium ${a2aEnabled ? 'text-green-400' : 'text-gray-400'}`}>
                {a2aEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">HITL Overrides</span>
              <span className="text-yellow-400 font-medium">
                {hitlEnabledAgents}/{agents.length} Agents
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Last Update</span>
              <span className="text-blue-400 font-medium">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </WidgetPanel>
    </div>
  );
};
import React from 'react';
import { WidgetPanel, AgentCard } from './AGUIComponents';

export const AgentCards = ({ agents, a2aMode, onAgentChange }) => {
  return (
    <WidgetPanel title="LangGraph Agents" status="active">
      <div className="space-y-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            name={agent.name}
            description={agent.description}
            mcpConnected={agent.mcpConnected}
            hitlOverride={agent.hitlOverride}
            a2aMode={a2aMode}
            onHitlToggle={(enabled) => onAgentChange(agent.id, 'hitlOverride', enabled)}
          />
        ))}
        
        {/* A2A Status */}
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
          <div className="flex items-center justify-between">
            <span className="text-gray-300 text-sm">Agent-to-Agent Communication</span>
            <span className={`text-sm font-semibold ${a2aMode ? 'text-green-400' : 'text-gray-400'}`}>
              {a2aMode ? 'Active' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>
    </WidgetPanel>
  );
};
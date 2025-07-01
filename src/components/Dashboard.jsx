import React from 'react';
import { IndexTicker } from './IndexTicker';
import { PortfolioPanel } from './PortfolioPanel';
import { InputControls } from './InputControls';
import { AgentCards } from './AgentCards';
import { WidgetPanel, ToggleSwitch } from './AGUIComponents';
import { TrendingUp, Bot, Zap } from 'lucide-react';

export const Dashboard = ({ state, onChange }) => {
  const handleInputChange = (field, value) => {
    onChange({ [field]: value });
  };

  const handleAgentChange = (agentId, field, value) => {
    const updatedAgents = state.agents.map(agent =>
      agent.id === agentId ? { ...agent, [field]: value } : agent
    );
    onChange({ agents: updatedAgents });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">Agentic Stock Advisor</h1>
          </div>
          
          <div className="flex items-center space-x-6">
            {/* Execution Mode Toggle */}
            <div className="flex items-center space-x-3">
              <Bot className="w-5 h-5 text-blue-400" />
              <ToggleSwitch
                enabled={state.executionMode === 'Autonomous'}
                onChange={(enabled) => handleInputChange('executionMode', enabled ? 'Autonomous' : 'HITL')}
                label={state.executionMode}
              />
            </div>
            
            {/* A2A Mode Toggle */}
            <div className="flex items-center space-x-3">
              <Zap className="w-5 h-5 text-yellow-400" />
              <ToggleSwitch
                enabled={state.a2aMode}
                onChange={(enabled) => handleInputChange('a2aMode', enabled)}
                label="A2A Mode"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Index Ticker */}
      <IndexTicker data={state.indexData} />

      {/* Main Dashboard */}
      <main className="px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Controls */}
          <div className="space-y-6">
            <InputControls
              budget={state.budget}
              timeframe={state.timeframe}
              riskLevel={state.riskLevel}
              onChange={handleInputChange}
            />
            
            <AgentCards
              agents={state.agents}
              a2aMode={state.a2aMode}
              onAgentChange={handleAgentChange}
            />
          </div>

          {/* Middle Column - Portfolio */}
          <div className="lg:col-span-2">
            <PortfolioPanel
              portfolio={state.portfolio}
              budget={state.budget}
              executionMode={state.executionMode}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
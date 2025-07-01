import React, { useState, useEffect } from 'react';
import { MarketTicker } from './MarketTicker';
import { PortfolioRecommendations } from './PortfolioRecommendations';
import { 
  WidgetPanel, 
  AgentCard, 
  ToggleSwitch, 
  Dropdown, 
  A2AToggle 
} from './AGUIComponents';
import { Bot, Settings, DollarSign, BarChart3, Activity, TrendingUp } from 'lucide-react';

export const Dashboard = () => {
  // State management
  const [autonomousMode, setAutonomousMode] = useState(true);
  const [timeframe, setTimeframe] = useState('Medium');
  const [riskAppetite, setRiskAppetite] = useState('Medium');
  const [budget, setBudget] = useState('50000');
  
  // Agent states
  const [agents, setAgents] = useState([
    { 
      id: 'index-scraper',
      name: 'Index Scraper', 
      type: 'Data Collection',
      status: 'connected',
      mcpStatus: true,
      isActive: true,
      performance: 12.5
    },
    { 
      id: 'portfolio-optimizer',
      name: 'Portfolio Optimizer', 
      type: 'Strategy',
      status: 'processing',
      mcpStatus: true,
      isActive: true,
      performance: 8.3
    },
    { 
      id: 'timing-advisor',
      name: 'Timing Advisor', 
      type: 'Market Intelligence',
      status: 'connected',
      mcpStatus: true,
      isActive: false,
      performance: 15.7
    },
    { 
      id: 'compliance-checker',
      name: 'Compliance Checker', 
      type: 'Risk Management',
      status: 'connected',
      mcpStatus: false,
      isActive: false,
      performance: -2.1
    }
  ]);

  // A2A communication states
  const [a2aConnections, setA2AConnections] = useState([
    { from: 'Index Scraper', to: 'Portfolio Optimizer', enabled: true },
    { from: 'Portfolio Optimizer', to: 'Timing Advisor', enabled: false },
    { from: 'Timing Advisor', to: 'Compliance Checker', enabled: true },
    { from: 'Compliance Checker', to: 'Portfolio Optimizer', enabled: false }
  ]);

  // Real-time updates simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({
        ...agent,
        performance: agent.performance + (Math.random() - 0.5) * 2,
        status: agent.isActive ? 
          (Math.random() > 0.1 ? 'connected' : 'processing') : 
          'disconnected'
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const toggleAgent = (agentId) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { ...agent, isActive: !agent.isActive }
        : agent
    ));
  };

  const toggleA2AConnection = (index) => {
    setA2AConnections(prev => prev.map((conn, i) => 
      i === index ? { ...conn, enabled: !conn.enabled } : conn
    ));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Stock Advisor Dashboard</h1>
              <div className="flex items-center space-x-2 ml-4">
                <Activity className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Live</span>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <ToggleSwitch
                enabled={autonomousMode}
                onChange={setAutonomousMode}
                label={`${autonomousMode ? 'Autonomous' : 'HITL'} Mode`}
              />
              <Settings className="w-6 h-6 text-gray-400 hover:text-white cursor-pointer transition-colors" />
            </div>
          </div>
        </div>
      </header>

      {/* Market Ticker */}
      <MarketTicker />

      {/* Main Dashboard */}
      <main className="px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Controls & Settings */}
          <div className="space-y-6">
            <WidgetPanel title="Trading Configuration" status="active">
              <div className="space-y-4">
                <Dropdown
                  label="Investment Timeframe"
                  options={['Short', 'Medium', 'Long']}
                  value={timeframe}
                  onChange={setTimeframe}
                />
                <Dropdown
                  label="Risk Appetite"
                  options={['Low', 'Medium', 'High']}
                  value={riskAppetite}
                  onChange={setRiskAppetite}
                />
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Investment Budget ($)
                  </label>
                  <input
                    type="number"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    placeholder="Enter budget"
                  />
                </div>
                <div className="pt-2">
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                    Update Configuration
                  </button>
                </div>
              </div>
            </WidgetPanel>

            <WidgetPanel title="Agent Communication Network" status="active">
              <div className="space-y-3">
                {a2aConnections.map((connection, index) => (
                  <A2AToggle
                    key={index}
                    fromAgent={connection.from}
                    toAgent={connection.to}
                    enabled={connection.enabled}
                    onChange={() => toggleA2AConnection(index)}
                  />
                ))}
              </div>
              <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Active Connections</span>
                  <span className="text-blue-400 font-semibold">
                    {a2aConnections.filter(conn => conn.enabled).length}/{a2aConnections.length}
                  </span>
                </div>
              </div>
            </WidgetPanel>
          </div>

          {/* Middle Column - Portfolio Recommendations */}
          <div>
            <WidgetPanel title="AI Portfolio Recommendations" status="active">
              <PortfolioRecommendations />
            </WidgetPanel>
          </div>

          {/* Right Column - Agents & System Status */}
          <div className="space-y-6">
            <WidgetPanel title="LangGraph Agents" status="active">
              <div className="grid grid-cols-1 gap-4">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    name={agent.name}
                    type={agent.type}
                    status={agent.status}
                    mcpStatus={agent.mcpStatus}
                    onToggle={() => toggleAgent(agent.id)}
                    isActive={agent.isActive}
                    performance={agent.performance}
                  />
                ))}
              </div>
            </WidgetPanel>

            <WidgetPanel title="System Performance" status="active">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Active Agents</span>
                  <span className="text-green-400 font-semibold">
                    {agents.filter(a => a.isActive).length}/{agents.length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">MCP Connections</span>
                  <span className="text-blue-400 font-semibold">
                    {agents.filter(a => a.mcpStatus).length}/{agents.length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Avg Performance</span>
                  <span className={`font-semibold flex items-center ${
                    (agents.reduce((acc, a) => acc + a.performance, 0) / agents.length) >= 0 
                      ? 'text-green-400' : 'text-red-400'
                  }`}>
                    <TrendingUp className="w-4 h-4 mr-1" />
                    {(agents.reduce((acc, a) => acc + a.performance, 0) / agents.length).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Portfolio Value</span>
                  <span className="text-green-400 font-semibold flex items-center">
                    <DollarSign className="w-4 h-4 mr-1" />
                    {Number(budget).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">System Status</span>
                  <span className="text-green-400 font-semibold">Operational</span>
                </div>
              </div>
            </WidgetPanel>
          </div>
        </div>
      </main>
    </div>
  );
};
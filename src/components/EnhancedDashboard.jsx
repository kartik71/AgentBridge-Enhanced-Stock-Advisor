import React, { useState, useEffect } from 'react';
import { MarketTicker } from './MarketTicker';
import { PortfolioRecommendations } from './PortfolioRecommendations';
import { UserInputPanel } from './UserInputPanel';
import { AgentStatusPanel } from './AgentStatusPanel';
import { A2ACommunicationPanel } from './A2ACommunicationPanel';
import { HITLDecisionPanel } from './HITLDecisionPanel';
import { HITLHistoryPanel } from './HITLHistoryPanel';
import { WidgetPanel, ToggleSwitch } from './AGUIComponents';
import { Bot, Network, Zap, TrendingUp, Activity, User } from 'lucide-react';

export const EnhancedDashboard = () => {
  // Core state
  const [userConfig, setUserConfig] = useState({
    budget: 50000,
    timeframe: 'Medium',
    riskLevel: 'Medium',
    goals: 'Growth'
  });

  // A2A Communication state
  const [a2aEnabled, setA2AEnabled] = useState(true);
  const [autonomousMode, setAutonomousMode] = useState(true);
  
  // Agent states
  const [agents, setAgents] = useState([
    {
      id: 'index-scraper',
      name: 'Index Scraper',
      type: 'Data Collection',
      status: 'connected',
      mcpConnected: true,
      isActive: true,
      performance: 12.5,
      lastUpdate: new Date().toISOString(),
      description: 'Collects real-time market data and indices',
      hitlEnabled: false
    },
    {
      id: 'portfolio-optimizer',
      name: 'Portfolio Optimizer',
      type: 'Strategy & Optimization',
      status: 'processing',
      mcpConnected: true,
      isActive: true,
      performance: 8.3,
      lastUpdate: new Date().toISOString(),
      description: 'Optimizes portfolio allocation using MPT',
      hitlEnabled: true
    },
    {
      id: 'timing-advisor',
      name: 'Timing Advisor',
      type: 'Market Intelligence',
      status: 'connected',
      mcpConnected: true,
      isActive: true,
      performance: 15.7,
      lastUpdate: new Date().toISOString(),
      description: 'Provides market timing analysis',
      hitlEnabled: false
    },
    {
      id: 'compliance-logger',
      name: 'Compliance Logger',
      type: 'Risk & Compliance',
      status: 'connected',
      mcpConnected: false,
      isActive: false,
      performance: -2.1,
      lastUpdate: new Date().toISOString(),
      description: 'Monitors regulatory compliance',
      hitlEnabled: false
    }
  ]);

  // A2A Connections
  const [a2aConnections, setA2AConnections] = useState([
    {
      from: 'Index Scraper',
      to: 'Portfolio Optimizer',
      enabled: true,
      description: 'Real-time market data and price feeds'
    },
    {
      from: 'Portfolio Optimizer',
      to: 'Timing Advisor',
      enabled: true,
      description: 'Portfolio allocation for timing analysis'
    },
    {
      from: 'Timing Advisor',
      to: 'Compliance Logger',
      enabled: false,
      description: 'Timing recommendations for compliance review'
    },
    {
      from: 'Compliance Logger',
      to: 'Portfolio Optimizer',
      enabled: false,
      description: 'Compliance feedback and risk alerts'
    }
  ]);

  // HITL state
  const [pendingDecisions, setPendingDecisions] = useState([
    {
      decision_id: 'decision-001',
      agent_id: 'portfolio-optimizer',
      decision_type: 'portfolio_approval',
      description: 'Portfolio allocation for $75,000 with Medium risk and Medium timeframe. Contains 5 positions with expected return of 12.3%.',
      created_at: new Date(Date.now() - 120000).toISOString(),
      status: 'pending',
      timeout_seconds: 300
    },
    {
      decision_id: 'decision-002',
      agent_id: 'timing-advisor',
      decision_type: 'timing_approval',
      description: 'Market timing analysis for Medium timeframe. Market regime: Neutral market in normal volatility environment. Overall timing: BUY_SIGNAL with 78% confidence.',
      created_at: new Date(Date.now() - 60000).toISOString(),
      status: 'pending',
      timeout_seconds: 300
    }
  ]);

  const [decisionHistory, setDecisionHistory] = useState([
    {
      decision_id: 'history-001',
      agent_id: 'portfolio-optimizer',
      decision_type: 'portfolio_approval',
      description: 'Portfolio allocation for $50,000 with Low risk and Long timeframe.',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      resolved_at: new Date(Date.now() - 3540000).toISOString(),
      status: 'approved',
      user_comments: 'Good diversification across sectors'
    },
    {
      decision_id: 'history-002',
      agent_id: 'compliance-logger',
      decision_type: 'compliance_approval',
      description: 'Compliance report with score 75.5/100. Contains 2 violations.',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      resolved_at: new Date(Date.now() - 7140000).toISOString(),
      status: 'rejected',
      user_comments: 'Too many position limit violations'
    },
    {
      decision_id: 'history-003',
      agent_id: 'timing-advisor',
      decision_type: 'timing_approval',
      description: 'Market timing analysis for Short timeframe.',
      created_at: new Date(Date.now() - 10800000).toISOString(),
      resolved_at: new Date(Date.now() - 10800000).toISOString(),
      status: 'bypassed',
      resolution_reason: 'Autonomous mode enabled'
    }
  ]);

  // Portfolio recommendations state
  const [recommendations, setRecommendations] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Create agent status map for A2A panel
  const agentStatuses = agents.reduce((acc, agent) => {
    acc[agent.name] = agent.status;
    return acc;
  }, {});

  // Simulate real-time agent updates
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({
        ...agent,
        performance: agent.performance + (Math.random() - 0.5) * 2,
        status: agent.isActive ? 
          (Math.random() > 0.1 ? 'connected' : 'processing') : 
          'disconnected',
        lastUpdate: new Date().toISOString()
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Auto-generate recommendations in autonomous mode
  useEffect(() => {
    if (autonomousMode && a2aEnabled) {
      const interval = setInterval(() => {
        generateRecommendations();
      }, 30000); // Every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autonomousMode, a2aEnabled, userConfig]);

  const handleUserConfigChange = (updates) => {
    setUserConfig(prev => ({ ...prev, ...updates }));
  };

  const toggleAgent = (agentId) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { ...agent, isActive: !agent.isActive }
        : agent
    ));
  };

  const toggleAgentHITL = (agentId, enabled) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { ...agent, hitlEnabled: enabled }
        : agent
    ));
  };

  const toggleA2AConnection = (index) => {
    setA2AConnections(prev => prev.map((conn, i) => 
      i === index ? { ...conn, enabled: !conn.enabled } : conn
    ));
  };

  const handleApproveDecision = (decisionId, comment) => {
    // Find the decision
    const decision = pendingDecisions.find(d => d.decision_id === decisionId);
    if (!decision) return;
    
    // Update decision history
    const updatedDecision = {
      ...decision,
      status: 'approved',
      resolved_at: new Date().toISOString(),
      user_comments: comment || undefined
    };
    
    setDecisionHistory(prev => [updatedDecision, ...prev]);
    
    // Remove from pending decisions
    setPendingDecisions(prev => prev.filter(d => d.decision_id !== decisionId));
  };

  const handleRejectDecision = (decisionId, comment) => {
    // Find the decision
    const decision = pendingDecisions.find(d => d.decision_id === decisionId);
    if (!decision) return;
    
    // Update decision history
    const updatedDecision = {
      ...decision,
      status: 'rejected',
      resolved_at: new Date().toISOString(),
      user_comments: comment || undefined
    };
    
    setDecisionHistory(prev => [updatedDecision, ...prev]);
    
    // Remove from pending decisions
    setPendingDecisions(prev => prev.filter(d => d.decision_id !== decisionId));
  };

  const handleToggleAutonomousMode = (enabled) => {
    setAutonomousMode(enabled);
    
    // If enabling autonomous mode, move all pending decisions to history as bypassed
    if (enabled && pendingDecisions.length > 0) {
      const bypassedDecisions = pendingDecisions.map(decision => ({
        ...decision,
        status: 'bypassed',
        resolved_at: new Date().toISOString(),
        resolution_reason: 'Autonomous mode enabled'
      }));
      
      setDecisionHistory(prev => [...bypassedDecisions, ...prev]);
      setPendingDecisions([]);
    }
  };

  const generateRecommendations = async () => {
    setIsGenerating(true);
    
    try {
      // Simulate A2A-enhanced portfolio optimization
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate enhanced recommendations
      const enhancedRecs = [
        {
          symbol: 'AAPL',
          action: 'BUY',
          currentPrice: 192.35,
          targetPrice: 210.00,
          confidence: a2aEnabled ? 89 : 82, // Higher confidence with A2A
          reason: a2aEnabled 
            ? 'Strong fundamentals + positive timing signals from A2A analysis'
            : 'Strong fundamentals and market position',
          risk: 'Low',
          sector: 'Technology',
          allocation: 25,
          a2aEnhanced: a2aEnabled
        },
        {
          symbol: 'MSFT',
          action: 'BUY',
          currentPrice: 398.75,
          targetPrice: 425.00,
          confidence: a2aEnabled ? 86 : 79,
          reason: a2aEnabled
            ? 'Cloud growth + A2A market timing indicates optimal entry'
            : 'Strong cloud growth and enterprise demand',
          risk: 'Low',
          sector: 'Technology',
          allocation: 22,
          a2aEnhanced: a2aEnabled
        },
        {
          symbol: 'GOOGL',
          action: 'HOLD',
          currentPrice: 142.50,
          targetPrice: 155.00,
          confidence: a2aEnabled ? 78 : 72,
          reason: a2aEnabled
            ? 'Mixed signals from A2A timing analysis, maintain position'
            : 'Solid fundamentals but regulatory concerns',
          risk: 'Medium',
          sector: 'Technology',
          allocation: 18,
          a2aEnhanced: a2aEnabled
        },
        {
          symbol: 'JNJ',
          action: 'BUY',
          currentPrice: 165.20,
          targetPrice: 175.00,
          confidence: a2aEnabled ? 84 : 77,
          reason: a2aEnabled
            ? 'Defensive play + A2A compliance signals all clear'
            : 'Defensive healthcare play with strong dividend',
          risk: 'Low',
          sector: 'Healthcare',
          allocation: 20,
          a2aEnhanced: a2aEnabled
        },
        {
          symbol: 'NVDA',
          action: 'BUY',
          currentPrice: 465.20,
          targetPrice: 520.00,
          confidence: a2aEnabled ? 91 : 85,
          reason: a2aEnabled
            ? 'AI momentum + A2A timing shows strong buy signals'
            : 'AI chip leadership and data center demand',
          risk: 'High',
          sector: 'Technology',
          allocation: 15,
          a2aEnhanced: a2aEnabled
        }
      ];
      
      setRecommendations(enhancedRecs);
      
      // If not in autonomous mode, create a new pending decision
      if (!autonomousMode) {
        const newDecision = {
          decision_id: `decision-${Date.now()}`,
          agent_id: 'portfolio-optimizer',
          decision_type: 'portfolio_approval',
          description: `Portfolio allocation for $${userConfig.budget.toLocaleString()} with ${userConfig.riskLevel} risk and ${userConfig.timeframe} timeframe. Contains ${enhancedRecs.length} positions with expected return of 12.8%.`,
          created_at: new Date().toISOString(),
          status: 'pending',
          timeout_seconds: 300,
          decision_data: {
            recommendations: enhancedRecs,
            userConfig
          }
        };
        
        setPendingDecisions(prev => [...prev, newDecision]);
      }
      
    } catch (error) {
      console.error('Error generating recommendations:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Enhanced Stock Advisor</h1>
              <div className="flex items-center space-x-2 ml-4">
                <Activity className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">A2A Enabled</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              {/* A2A Toggle */}
              <div className="flex items-center space-x-3">
                <Network className="w-5 h-5 text-blue-400" />
                <ToggleSwitch
                  enabled={a2aEnabled}
                  onChange={setA2AEnabled}
                  label="A2A Mode"
                />
              </div>
              
              {/* Autonomous Mode Toggle */}
              <div className="flex items-center space-x-3">
                {autonomousMode ? (
                  <Bot className="w-5 h-5 text-green-400" />
                ) : (
                  <User className="w-5 h-5 text-yellow-400" />
                )}
                <ToggleSwitch
                  enabled={autonomousMode}
                  onChange={handleToggleAutonomousMode}
                  label={autonomousMode ? 'Autonomous' : 'HITL'}
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Market Ticker */}
      <MarketTicker />

      {/* Main Dashboard */}
      <main className="px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column - User Input & HITL */}
          <div className="lg:col-span-3 space-y-6">
            <UserInputPanel
              config={userConfig}
              onChange={handleUserConfigChange}
              onGenerateRecommendations={generateRecommendations}
              autonomousMode={autonomousMode}
              isGenerating={isGenerating}
            />
            
            <HITLDecisionPanel
              pendingDecisions={pendingDecisions}
              onApprove={handleApproveDecision}
              onReject={handleRejectDecision}
              autonomousMode={autonomousMode}
              onToggleAutonomousMode={handleToggleAutonomousMode}
            />
          </div>

          {/* Middle Column - Portfolio Recommendations */}
          <div className="lg:col-span-5">
            <WidgetPanel title="AI Portfolio Recommendations" status="active">
              <PortfolioRecommendations
                recommendations={recommendations}
                isGenerating={isGenerating}
                userConfig={userConfig}
                autonomousMode={autonomousMode}
              />
            </WidgetPanel>
          </div>

          {/* Right Column - Agents, A2A & History */}
          <div className="lg:col-span-4 space-y-6">
            {/* A2A Communication Panel */}
            <A2ACommunicationPanel
              connections={a2aConnections}
              onToggleConnection={toggleA2AConnection}
              enabled={a2aEnabled}
              onToggleA2A={setA2AEnabled}
              agentStatuses={agentStatuses}
            />

            {/* Agent Status Panel */}
            <AgentStatusPanel
              agents={agents}
              onToggleAgent={toggleAgent}
              onToggleHITL={toggleAgentHITL}
              a2aEnabled={a2aEnabled}
            />
            
            {/* HITL History Panel */}
            <HITLHistoryPanel
              decisionHistory={decisionHistory}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
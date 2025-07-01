import React, { useState } from 'react';
import { WidgetPanel, ToggleSwitch, Dropdown } from './AGUIComponents';
import { Settings as SettingsIcon, Save, RefreshCw, AlertTriangle, Shield, Database, Bell } from 'lucide-react';

export const Settings = () => {
  // System Settings
  const [systemSettings, setSystemSettings] = useState({
    autoRebalancing: true,
    riskMonitoring: true,
    complianceChecking: true,
    realTimeUpdates: true,
    emailNotifications: false,
    smsAlerts: false,
    paperTrading: true
  });

  // Agent Configuration
  const [agentConfig, setAgentConfig] = useState({
    indexScraperInterval: '30',
    optimizerFrequency: 'hourly',
    timingAnalysisDepth: 'medium',
    complianceStrictness: 'high'
  });

  // Risk Management
  const [riskSettings, setRiskSettings] = useState({
    maxPositionSize: '10',
    maxDailyLoss: '5',
    stopLossThreshold: '3',
    portfolioVaR: '2'
  });

  // Data Sources
  const [dataSources, setDataSources] = useState({
    primaryProvider: 'alpha_vantage',
    backupProvider: 'yahoo_finance',
    newsProvider: 'reuters',
    sentimentProvider: 'twitter_api'
  });

  const handleSystemSettingChange = (key, value) => {
    setSystemSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleAgentConfigChange = (key, value) => {
    setAgentConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleRiskSettingChange = (key, value) => {
    setRiskSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleDataSourceChange = (key, value) => {
    setDataSources(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveSettings = () => {
    console.log('Saving settings...', {
      systemSettings,
      agentConfig,
      riskSettings,
      dataSources
    });
    alert('Settings saved successfully!');
  };

  const handleResetSettings = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      setSystemSettings({
        autoRebalancing: true,
        riskMonitoring: true,
        complianceChecking: true,
        realTimeUpdates: true,
        emailNotifications: false,
        smsAlerts: false,
        paperTrading: true
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <SettingsIcon className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">System Settings</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleResetSettings}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reset</span>
              </button>
              <button
                onClick={handleSaveSettings}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Content */}
      <main className="px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* System Configuration */}
          <div className="space-y-6">
            <WidgetPanel title="System Configuration" status="active">
              <div className="space-y-4">
                <ToggleSwitch
                  enabled={systemSettings.autoRebalancing}
                  onChange={(value) => handleSystemSettingChange('autoRebalancing', value)}
                  label="Auto Portfolio Rebalancing"
                />
                <ToggleSwitch
                  enabled={systemSettings.riskMonitoring}
                  onChange={(value) => handleSystemSettingChange('riskMonitoring', value)}
                  label="Real-time Risk Monitoring"
                />
                <ToggleSwitch
                  enabled={systemSettings.complianceChecking}
                  onChange={(value) => handleSystemSettingChange('complianceChecking', value)}
                  label="Compliance Checking"
                />
                <ToggleSwitch
                  enabled={systemSettings.realTimeUpdates}
                  onChange={(value) => handleSystemSettingChange('realTimeUpdates', value)}
                  label="Real-time Market Updates"
                />
                <ToggleSwitch
                  enabled={systemSettings.paperTrading}
                  onChange={(value) => handleSystemSettingChange('paperTrading', value)}
                  label="Paper Trading Mode"
                />
              </div>
            </WidgetPanel>

            <WidgetPanel title="Notifications" status="active">
              <div className="space-y-4">
                <ToggleSwitch
                  enabled={systemSettings.emailNotifications}
                  onChange={(value) => handleSystemSettingChange('emailNotifications', value)}
                  label="Email Notifications"
                />
                <ToggleSwitch
                  enabled={systemSettings.smsAlerts}
                  onChange={(value) => handleSystemSettingChange('smsAlerts', value)}
                  label="SMS Alerts"
                />
                <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-3 flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-blue-400" />
                  <span className="text-blue-400 text-sm">Configure notification preferences for trading alerts</span>
                </div>
              </div>
            </WidgetPanel>
          </div>

          {/* Agent & Risk Configuration */}
          <div className="space-y-6">
            <WidgetPanel title="Agent Configuration" status="active">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Index Scraper Interval (seconds)
                  </label>
                  <input
                    type="number"
                    value={agentConfig.indexScraperInterval}
                    onChange={(e) => handleAgentConfigChange('indexScraperInterval', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="10"
                    max="300"
                  />
                </div>
                <Dropdown
                  label="Portfolio Optimizer Frequency"
                  options={['every_minute', 'every_5_minutes', 'hourly', 'daily']}
                  value={agentConfig.optimizerFrequency}
                  onChange={(value) => handleAgentConfigChange('optimizerFrequency', value)}
                />
                <Dropdown
                  label="Timing Analysis Depth"
                  options={['basic', 'medium', 'advanced']}
                  value={agentConfig.timingAnalysisDepth}
                  onChange={(value) => handleAgentConfigChange('timingAnalysisDepth', value)}
                />
                <Dropdown
                  label="Compliance Strictness"
                  options={['low', 'medium', 'high', 'maximum']}
                  value={agentConfig.complianceStrictness}
                  onChange={(value) => handleAgentConfigChange('complianceStrictness', value)}
                />
              </div>
            </WidgetPanel>

            <WidgetPanel title="Risk Management" status="warning">
              <div className="flex items-center space-x-2 mb-4 p-3 bg-yellow-900/20 border border-yellow-600 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-400 text-sm">Changes to risk settings require admin approval</span>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Position Size (% of portfolio)
                  </label>
                  <input
                    type="number"
                    value={riskSettings.maxPositionSize}
                    onChange={(e) => handleRiskSettingChange('maxPositionSize', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Daily Loss (% of portfolio)
                  </label>
                  <input
                    type="number"
                    value={riskSettings.maxDailyLoss}
                    onChange={(e) => handleRiskSettingChange('maxDailyLoss', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="20"
                  />
                </div>
              </div>
            </WidgetPanel>
          </div>
        </div>
      </main>
    </div>
  );
};
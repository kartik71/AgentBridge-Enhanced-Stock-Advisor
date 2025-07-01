"""
ComplianceLoggerAgent - LangGraph ReAct Agent for Regulatory Compliance
Uses ReAct pattern with reasoning traces for compliance monitoring and audit logging
"""

import asyncio
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

try:
    from mcp_servers.trading_server import trading_server
except ImportError:
    print("Warning: MCP servers not available, using mock data")
    trading_server = None

# State definition for the agent
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    compliance_rules: Dict[str, Any]
    monitoring_scope: str
    portfolio_data: Dict[str, Any]
    trade_orders: List[Dict[str, Any]]
    compliance_violations: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approved: bool
    final_compliance_report: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

@dataclass
class ComplianceConfig:
    """Configuration for compliance monitoring"""
    monitoring_scope: str = "full"  # full, portfolio, trades
    compliance_strictness: str = "high"  # low, medium, high, maximum
    real_time_monitoring: bool = True
    hitl_enabled: bool = False
    audit_retention_days: int = 365

class ComplianceLoggerReActAgent:
    """LangGraph ReAct Agent for Regulatory Compliance with HITL support"""
    
    def __init__(self, agent_id: str = "compliance_logger_react"):
        self.agent_id = agent_id
        self.name = "ComplianceLoggerReActAgent"
        self.version = "1.0.0"
        self.audit_log_file = "data/compliance_logger_audit.json"
        self.csv_log_file = "data/compliance_logger_decisions.csv"
        self.violations_log_file = "data/compliance_violations.json"
        
        # Initialize MCP server
        self.trading_server = trading_server
        
        # Create the StateGraph
        self.graph = self._create_graph()
        
        # Ensure audit directories exist
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
        self._initialize_csv_log()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph StateGraph for ReAct pattern"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("load_compliance_rules", self._load_compliance_rules)
        workflow.add_node("collect_portfolio_data", self._collect_portfolio_data)
        workflow.add_node("analyze_trade_orders", self._analyze_trade_orders)
        workflow.add_node("check_position_limits", self._check_position_limits)
        workflow.add_node("assess_risk_compliance", self._assess_risk_compliance)
        workflow.add_node("detect_violations", self._detect_violations)
        workflow.add_node("reason_about_compliance", self._reason_about_compliance)
        workflow.add_node("hitl_review", self._hitl_review)
        workflow.add_node("finalize_compliance_report", self._finalize_compliance_report)
        workflow.add_node("log_compliance_check", self._log_compliance_check)
        
        # Define the flow
        workflow.set_entry_point("load_compliance_rules")
        
        workflow.add_edge("load_compliance_rules", "collect_portfolio_data")
        workflow.add_edge("collect_portfolio_data", "analyze_trade_orders")
        workflow.add_edge("analyze_trade_orders", "check_position_limits")
        workflow.add_edge("check_position_limits", "assess_risk_compliance")
        workflow.add_edge("assess_risk_compliance", "detect_violations")
        workflow.add_edge("detect_violations", "reason_about_compliance")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "reason_about_compliance",
            self._should_require_hitl_approval,
            {
                "hitl_required": "hitl_review",
                "no_hitl": "finalize_compliance_report"
            }
        )
        
        workflow.add_conditional_edges(
            "hitl_review",
            self._check_hitl_approval,
            {
                "approved": "finalize_compliance_report",
                "rejected": "detect_violations",  # Re-analyze violations
                "pending": END
            }
        )
        
        workflow.add_edge("finalize_compliance_report", "log_compliance_check")
        workflow.add_edge("log_compliance_check", END)
        
        return workflow.compile()
    
    async def _load_compliance_rules(self, state: AgentState) -> AgentState:
        """Load and validate compliance rules"""
        reasoning = f"🔍 ANALYZE: Loading compliance rules for {state['monitoring_scope']} monitoring"
        
        # Load comprehensive compliance rules
        compliance_rules = {
            "position_limits": {
                "max_single_position": 0.25,  # 25% of portfolio
                "max_sector_concentration": 0.40,  # 40% in single sector
                "max_daily_trading_volume": 1000000,  # $1M daily
                "max_leverage": 2.0  # 2:1 leverage
            },
            "risk_limits": {
                "max_portfolio_var": 0.05,  # 5% Value at Risk
                "max_drawdown": 0.15,  # 15% maximum drawdown
                "max_correlation": 0.8,  # Max correlation between positions
                "min_liquidity_ratio": 0.10  # 10% cash minimum
            },
            "regulatory_requirements": {
                "pattern_day_trader_rule": True,
                "wash_sale_rule": True,
                "insider_trading_monitoring": True,
                "market_manipulation_detection": True,
                "best_execution": True,
                "know_your_customer": True,
                "anti_money_laundering": True
            },
            "reporting_requirements": {
                "large_position_reporting": 100000,  # Report positions > $100k
                "suspicious_activity_threshold": 50000,  # Flag trades > $50k
                "audit_trail_retention": 365,  # Days to retain records
                "real_time_monitoring": True,
                "daily_compliance_report": True
            },
            "restricted_securities": [],  # No restrictions in demo mode
            "trading_hours": {
                "market_open": "09:30",
                "market_close": "16:00",
                "extended_hours_allowed": False,
                "timezone": "EST"
            },
            "paper_trading": {
                "enabled": True,
                "virtual_funds": True,
                "real_market_data": True,
                "compliance_simulation": True
            }
        }
        
        state['compliance_rules'] = compliance_rules
        
        reasoning += f" ✅ Loaded {len(compliance_rules)} rule categories"
        reasoning += f" 📊 Position limits: {compliance_rules['position_limits']['max_single_position']:.0%} max position"
        reasoning += f" 🛡️ Risk limits: {compliance_rules['risk_limits']['max_portfolio_var']:.0%} max VaR"
        reasoning += f" 📋 Regulatory rules: {len(compliance_rules['regulatory_requirements'])} requirements"
        reasoning += f" 🔄 Paper trading mode: {compliance_rules['paper_trading']['enabled']}"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _collect_portfolio_data(self, state: AgentState) -> AgentState:
        """Collect current portfolio data for compliance analysis"""
        reasoning = "📊 COLLECT: Gathering portfolio data for compliance analysis..."
        
        try:
            if self.trading_server:
                # Get portfolio positions
                portfolio_result = await self.trading_server.get_portfolio_positions("default_user")
                
                if portfolio_result['status'] == 'success':
                    state['portfolio_data'] = portfolio_result
                    positions = portfolio_result.get('positions', {})
                    summary = portfolio_result.get('summary', {})
                    
                    reasoning += f" ✅ Retrieved portfolio with {len(positions)} positions"
                    reasoning += f" 💰 Total value: ${summary.get('total_market_value', 0):,.2f}"
                    reasoning += f" 📈 Total P&L: ${summary.get('total_unrealized_pnl', 0):,.2f}"
                    
                    # Log major positions
                    for symbol, position in list(positions.items())[:3]:
                        reasoning += f" 📊 {symbol}: {position.get('shares', 0)} shares (${position.get('market_value', 0):,.2f})"
                else:
                    raise Exception("Failed to retrieve portfolio data")
                    
            else:
                # Generate mock portfolio data
                state['portfolio_data'] = self._generate_mock_portfolio()
                reasoning += " ⚠️ Using mock portfolio data (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error collecting portfolio data: {str(e)}"
            state['portfolio_data'] = self._generate_mock_portfolio()
            reasoning += " 🔄 Using fallback portfolio data"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _analyze_trade_orders(self, state: AgentState) -> AgentState:
        """Analyze recent trade orders for compliance"""
        reasoning = "📋 ORDERS: Analyzing recent trade orders for compliance..."
        
        try:
            if self.trading_server:
                # Get recent order history
                orders_result = await self.trading_server.get_order_history("default_user", limit=50)
                
                if orders_result['status'] == 'success':
                    state['trade_orders'] = orders_result.get('orders', [])
                    orders = orders_result.get('orders', [])
                    
                    reasoning += f" ✅ Retrieved {len(orders)} recent orders"
                    
                    # Analyze order patterns
                    executed_orders = [o for o in orders if o.get('status') == 'executed']
                    rejected_orders = [o for o in orders if o.get('status') == 'rejected']
                    
                    reasoning += f" 📊 Executed: {len(executed_orders)}, Rejected: {len(rejected_orders)}"
                    
                    # Check for day trading patterns
                    today_orders = [o for o in orders if o.get('created_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
                    reasoning += f" 📅 Today's orders: {len(today_orders)}"
                    
                    if len(today_orders) > 10:
                        reasoning += " ⚠️ High trading frequency detected"
                else:
                    raise Exception("Failed to retrieve order history")
                    
            else:
                # Generate mock order data
                state['trade_orders'] = self._generate_mock_orders()
                reasoning += " ⚠️ Using mock order data (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error analyzing orders: {str(e)}"
            state['trade_orders'] = self._generate_mock_orders()
            reasoning += " 🔄 Using fallback order data"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _check_position_limits(self, state: AgentState) -> AgentState:
        """Check portfolio positions against compliance limits"""
        reasoning = "⚖️ LIMITS: Checking position limits compliance..."
        
        portfolio_data = state.get('portfolio_data', {})
        compliance_rules = state.get('compliance_rules', {})
        violations = []
        
        try:
            positions = portfolio_data.get('positions', {})
            summary = portfolio_data.get('summary', {})
            total_value = summary.get('total_market_value', 0)
            
            if total_value == 0:
                reasoning += " ⚠️ No portfolio value detected"
                state['position_violations'] = []
                state['reasoning_trace'].append(reasoning)
                state['messages'].append(AIMessage(content=reasoning))
                return state
            
            # Check individual position limits
            max_position = compliance_rules['position_limits']['max_single_position']
            
            for symbol, position in positions.items():
                position_value = position.get('market_value', 0)
                position_percentage = position_value / total_value
                
                if position_percentage > max_position:
                    violation = {
                        'type': 'POSITION_LIMIT_EXCEEDED',
                        'severity': 'MEDIUM',
                        'symbol': symbol,
                        'description': f"Position {symbol} is {position_percentage:.1%} of portfolio, exceeding {max_position:.1%} limit",
                        'current_value': position_percentage,
                        'limit_value': max_position,
                        'recommendation': 'Reduce position size or diversify portfolio'
                    }
                    violations.append(violation)
                    reasoning += f" ❌ {symbol}: {position_percentage:.1%} exceeds {max_position:.1%} limit"
                else:
                    reasoning += f" ✅ {symbol}: {position_percentage:.1%} within limits"
            
            # Check sector concentration
            sector_allocations = self._calculate_sector_allocations(positions, total_value)
            max_sector = compliance_rules['position_limits']['max_sector_concentration']
            
            for sector, allocation in sector_allocations.items():
                if allocation > max_sector:
                    violation = {
                        'type': 'SECTOR_CONCENTRATION_EXCEEDED',
                        'severity': 'LOW',
                        'sector': sector,
                        'description': f"Sector {sector} represents {allocation:.1%} of portfolio, exceeding {max_sector:.1%} guideline",
                        'current_value': allocation,
                        'limit_value': max_sector,
                        'recommendation': 'Diversify across additional sectors'
                    }
                    violations.append(violation)
                    reasoning += f" ⚠️ {sector} sector: {allocation:.1%} exceeds {max_sector:.1%} guideline"
            
            state['position_violations'] = violations
            reasoning += f" 📊 Position compliance check: {len(violations)} violations found"
            
        except Exception as e:
            reasoning += f" ❌ Error checking position limits: {str(e)}"
            state['position_violations'] = []
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _assess_risk_compliance(self, state: AgentState) -> AgentState:
        """Assess portfolio risk compliance"""
        reasoning = "🛡️ RISK: Assessing portfolio risk compliance..."
        
        portfolio_data = state.get('portfolio_data', {})
        compliance_rules = state.get('compliance_rules', {})
        risk_violations = []
        
        try:
            summary = portfolio_data.get('summary', {})
            total_value = summary.get('total_market_value', 0)
            total_pnl = summary.get('total_unrealized_pnl', 0)
            
            if total_value == 0:
                reasoning += " ⚠️ No portfolio value for risk assessment"
                state['risk_violations'] = []
                state['reasoning_trace'].append(reasoning)
                state['messages'].append(AIMessage(content=reasoning))
                return state
            
            # Calculate current portfolio metrics
            pnl_percentage = abs(total_pnl) / total_value if total_value > 0 else 0
            max_var = compliance_rules['risk_limits']['max_portfolio_var']
            
            # Check Value at Risk
            if pnl_percentage > max_var:
                violation = {
                    'type': 'PORTFOLIO_VAR_EXCEEDED',
                    'severity': 'HIGH',
                    'description': f"Portfolio VaR {pnl_percentage:.1%} exceeds {max_var:.1%} limit",
                    'current_value': pnl_percentage,
                    'limit_value': max_var,
                    'recommendation': 'Reduce portfolio risk or hedge positions'
                }
                risk_violations.append(violation)
                reasoning += f" ❌ Portfolio VaR: {pnl_percentage:.1%} exceeds {max_var:.1%} limit"
            else:
                reasoning += f" ✅ Portfolio VaR: {pnl_percentage:.1%} within {max_var:.1%} limit"
            
            # Check drawdown (simplified)
            if total_pnl < 0:
                drawdown_percentage = abs(total_pnl) / total_value
                max_drawdown = compliance_rules['risk_limits']['max_drawdown']
                
                if drawdown_percentage > max_drawdown:
                    violation = {
                        'type': 'MAX_DRAWDOWN_EXCEEDED',
                        'severity': 'HIGH',
                        'description': f"Portfolio drawdown {drawdown_percentage:.1%} exceeds {max_drawdown:.1%} limit",
                        'current_value': drawdown_percentage,
                        'limit_value': max_drawdown,
                        'recommendation': 'Implement stop-loss strategy or reduce exposure'
                    }
                    risk_violations.append(violation)
                    reasoning += f" ❌ Drawdown: {drawdown_percentage:.1%} exceeds {max_drawdown:.1%} limit"
                else:
                    reasoning += f" ✅ Drawdown: {drawdown_percentage:.1%} within {max_drawdown:.1%} limit"
            
            # Check liquidity (cash position)
            # In paper trading, assume some cash is available
            cash_ratio = 0.05  # Assume 5% cash for demo
            min_liquidity = compliance_rules['risk_limits']['min_liquidity_ratio']
            
            if cash_ratio < min_liquidity:
                violation = {
                    'type': 'INSUFFICIENT_LIQUIDITY',
                    'severity': 'MEDIUM',
                    'description': f"Cash ratio {cash_ratio:.1%} below {min_liquidity:.1%} minimum",
                    'current_value': cash_ratio,
                    'limit_value': min_liquidity,
                    'recommendation': 'Maintain higher cash reserves for liquidity'
                }
                risk_violations.append(violation)
                reasoning += f" ⚠️ Liquidity: {cash_ratio:.1%} below {min_liquidity:.1%} minimum"
            else:
                reasoning += f" ✅ Liquidity: {cash_ratio:.1%} above {min_liquidity:.1%} minimum"
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(portfolio_data, compliance_rules)
            reasoning += f" 📊 Overall risk score: {risk_score:.1f}/10"
            
            state['risk_violations'] = risk_violations
            state['risk_assessment'] = {
                'risk_score': risk_score,
                'var_level': pnl_percentage,
                'liquidity_ratio': cash_ratio,
                'violations_count': len(risk_violations)
            }
            
            reasoning += f" 🛡️ Risk compliance check: {len(risk_violations)} violations found"
            
        except Exception as e:
            reasoning += f" ❌ Error assessing risk compliance: {str(e)}"
            state['risk_violations'] = []
            state['risk_assessment'] = {'risk_score': 5.0, 'violations_count': 0}
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _detect_violations(self, state: AgentState) -> AgentState:
        """Detect and categorize all compliance violations"""
        reasoning = "🚨 VIOLATIONS: Detecting and categorizing compliance violations..."
        
        all_violations = []
        
        # Combine violations from different checks
        position_violations = state.get('position_violations', [])
        risk_violations = state.get('risk_violations', [])
        
        all_violations.extend(position_violations)
        all_violations.extend(risk_violations)
        
        # Check trading pattern violations
        trade_violations = self._check_trading_patterns(state.get('trade_orders', []), state.get('compliance_rules', {}))
        all_violations.extend(trade_violations)
        
        # Check regulatory violations
        regulatory_violations = self._check_regulatory_compliance(state)
        all_violations.extend(regulatory_violations)
        
        # Categorize violations by severity
        high_severity = [v for v in all_violations if v.get('severity') == 'HIGH']
        medium_severity = [v for v in all_violations if v.get('severity') == 'MEDIUM']
        low_severity = [v for v in all_violations if v.get('severity') == 'LOW']
        
        reasoning += f" 🚨 Total violations: {len(all_violations)}"
        reasoning += f" 🔴 High severity: {len(high_severity)}"
        reasoning += f" 🟡 Medium severity: {len(medium_severity)}"
        reasoning += f" 🟢 Low severity: {len(low_severity)}"
        
        # Log specific high-severity violations
        for violation in high_severity:
            reasoning += f" ❌ HIGH: {violation.get('type', 'Unknown')} - {violation.get('description', 'No description')}"
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(all_violations)
        reasoning += f" 📊 Overall compliance score: {compliance_score:.1f}/100"
        
        state['compliance_violations'] = all_violations
        state['compliance_score'] = compliance_score
        
        # Add paper trading context
        if state.get('compliance_rules', {}).get('paper_trading', {}).get('enabled'):
            reasoning += " 📝 Note: Operating in paper trading mode - no real financial risk"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _reason_about_compliance(self, state: AgentState) -> AgentState:
        """Apply ReAct reasoning about compliance status"""
        reasoning = "🧠 REASON: Analyzing compliance status and generating recommendations..."
        
        violations = state.get('compliance_violations', [])
        compliance_score = state.get('compliance_score', 100)
        risk_assessment = state.get('risk_assessment', {})
        
        try:
            # Analyze compliance trends
            if compliance_score >= 95:
                compliance_status = "EXCELLENT"
                reasoning += " ✅ EXCELLENT compliance status - all systems operating within parameters"
            elif compliance_score >= 85:
                compliance_status = "GOOD"
                reasoning += " 👍 GOOD compliance status - minor issues detected"
            elif compliance_score >= 70:
                compliance_status = "FAIR"
                reasoning += " ⚠️ FAIR compliance status - attention required"
            else:
                compliance_status = "POOR"
                reasoning += " 🚨 POOR compliance status - immediate action required"
            
            # Generate specific recommendations
            recommendations = []
            
            # Position-based recommendations
            position_violations = [v for v in violations if 'POSITION' in v.get('type', '')]
            if position_violations:
                recommendations.append({
                    'category': 'POSITION_MANAGEMENT',
                    'priority': 'HIGH',
                    'description': 'Rebalance portfolio to comply with position limits',
                    'actions': ['Reduce oversized positions', 'Diversify across more securities']
                })
                reasoning += " 📊 Recommendation: Rebalance portfolio positions"
            
            # Risk-based recommendations
            risk_violations = [v for v in violations if 'RISK' in v.get('type', '') or 'VAR' in v.get('type', '')]
            if risk_violations:
                recommendations.append({
                    'category': 'RISK_MANAGEMENT',
                    'priority': 'HIGH',
                    'description': 'Implement risk reduction measures',
                    'actions': ['Add hedging positions', 'Reduce overall exposure', 'Increase cash reserves']
                })
                reasoning += " 🛡️ Recommendation: Implement risk reduction measures"
            
            # Trading pattern recommendations
            if len(state.get('trade_orders', [])) > 20:  # High frequency
                recommendations.append({
                    'category': 'TRADING_BEHAVIOR',
                    'priority': 'MEDIUM',
                    'description': 'Monitor trading frequency for pattern day trader rules',
                    'actions': ['Track day trade count', 'Consider position holding periods']
                })
                reasoning += " 📈 Recommendation: Monitor trading frequency"
            
            # Paper trading reminder
            if state.get('compliance_rules', {}).get('paper_trading', {}).get('enabled'):
                recommendations.append({
                    'category': 'PAPER_TRADING',
                    'priority': 'INFO',
                    'description': 'System operating in paper trading mode',
                    'actions': ['All trades are simulated', 'No real financial risk']
                })
                reasoning += " 📝 Note: Paper trading mode active - educational purposes"
            
            # Calculate next review time
            if compliance_score < 80:
                next_review_hours = 1  # Immediate review for poor compliance
                reasoning += " ⏰ Next review: 1 hour (urgent)"
            elif compliance_score < 90:
                next_review_hours = 4  # Regular review
                reasoning += " ⏰ Next review: 4 hours (standard)"
            else:
                next_review_hours = 24  # Daily review for good compliance
                reasoning += " ⏰ Next review: 24 hours (routine)"
            
            state['compliance_analysis'] = {
                'status': compliance_status,
                'score': compliance_score,
                'recommendations': recommendations,
                'next_review': (datetime.now() + timedelta(hours=next_review_hours)).isoformat(),
                'risk_level': 'LOW' if compliance_score > 90 else 'HIGH' if compliance_score < 70 else 'MEDIUM'
            }
            
            reasoning += f" 🎯 Compliance analysis complete: {compliance_status} status"
            reasoning += f" 📋 Generated {len(recommendations)} recommendations"
            
        except Exception as e:
            reasoning += f" ❌ Error in compliance reasoning: {str(e)}"
            state['compliance_analysis'] = {
                'status': 'UNKNOWN',
                'score': 50,
                'recommendations': [],
                'risk_level': 'MEDIUM'
            }
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _should_require_hitl_approval(self, state: AgentState) -> str:
        """Determine if HITL approval is required"""
        # Require HITL approval if:
        # 1. High severity violations detected
        # 2. Compliance score below threshold
        # 3. Multiple violations across categories
        
        violations = state.get('compliance_violations', [])
        compliance_score = state.get('compliance_score', 100)
        
        high_severity_violations = [v for v in violations if v.get('severity') == 'HIGH']
        violation_types = set(v.get('type', '') for v in violations)
        
        if (len(high_severity_violations) > 0 or 
            compliance_score < 80 or 
            len(violation_types) > 3):
            state['hitl_approval_required'] = True
            return "hitl_required"
        else:
            state['hitl_approval_required'] = False
            return "no_hitl"
    
    async def _hitl_review(self, state: AgentState) -> AgentState:
        """Handle Human-in-the-Loop review process"""
        reasoning = "👤 HITL: Compliance analysis requires human review due to violations"
        
        violations = state.get('compliance_violations', [])
        compliance_score = state.get('compliance_score', 100)
        
        reasoning += f" 🔍 Review criteria triggered:"
        reasoning += f" - Total violations: {len(violations)}"
        reasoning += f" - Compliance score: {compliance_score:.1f}/100"
        reasoning += f" - High severity violations: {len([v for v in violations if v.get('severity') == 'HIGH'])}"
        
        reasoning += " ⏳ Waiting for human approval..."
        
        # Simulate human decision based on compliance quality
        if compliance_score > 70 and len([v for v in violations if v.get('severity') == 'HIGH']) == 0:
            state['hitl_approved'] = True
            reasoning += " ✅ Compliance status approved by human reviewer"
        else:
            state['hitl_approved'] = False
            reasoning += " ❌ Compliance status rejected - requires remediation"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _check_hitl_approval(self, state: AgentState) -> str:
        """Check HITL approval status"""
        if state.get('hitl_approved') is True:
            return "approved"
        elif state.get('hitl_approved') is False:
            return "rejected"
        else:
            return "pending"
    
    async def _finalize_compliance_report(self, state: AgentState) -> AgentState:
        """Finalize the compliance report"""
        reasoning = "✅ FINALIZE: Compliance monitoring complete"
        
        # Compile final compliance report
        final_report = {
            'compliance_score': state.get('compliance_score', 100),
            'compliance_status': state.get('compliance_analysis', {}).get('status', 'UNKNOWN'),
            'total_violations': len(state.get('compliance_violations', [])),
            'violations_by_severity': {
                'high': len([v for v in state.get('compliance_violations', []) if v.get('severity') == 'HIGH']),
                'medium': len([v for v in state.get('compliance_violations', []) if v.get('severity') == 'MEDIUM']),
                'low': len([v for v in state.get('compliance_violations', []) if v.get('severity') == 'LOW'])
            },
            'violations_detail': state.get('compliance_violations', []),
            'risk_assessment': state.get('risk_assessment', {}),
            'recommendations': state.get('compliance_analysis', {}).get('recommendations', []),
            'next_review': state.get('compliance_analysis', {}).get('next_review'),
            'portfolio_summary': {
                'total_positions': len(state.get('portfolio_data', {}).get('positions', {})),
                'total_value': state.get('portfolio_data', {}).get('summary', {}).get('total_market_value', 0),
                'total_pnl': state.get('portfolio_data', {}).get('summary', {}).get('total_unrealized_pnl', 0)
            },
            'monitoring_metadata': {
                'monitoring_scope': state.get('monitoring_scope', 'full'),
                'paper_trading': state.get('compliance_rules', {}).get('paper_trading', {}).get('enabled', True),
                'hitl_reviewed': state.get('hitl_approval_required', False),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        state['final_compliance_report'] = final_report
        
        reasoning += f" 📊 Compliance Summary:"
        reasoning += f" - Score: {final_report['compliance_score']:.1f}/100"
        reasoning += f" - Status: {final_report['compliance_status']}"
        reasoning += f" - Violations: {final_report['total_violations']}"
        reasoning += f" - Portfolio value: ${final_report['portfolio_summary']['total_value']:,.2f}"
        reasoning += f" - Paper trading: {final_report['monitoring_metadata']['paper_trading']}"
        
        if state.get('hitl_approval_required'):
            reasoning += f" - Human review: {'✅ Approved' if state.get('hitl_approved') else '❌ Rejected'}"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _log_compliance_check(self, state: AgentState) -> AgentState:
        """Log the compliance check to audit files"""
        reasoning = "📝 LOG: Recording compliance check to audit trail"
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id,
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'monitoring_config': {
                'monitoring_scope': state.get('monitoring_scope', 'full')
            },
            'reasoning_trace': state['reasoning_trace'],
            'final_compliance_report': state['final_compliance_report'],
            'hitl_required': state.get('hitl_approval_required', False),
            'hitl_approved': state.get('hitl_approved', None),
            'performance_metrics': {
                'check_time': len(state['reasoning_trace']) * 0.2,
                'compliance_score': state['final_compliance_report']['compliance_score'],
                'violations_detected': state['final_compliance_report']['total_violations']
            }
        }
        
        # Save to audit files
        await self._save_audit_log(audit_entry)
        await self._save_csv_log(audit_entry)
        
        # Save violations to separate log
        if state.get('compliance_violations'):
            await self._save_violations_log(state['compliance_violations'])
        
        reasoning += " ✅ Compliance check logged to audit trail"
        
        state['reasoning_trace'].append(reasoning)
        state['audit_log'] = [audit_entry]
        
        return state
    
    # Helper methods
    def _generate_mock_portfolio(self) -> Dict[str, Any]:
        """Generate mock portfolio data"""
        return {
            'status': 'success',
            'positions': {
                'AAPL': {'shares': 50, 'market_value': 9617.50, 'sector': 'Technology'},
                'MSFT': {'shares': 25, 'market_value': 9968.75, 'sector': 'Technology'},
                'JNJ': {'shares': 75, 'market_value': 12390.00, 'sector': 'Healthcare'},
                'JPM': {'shares': 30, 'market_value': 5053.50, 'sector': 'Finance'}
            },
            'summary': {
                'total_market_value': 37029.75,
                'total_unrealized_pnl': 1529.75,
                'total_positions': 4
            }
        }
    
    def _generate_mock_orders(self) -> List[Dict[str, Any]]:
        """Generate mock order data"""
        import random
        
        orders = []
        for i in range(10):
            orders.append({
                'order_id': f"order_{i:03d}",
                'symbol': random.choice(['AAPL', 'MSFT', 'GOOGL', 'JNJ']),
                'side': random.choice(['buy', 'sell']),
                'quantity': random.randint(10, 100),
                'status': random.choice(['executed', 'executed', 'executed', 'rejected']),
                'created_at': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
                'paper_trading': True
            })
        
        return orders
    
    def _calculate_sector_allocations(self, positions: Dict, total_value: float) -> Dict[str, float]:
        """Calculate sector allocation percentages"""
        sector_values = {}
        
        for position in positions.values():
            sector = position.get('sector', 'Unknown')
            value = position.get('market_value', 0)
            
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += value
        
        # Convert to percentages
        sector_allocations = {}
        for sector, value in sector_values.items():
            sector_allocations[sector] = value / total_value if total_value > 0 else 0
        
        return sector_allocations
    
    def _calculate_risk_score(self, portfolio_data: Dict, compliance_rules: Dict) -> float:
        """Calculate overall portfolio risk score (0-10 scale)"""
        summary = portfolio_data.get('summary', {})
        total_value = summary.get('total_market_value', 0)
        total_pnl = summary.get('total_unrealized_pnl', 0)
        
        if total_value == 0:
            return 5.0  # Neutral risk
        
        # Base risk from P&L volatility
        pnl_ratio = abs(total_pnl) / total_value
        risk_score = min(10, pnl_ratio * 100)  # Scale to 0-10
        
        # Adjust for concentration
        positions = portfolio_data.get('positions', {})
        if len(positions) < 3:
            risk_score += 2  # Concentration risk
        
        return min(10, max(0, risk_score))
    
    def _check_trading_patterns(self, orders: List[Dict], compliance_rules: Dict) -> List[Dict[str, Any]]:
        """Check for trading pattern violations"""
        violations = []
        
        if not orders:
            return violations
        
        # Check for excessive trading
        today_orders = [o for o in orders if o.get('created_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
        
        if len(today_orders) > 10:
            violations.append({
                'type': 'EXCESSIVE_TRADING',
                'severity': 'MEDIUM',
                'description': f"High trading frequency: {len(today_orders)} orders today",
                'recommendation': 'Monitor for pattern day trader rules'
            })
        
        # Check for large orders
        large_order_threshold = compliance_rules.get('reporting_requirements', {}).get('suspicious_activity_threshold', 50000)
        
        for order in orders:
            if order.get('status') == 'executed':
                # Estimate order value (simplified)
                order_value = order.get('quantity', 0) * 100  # Assume $100 per share average
                
                if order_value > large_order_threshold:
                    violations.append({
                        'type': 'LARGE_ORDER_DETECTED',
                        'severity': 'LOW',
                        'description': f"Large order: ${order_value:,.2f} for {order.get('symbol', 'unknown')}",
                        'recommendation': 'Verify order meets reporting requirements'
                    })
        
        return violations
    
    def _check_regulatory_compliance(self, state: AgentState) -> List[Dict[str, Any]]:
        """Check regulatory compliance requirements"""
        violations = []
        compliance_rules = state.get('compliance_rules', {})
        
        # Paper trading compliance
        if compliance_rules.get('paper_trading', {}).get('enabled'):
            # In paper trading, add informational note
            violations.append({
                'type': 'PAPER_TRADING_MODE',
                'severity': 'INFO',
                'description': 'System operating in paper trading mode',
                'recommendation': 'All trades are simulated for educational purposes'
            })
        
        # Check if real-time monitoring is enabled
        if not compliance_rules.get('reporting_requirements', {}).get('real_time_monitoring', True):
            violations.append({
                'type': 'MONITORING_DISABLED',
                'severity': 'HIGH',
                'description': 'Real-time compliance monitoring is disabled',
                'recommendation': 'Enable real-time monitoring for regulatory compliance'
            })
        
        return violations
    
    def _calculate_compliance_score(self, violations: List[Dict]) -> float:
        """Calculate overall compliance score (0-100)"""
        if not violations:
            return 100.0
        
        score = 100.0
        
        for violation in violations:
            severity = violation.get('severity', 'LOW')
            
            if severity == 'HIGH':
                score -= 25
            elif severity == 'MEDIUM':
                score -= 10
            elif severity == 'LOW':
                score -= 5
            # INFO violations don't reduce score
        
        return max(0, score)
    
    async def _save_audit_log(self, audit_entry: Dict[str, Any]):
        """Save audit entry to JSON file"""
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r') as f:
                    audit_log = json.load(f)
            else:
                audit_log = []
            
            audit_log.append(audit_entry)
            
            if len(audit_log) > 1000:
                audit_log = audit_log[-1000:]
            
            with open(self.audit_log_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            print(f"Error saving audit log: {e}")
    
    async def _save_csv_log(self, audit_entry: Dict[str, Any]):
        """Save compliance summary to CSV file"""
        try:
            final_report = audit_entry['final_compliance_report']
            
            csv_row = {
                'timestamp': audit_entry['timestamp'],
                'session_id': audit_entry['session_id'],
                'monitoring_scope': audit_entry['monitoring_config']['monitoring_scope'],
                'compliance_score': final_report['compliance_score'],
                'compliance_status': final_report['compliance_status'],
                'total_violations': final_report['total_violations'],
                'high_severity_violations': final_report['violations_by_severity']['high'],
                'medium_severity_violations': final_report['violations_by_severity']['medium'],
                'low_severity_violations': final_report['violations_by_severity']['low'],
                'portfolio_value': final_report['portfolio_summary']['total_value'],
                'portfolio_pnl': final_report['portfolio_summary']['total_pnl'],
                'paper_trading': final_report['monitoring_metadata']['paper_trading'],
                'hitl_required': audit_entry['hitl_required'],
                'hitl_approved': audit_entry['hitl_approved'],
                'check_time': audit_entry['performance_metrics']['check_time']
            }
            
            file_exists = os.path.exists(self.csv_log_file)
            with open(self.csv_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_row)
                
        except Exception as e:
            print(f"Error saving CSV log: {e}")
    
    async def _save_violations_log(self, violations: List[Dict[str, Any]]):
        """Save violations to separate log file"""
        try:
            violations_entry = {
                'timestamp': datetime.now().isoformat(),
                'violations': violations,
                'total_count': len(violations)
            }
            
            if os.path.exists(self.violations_log_file):
                with open(self.violations_log_file, 'r') as f:
                    violations_log = json.load(f)
            else:
                violations_log = []
            
            violations_log.append(violations_entry)
            
            # Keep only last 500 entries
            if len(violations_log) > 500:
                violations_log = violations_log[-500:]
            
            with open(self.violations_log_file, 'w') as f:
                json.dump(violations_log, f, indent=2)
                
        except Exception as e:
            print(f"Error saving violations log: {e}")
    
    def _initialize_csv_log(self):
        """Initialize CSV log file with headers"""
        if not os.path.exists(self.csv_log_file):
            headers = [
                'timestamp', 'session_id', 'monitoring_scope', 'compliance_score',
                'compliance_status', 'total_violations', 'high_severity_violations',
                'medium_severity_violations', 'low_severity_violations', 'portfolio_value',
                'portfolio_pnl', 'paper_trading', 'hitl_required', 'hitl_approved',
                'check_time'
            ]
            
            with open(self.csv_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    async def monitor_compliance(self, monitoring_scope: str = "full",
                                hitl_enabled: bool = False) -> Dict[str, Any]:
        """Main entry point for compliance monitoring"""
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=f"Monitor compliance for {monitoring_scope} scope")],
            compliance_rules={},
            monitoring_scope=monitoring_scope,
            portfolio_data={},
            trade_orders=[],
            compliance_violations=[],
            risk_assessment={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approved=None,
            final_compliance_report={},
            audit_log=[]
        )
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'compliance_report': final_state['final_compliance_report'],
                'reasoning_trace': final_state['reasoning_trace'],
                'hitl_required': final_state.get('hitl_approval_required', False),
                'hitl_approved': final_state.get('hitl_approved'),
                'audit_log': final_state.get('audit_log', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'version': self.version,
            'status': 'ready',
            'graph_nodes': len(self.graph.nodes),
            'audit_log_file': self.audit_log_file,
            'csv_log_file': self.csv_log_file,
            'violations_log_file': self.violations_log_file,
            'mcp_server_connected': self.trading_server is not None
        }

# Global agent instance
compliance_logger_react_agent = ComplianceLoggerReActAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = ComplianceLoggerReActAgent()
        
        # Test compliance monitoring
        result = await agent.monitor_compliance(
            monitoring_scope="full",
            hitl_enabled=True
        )
        
        print("Compliance Monitoring Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())
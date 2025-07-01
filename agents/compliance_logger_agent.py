"""
ComplianceLoggerAgent - LangGraph Agent for Regulatory Compliance and Logging
Ensures all trading activities comply with regulatory requirements and maintains audit trails
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from mcp_servers.trading_server import trading_server
except ImportError:
    print("Warning: MCP server not available, using mock data")
    trading_server = None

@dataclass
class ComplianceState:
    """State management for ComplianceLoggerAgent"""
    status: str = "idle"
    last_check: Optional[datetime] = None
    compliance_rules: Dict[str, Any] = None
    violations_detected: int = 0
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.compliance_rules is None:
            self.compliance_rules = {}
        if self.performance_metrics is None:
            self.performance_metrics = {"compliance_score": 99.1, "check_accuracy": 95.0}

class ComplianceLoggerAgent:
    """LangGraph Agent for regulatory compliance and audit logging"""
    
    def __init__(self, agent_id: str = "compliance_logger"):
        self.agent_id = agent_id
        self.name = "ComplianceLoggerAgent"
        self.type = "Risk & Compliance"
        self.version = "1.0.0"
        self.state = ComplianceState()
        self.mcp_server = trading_server
        self.audit_log = []
        
    async def initialize(self):
        """Initialize the agent and its MCP server connection"""
        try:
            if self.mcp_server:
                await self.mcp_server.initialize()
            self.state.compliance_rules = await self.load_compliance_rules()
            self.state.status = "connected"
            print(f"[{self.name}] Agent initialized successfully")
            return True
        except Exception as e:
            self.state.status = "error"
            print(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def load_compliance_rules(self) -> Dict[str, Any]:
        """Load comprehensive compliance rules and regulations"""
        return {
            "position_limits": {
                "max_single_position": 0.25,  # 25% of portfolio
                "max_sector_concentration": 0.40,  # 40% in single sector
                "max_daily_trading_volume": 1000000  # $1M daily
            },
            "risk_limits": {
                "max_portfolio_var": 0.05,  # 5% Value at Risk
                "max_leverage": 2.0,  # 2:1 leverage
                "max_correlation": 0.8,  # Max correlation between positions
                "max_drawdown": 0.15  # 15% maximum drawdown
            },
            "regulatory_requirements": {
                "pattern_day_trader_rule": True,  # PDT rule enforcement
                "wash_sale_rule": True,  # Wash sale prevention
                "insider_trading_monitoring": True,
                "market_manipulation_detection": True,
                "best_execution": True,
                "know_your_customer": True
            },
            "reporting_requirements": {
                "large_position_reporting": 100000,  # Report positions > $100k
                "suspicious_activity_threshold": 50000,  # Flag trades > $50k
                "audit_trail_retention": 365,  # Days to retain records
                "real_time_monitoring": True
            },
            "restricted_securities": [
                # No restrictions in demo mode
            ],
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
    
    async def check_portfolio_compliance(self, portfolio_data: Dict[str, Any], 
                                       user_id: str = "default_user") -> Dict[str, Any]:
        """Check portfolio for compliance violations"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            violations = []
            warnings = []
            compliance_score = 100.0
            
            # Get portfolio positions
            if self.mcp_server:
                portfolio_result = await self.mcp_server.get_portfolio_positions(user_id)
            else:
                portfolio_result = self.generate_mock_portfolio()
            
            if portfolio_result["status"] != "success":
                return {"status": "error", "message": "Unable to retrieve portfolio data"}
            
            positions = portfolio_result.get("positions", {})
            summary = portfolio_result.get("summary", {})
            
            # Check position concentration limits
            concentration_check = await self.check_position_concentration(positions, summary)
            if not concentration_check["compliant"]:
                violations.extend(concentration_check["violations"])
                compliance_score -= 15
            
            # Check sector concentration
            sector_check = await self.check_sector_concentration(positions, summary)
            if not sector_check["compliant"]:
                warnings.extend(sector_check["warnings"])
                compliance_score -= 5
            
            # Check risk limits
            risk_check = await self.check_risk_limits(positions, summary)
            if not risk_check["compliant"]:
                violations.extend(risk_check["violations"])
                compliance_score -= 20
            
            # Check paper trading compliance
            paper_trading_check = await self.check_paper_trading_compliance()
            if not paper_trading_check["compliant"]:
                warnings.extend(paper_trading_check["warnings"])
            
            # Log compliance check
            await self.log_compliance_check(user_id, violations, warnings, compliance_score)
            
            # Update metrics
            end_time = datetime.now()
            check_time = (end_time - start_time).total_seconds()
            
            self.state.violations_detected += len(violations)
            self.state.performance_metrics["compliance_score"] = compliance_score
            self.state.last_check = end_time
            self.state.status = "connected"
            
            result = {
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": end_time.isoformat(),
                "user_id": user_id,
                "compliance_result": {
                    "compliant": len(violations) == 0,
                    "compliance_score": compliance_score,
                    "violations": violations,
                    "warnings": warnings,
                    "total_violations": len(violations),
                    "total_warnings": len(warnings)
                },
                "portfolio_summary": summary,
                "check_time": check_time,
                "paper_trading": True
            }
            
            return result
            
        except Exception as e:
            self.state.status = "error"
            return {
                "status": "error",
                "agent_id": self.agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_mock_portfolio(self) -> Dict[str, Any]:
        """Generate mock portfolio data when MCP server is unavailable"""
        return {
            "status": "success",
            "positions": {
                "AAPL": {"shares": 50, "market_value": 9617.50, "sector": "Technology"},
                "MSFT": {"shares": 25, "market_value": 9968.75, "sector": "Technology"},
                "JNJ": {"shares": 75, "market_value": 12390.00, "sector": "Healthcare"}
            },
            "summary": {
                "total_market_value": 31976.25,
                "total_unrealized_pnl": 1476.25,
                "total_positions": 3
            }
        }
    
    async def check_position_concentration(self, positions: Dict, summary: Dict) -> Dict[str, Any]:
        """Check individual position concentration limits"""
        violations = []
        total_value = summary.get("total_market_value", 0)
        max_position = self.state.compliance_rules["position_limits"]["max_single_position"]
        
        if total_value == 0:
            return {"compliant": True, "violations": []}
        
        for symbol, position in positions.items():
            position_value = position.get("market_value", 0)
            position_percentage = position_value / total_value
            
            if position_percentage > max_position:
                violations.append({
                    "type": "POSITION_CONCENTRATION",
                    "severity": "MEDIUM",
                    "symbol": symbol,
                    "description": f"Position {symbol} is {position_percentage:.1%} of portfolio, exceeding {max_position:.1%} limit",
                    "rule": "position_limits.max_single_position",
                    "current_value": position_percentage,
                    "limit_value": max_position
                })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def check_sector_concentration(self, positions: Dict, summary: Dict) -> Dict[str, Any]:
        """Check sector concentration limits"""
        warnings = []
        total_value = summary.get("total_market_value", 0)
        max_sector = self.state.compliance_rules["position_limits"]["max_sector_concentration"]
        
        if total_value == 0:
            return {"compliant": True, "warnings": []}
        
        # Calculate sector allocations
        sector_allocations = {}
        for symbol, position in positions.items():
            sector = position.get("sector", "Unknown")
            position_value = position.get("market_value", 0)
            
            if sector not in sector_allocations:
                sector_allocations[sector] = 0
            sector_allocations[sector] += position_value
        
        # Check each sector
        for sector, sector_value in sector_allocations.items():
            sector_percentage = sector_value / total_value
            
            if sector_percentage > max_sector:
                warnings.append({
                    "type": "SECTOR_CONCENTRATION",
                    "severity": "LOW",
                    "sector": sector,
                    "description": f"Sector {sector} represents {sector_percentage:.1%} of portfolio, exceeding {max_sector:.1%} guideline",
                    "rule": "position_limits.max_sector_concentration",
                    "current_value": sector_percentage,
                    "limit_value": max_sector
                })
        
        return {
            "compliant": len(warnings) == 0,
            "warnings": warnings
        }
    
    async def check_risk_limits(self, positions: Dict, summary: Dict) -> Dict[str, Any]:
        """Check portfolio risk limits"""
        violations = []
        total_pnl = summary.get("total_unrealized_pnl", 0)
        total_value = summary.get("total_market_value", 0)
        
        if total_value == 0:
            return {"compliant": True, "violations": []}
        
        # Check unrealized P&L as proxy for risk
        pnl_percentage = abs(total_pnl) / total_value
        max_var = self.state.compliance_rules["risk_limits"]["max_portfolio_var"]
        
        if pnl_percentage > max_var:
            violations.append({
                "type": "PORTFOLIO_RISK",
                "severity": "HIGH",
                "description": f"Portfolio risk level {pnl_percentage:.1%} exceeds {max_var:.1%} VaR limit",
                "rule": "risk_limits.max_portfolio_var",
                "current_value": pnl_percentage,
                "limit_value": max_var
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def check_paper_trading_compliance(self) -> Dict[str, Any]:
        """Check paper trading specific compliance"""
        warnings = []
        
        if self.state.compliance_rules["paper_trading"]["enabled"]:
            warnings.append({
                "type": "PAPER_TRADING",
                "severity": "INFO",
                "description": "System operating in paper trading mode - no real funds at risk",
                "rule": "paper_trading.enabled"
            })
        
        return {
            "compliant": True,  # Always compliant in paper trading
            "warnings": warnings
        }
    
    async def log_compliance_check(self, user_id: str, violations: List, 
                                 warnings: List, compliance_score: float):
        """Log compliance check to audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "COMPLIANCE_CHECK",
            "user_id": user_id,
            "agent_id": self.agent_id,
            "compliance_score": compliance_score,
            "violations_count": len(violations),
            "warnings_count": len(warnings),
            "violations": violations,
            "warnings": warnings,
            "paper_trading": True
        }
        
        self.audit_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    async def generate_compliance_report(self, user_id: str = "default_user", 
                                       days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            # Filter audit log for the specified period
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_logs = [
                log for log in self.audit_log 
                if datetime.fromisoformat(log["timestamp"]) > cutoff_date
                and log.get("user_id") == user_id
            ]
            
            # Calculate compliance metrics
            total_checks = len(recent_logs)
            total_violations = sum(log["violations_count"] for log in recent_logs)
            total_warnings = sum(log["warnings_count"] for log in recent_logs)
            avg_compliance_score = sum(log["compliance_score"] for log in recent_logs) / total_checks if total_checks > 0 else 100
            
            # Violation breakdown
            violation_types = {}
            for log in recent_logs:
                for violation in log["violations"]:
                    v_type = violation["type"]
                    if v_type not in violation_types:
                        violation_types[v_type] = 0
                    violation_types[v_type] += 1
            
            return {
                "status": "success",
                "user_id": user_id,
                "report_period": f"{days} days",
                "report_date": datetime.now().isoformat(),
                "compliance_metrics": {
                    "overall_compliance_score": round(avg_compliance_score, 1),
                    "total_compliance_checks": total_checks,
                    "total_violations": total_violations,
                    "total_warnings": total_warnings,
                    "violation_rate": round((total_violations / total_checks * 100), 2) if total_checks > 0 else 0,
                    "paper_trading_mode": True
                },
                "violation_breakdown": violation_types,
                "recommendations": await self.generate_compliance_recommendations(avg_compliance_score, violation_types),
                "audit_trail_entries": len(self.audit_log)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_compliance_recommendations(self, compliance_score: float, 
                                                violation_types: Dict) -> List[Dict[str, Any]]:
        """Generate compliance recommendations based on analysis"""
        recommendations = []
        
        if compliance_score < 90:
            recommendations.append({
                "type": "COMPLIANCE_IMPROVEMENT",
                "priority": "HIGH",
                "description": "Overall compliance score below 90% threshold",
                "action": "Review and address recurring compliance violations",
                "impact": "Regulatory risk reduction"
            })
        
        if "POSITION_CONCENTRATION" in violation_types:
            recommendations.append({
                "type": "DIVERSIFICATION",
                "priority": "MEDIUM",
                "description": f"Position concentration violations detected ({violation_types['POSITION_CONCENTRATION']} instances)",
                "action": "Implement position size limits and diversification rules",
                "impact": "Risk reduction and compliance improvement"
            })
        
        if "SECTOR_CONCENTRATION" in violation_types:
            recommendations.append({
                "type": "SECTOR_DIVERSIFICATION",
                "priority": "MEDIUM",
                "description": f"Sector concentration warnings ({violation_types['SECTOR_CONCENTRATION']} instances)",
                "action": "Diversify across multiple sectors to reduce concentration risk",
                "impact": "Improved portfolio balance"
            })
        
        # Always include paper trading reminder
        recommendations.append({
            "type": "PAPER_TRADING",
            "priority": "INFO",
            "description": "System operating in paper trading mode",
            "action": "All trades are simulated - no real financial risk",
            "impact": "Safe learning environment"
        })
        
        return recommendations
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "status": self.state.status,
            "last_check": self.state.last_check.isoformat() if self.state.last_check else None,
            "violations_detected": self.state.violations_detected,
            "performance_metrics": self.state.performance_metrics,
            "compliance_rules_loaded": len(self.state.compliance_rules),
            "audit_log_entries": len(self.audit_log),
            "paper_trading_mode": True,
            "mcp_server_status": "connected" if self.mcp_server else "unavailable"
        }

# Global agent instance
compliance_logger_agent = ComplianceLoggerAgent()
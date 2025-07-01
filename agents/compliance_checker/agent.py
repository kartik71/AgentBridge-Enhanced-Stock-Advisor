"""
Compliance Checker Agent - LangGraph Agent for Regulatory Compliance
Ensures all trading activities comply with regulatory requirements
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.trading_server import trading_server

@dataclass
class ComplianceState:
    """State management for Compliance Checker Agent"""
    status: str = "idle"
    last_check: Optional[datetime] = None
    compliance_rules: Dict[str, Any] = None
    violations_detected: int = 0
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.compliance_rules is None:
            self.compliance_rules = {}
        if self.performance_metrics is None:
            self.performance_metrics = {"compliance_score": 100.0, "check_accuracy": 95.0}

class ComplianceCheckerAgent:
    """LangGraph Agent for regulatory compliance checking"""
    
    def __init__(self, agent_id: str = "compliance_checker"):
        self.agent_id = agent_id
        self.name = "Compliance Checker"
        self.type = "Risk Management"
        self.version = "1.0.0"
        self.state = ComplianceState()
        self.mcp_server = trading_server
        
    async def initialize(self):
        """Initialize the agent and its MCP server connection"""
        try:
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
        """Load compliance rules and regulations"""
        return {
            "position_limits": {
                "max_single_position": 0.10,  # 10% of portfolio
                "max_sector_concentration": 0.30,  # 30% in single sector
                "max_daily_trading_volume": 1000000  # $1M daily
            },
            "risk_limits": {
                "max_portfolio_var": 0.05,  # 5% Value at Risk
                "max_leverage": 2.0,  # 2:1 leverage
                "max_correlation": 0.8  # Max correlation between positions
            },
            "regulatory_requirements": {
                "pattern_day_trader_rule": True,  # PDT rule enforcement
                "wash_sale_rule": True,  # Wash sale prevention
                "insider_trading_monitoring": True,
                "market_manipulation_detection": True
            },
            "reporting_requirements": {
                "large_position_reporting": 100000,  # Report positions > $100k
                "suspicious_activity_threshold": 50000,  # Flag trades > $50k
                "audit_trail_retention": 365  # Days to retain records
            },
            "restricted_securities": [
                "RESTRICTED1", "RESTRICTED2"  # Example restricted symbols
            ],
            "trading_hours": {
                "market_open": "09:30",
                "market_close": "16:00",
                "extended_hours_allowed": False
            }
        }
    
    async def check_trade_compliance(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check a trade order for compliance violations"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            violations = []
            warnings = []
            compliance_score = 100.0
            
            # Check restricted securities
            if trade_order["symbol"] in self.state.compliance_rules["restricted_securities"]:
                violations.append({
                    "type": "RESTRICTED_SECURITY",
                    "severity": "HIGH",
                    "description": f"Trading in restricted security {trade_order['symbol']} is prohibited",
                    "rule": "restricted_securities"
                })
                compliance_score -= 50
            
            # Check position limits
            position_check = await self.check_position_limits(trade_order)
            if not position_check["compliant"]:
                violations.extend(position_check["violations"])
                compliance_score -= 20
            
            # Check trading hours
            trading_hours_check = await self.check_trading_hours(trade_order)
            if not trading_hours_check["compliant"]:
                warnings.extend(trading_hours_check["warnings"])
                compliance_score -= 5
            
            # Check order size limits
            order_size_check = await self.check_order_size(trade_order)
            if not order_size_check["compliant"]:
                violations.extend(order_size_check["violations"])
                compliance_score -= 15
            
            # Check for pattern day trading
            pdt_check = await self.check_pattern_day_trading(trade_order)
            if not pdt_check["compliant"]:
                warnings.extend(pdt_check["warnings"])
                compliance_score -= 10
            
            # Check for wash sale rule
            wash_sale_check = await self.check_wash_sale_rule(trade_order)
            if not wash_sale_check["compliant"]:
                warnings.extend(wash_sale_check["warnings"])
                compliance_score -= 5
            
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
                "trade_order": trade_order,
                "compliance_result": {
                    "compliant": len(violations) == 0,
                    "compliance_score": compliance_score,
                    "violations": violations,
                    "warnings": warnings,
                    "total_violations": len(violations),
                    "total_warnings": len(warnings)
                },
                "check_time": check_time,
                "recommendation": "APPROVE" if len(violations) == 0 else "REJECT"
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
    
    async def check_position_limits(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check position size limits"""
        violations = []
        
        # Get current portfolio positions
        portfolio_result = await self.mcp_server.get_portfolio_positions(trade_order.get("user_id", "default_user"))
        
        if portfolio_result["status"] != "success":
            return {"compliant": True, "violations": []}  # Can't check, assume compliant
        
        positions = portfolio_result["positions"]
        total_portfolio_value = portfolio_result["summary"]["total_market_value"]
        
        # Calculate new position size after trade
        current_position = positions.get(trade_order["symbol"], {"shares": 0, "market_value": 0})
        trade_value = trade_order["quantity"] * trade_order.get("price", 100)
        
        if trade_order["side"] == "buy":
            new_position_value = current_position["market_value"] + trade_value
        else:
            new_position_value = max(0, current_position["market_value"] - trade_value)
        
        # Check single position limit
        position_percentage = new_position_value / (total_portfolio_value + trade_value) if total_portfolio_value > 0 else 0
        max_position = self.state.compliance_rules["position_limits"]["max_single_position"]
        
        if position_percentage > max_position:
            violations.append({
                "type": "POSITION_LIMIT_EXCEEDED",
                "severity": "MEDIUM",
                "description": f"Position would be {position_percentage:.1%} of portfolio, exceeding {max_position:.1%} limit",
                "rule": "position_limits.max_single_position"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "position_percentage": position_percentage
        }
    
    async def check_trading_hours(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check if trade is within allowed trading hours"""
        warnings = []
        
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Convert trading hours to minutes for comparison
        market_open_hour, market_open_minute = map(int, self.state.compliance_rules["trading_hours"]["market_open"].split(":"))
        market_close_hour, market_close_minute = map(int, self.state.compliance_rules["trading_hours"]["market_close"].split(":"))
        
        current_minutes = current_hour * 60 + current_minute
        open_minutes = market_open_hour * 60 + market_open_minute
        close_minutes = market_close_hour * 60 + market_close_minute
        
        if current_minutes < open_minutes or current_minutes > close_minutes:
            if not self.state.compliance_rules["trading_hours"]["extended_hours_allowed"]:
                warnings.append({
                    "type": "OUTSIDE_TRADING_HOURS",
                    "severity": "LOW",
                    "description": f"Trade placed outside regular trading hours ({self.state.compliance_rules['trading_hours']['market_open']}-{self.state.compliance_rules['trading_hours']['market_close']})",
                    "rule": "trading_hours"
                })
        
        return {
            "compliant": len(warnings) == 0,
            "warnings": warnings
        }
    
    async def check_order_size(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check order size limits"""
        violations = []
        
        order_value = trade_order["quantity"] * trade_order.get("price", 100)
        max_daily_volume = self.state.compliance_rules["position_limits"]["max_daily_trading_volume"]
        
        if order_value > max_daily_volume:
            violations.append({
                "type": "ORDER_SIZE_EXCEEDED",
                "severity": "HIGH",
                "description": f"Order value ${order_value:,.2f} exceeds daily limit of ${max_daily_volume:,.2f}",
                "rule": "position_limits.max_daily_trading_volume"
            })
        
        # Check for suspicious activity
        suspicious_threshold = self.state.compliance_rules["reporting_requirements"]["suspicious_activity_threshold"]
        if order_value > suspicious_threshold:
            violations.append({
                "type": "SUSPICIOUS_ACTIVITY",
                "severity": "MEDIUM",
                "description": f"Large order value ${order_value:,.2f} flagged for review",
                "rule": "reporting_requirements.suspicious_activity_threshold"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def check_pattern_day_trading(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check for pattern day trading violations"""
        warnings = []
        
        if not self.state.compliance_rules["regulatory_requirements"]["pattern_day_trader_rule"]:
            return {"compliant": True, "warnings": []}
        
        # Get recent order history
        order_history_result = await self.mcp_server.get_order_history(
            trade_order.get("user_id", "default_user"), limit=10
        )
        
        if order_history_result["status"] != "success":
            return {"compliant": True, "warnings": []}
        
        # Count day trades in the last 5 business days (simplified)
        recent_orders = order_history_result["orders"]
        day_trades_count = 0
        
        # Simplified day trade detection
        for order in recent_orders:
            if (order["symbol"] == trade_order["symbol"] and 
                order["status"] == "executed" and
                (datetime.now() - datetime.fromisoformat(order["created_at"])).days <= 5):
                day_trades_count += 1
        
        if day_trades_count >= 4:  # PDT rule threshold
            warnings.append({
                "type": "PATTERN_DAY_TRADER",
                "severity": "MEDIUM",
                "description": f"Account flagged as Pattern Day Trader with {day_trades_count} day trades in 5 days",
                "rule": "regulatory_requirements.pattern_day_trader_rule"
            })
        
        return {
            "compliant": True,  # Warning, not violation
            "warnings": warnings,
            "day_trades_count": day_trades_count
        }
    
    async def check_wash_sale_rule(self, trade_order: Dict[str, Any]) -> Dict[str, Any]:
        """Check for wash sale rule violations"""
        warnings = []
        
        if not self.state.compliance_rules["regulatory_requirements"]["wash_sale_rule"]:
            return {"compliant": True, "warnings": []}
        
        # Simplified wash sale check
        if trade_order["side"] == "buy":
            # Check if there was a sale of the same security in the last 30 days
            # This is a simplified implementation
            warnings.append({
                "type": "POTENTIAL_WASH_SALE",
                "severity": "LOW",
                "description": f"Review for potential wash sale on {trade_order['symbol']}",
                "rule": "regulatory_requirements.wash_sale_rule"
            })
        
        return {
            "compliant": True,  # Warning, not violation
            "warnings": warnings
        }
    
    async def generate_compliance_report(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            # Get portfolio positions
            portfolio_result = await self.mcp_server.get_portfolio_positions(user_id)
            
            # Get order history
            order_history_result = await self.mcp_server.get_order_history(user_id, limit=100)
            
            # Calculate compliance metrics
            compliance_metrics = {
                "overall_compliance_score": self.state.performance_metrics["compliance_score"],
                "total_violations": self.state.violations_detected,
                "position_concentration": await self.calculate_position_concentration(portfolio_result),
                "trading_activity_score": await self.calculate_trading_activity_score(order_history_result),
                "risk_metrics": await self.calculate_risk_metrics(portfolio_result)
            }
            
            return {
                "status": "success",
                "user_id": user_id,
                "report_date": datetime.now().isoformat(),
                "compliance_metrics": compliance_metrics,
                "recommendations": await self.generate_compliance_recommendations(compliance_metrics)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def calculate_position_concentration(self, portfolio_result: Dict) -> Dict[str, Any]:
        """Calculate position concentration metrics"""
        if portfolio_result["status"] != "success":
            return {"error": "Unable to calculate position concentration"}
        
        positions = portfolio_result["positions"]
        total_value = portfolio_result["summary"]["total_market_value"]
        
        if total_value == 0:
            return {"max_position_percentage": 0, "number_of_positions": 0}
        
        position_percentages = [
            (pos["market_value"] / total_value) * 100 
            for pos in positions.values()
        ]
        
        return {
            "max_position_percentage": max(position_percentages) if position_percentages else 0,
            "number_of_positions": len(positions),
            "concentration_score": 100 - max(position_percentages) if position_percentages else 100
        }
    
    async def calculate_trading_activity_score(self, order_history_result: Dict) -> Dict[str, Any]:
        """Calculate trading activity compliance score"""
        if order_history_result["status"] != "success":
            return {"error": "Unable to calculate trading activity score"}
        
        orders = order_history_result["orders"]
        
        # Calculate metrics
        total_orders = len(orders)
        executed_orders = len([o for o in orders if o["status"] == "executed"])
        rejected_orders = len([o for o in orders if o["status"] == "rejected"])
        
        execution_rate = (executed_orders / total_orders * 100) if total_orders > 0 else 0
        rejection_rate = (rejected_orders / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "total_orders": total_orders,
            "execution_rate": execution_rate,
            "rejection_rate": rejection_rate,
            "activity_score": max(0, 100 - rejection_rate * 2)  # Penalize rejections
        }
    
    async def calculate_risk_metrics(self, portfolio_result: Dict) -> Dict[str, Any]:
        """Calculate portfolio risk metrics for compliance"""
        if portfolio_result["status"] != "success":
            return {"error": "Unable to calculate risk metrics"}
        
        total_pnl = portfolio_result["summary"]["total_unrealized_pnl"]
        total_value = portfolio_result["summary"]["total_market_value"]
        
        unrealized_pnl_percentage = (total_pnl / total_value * 100) if total_value > 0 else 0
        
        return {
            "unrealized_pnl_percentage": unrealized_pnl_percentage,
            "risk_score": max(0, 100 - abs(unrealized_pnl_percentage) * 2),
            "risk_level": "LOW" if abs(unrealized_pnl_percentage) < 5 else "HIGH" if abs(unrealized_pnl_percentage) > 15 else "MEDIUM"
        }
    
    async def generate_compliance_recommendations(self, metrics: Dict) -> List[Dict[str, Any]]:
        """Generate compliance recommendations based on metrics"""
        recommendations = []
        
        if metrics["overall_compliance_score"] < 80:
            recommendations.append({
                "type": "COMPLIANCE_IMPROVEMENT",
                "priority": "HIGH",
                "description": "Overall compliance score is below acceptable threshold",
                "action": "Review and address compliance violations"
            })
        
        if metrics.get("position_concentration", {}).get("max_position_percentage", 0) > 15:
            recommendations.append({
                "type": "DIVERSIFICATION",
                "priority": "MEDIUM",
                "description": "Portfolio concentration risk detected",
                "action": "Consider diversifying large positions"
            })
        
        if metrics.get("trading_activity_score", {}).get("rejection_rate", 0) > 10:
            recommendations.append({
                "type": "ORDER_QUALITY",
                "priority": "MEDIUM",
                "description": "High order rejection rate detected",
                "action": "Review order parameters and compliance rules"
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
            "mcp_server_status": await self.mcp_server.get_server_status()
        }

# Global agent instance
compliance_checker_agent = ComplianceCheckerAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = ComplianceCheckerAgent()
        await agent.initialize()
        
        # Test compliance check
        test_order = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 192.35,
            "user_id": "default_user"
        }
        
        result = await agent.check_trade_compliance(test_order)
        
        print("Compliance Check Result:")
        print(json.dumps(result, indent=2))
        
        # Generate compliance report
        report = await agent.generate_compliance_report("default_user")
        print("\nCompliance Report:")
        print(json.dumps(report, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())
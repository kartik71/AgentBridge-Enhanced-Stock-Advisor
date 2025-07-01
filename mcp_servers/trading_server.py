"""
Trading Server - MCP Server for Trade Execution and Compliance
Handles simulated trade execution, compliance checking, and order management
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class TradingServer:
    def __init__(self):
        self.name = "trading_server"
        self.version = "1.0.0"
        self.description = "Simulated Trade Execution and Compliance Engine"
        self.orders = {}
        self.compliance_rules = {}
        self.portfolio_positions = {}
        self.paper_trading = True  # Always in paper trading mode for demo
        
    async def initialize(self):
        """Initialize the trading server"""
        await self.setup_compliance_rules()
        await self.initialize_demo_portfolio()
        print(f"[{self.name}] Server initialized successfully (Paper Trading Mode)")
        
    async def setup_compliance_rules(self):
        """Setup compliance rules for trading"""
        self.compliance_rules = {
            "max_position_size": 0.25,  # Max 25% of portfolio in single position
            "max_daily_trades": 50,
            "max_order_value": 100000,
            "restricted_symbols": [],  # No restrictions in demo
            "trading_hours": {
                "start": "09:30",
                "end": "16:00",
                "timezone": "EST"
            },
            "risk_limits": {
                "max_portfolio_risk": 0.20,
                "max_sector_concentration": 0.40
            }
        }
    
    async def initialize_demo_portfolio(self):
        """Initialize demo portfolio positions"""
        self.portfolio_positions = {
            "AAPL": {
                "shares": 50,
                "avg_cost": 180.00,
                "current_price": 192.35,
                "market_value": 9617.50,
                "unrealized_pnl": 617.50,
                "sector": "Technology"
            },
            "MSFT": {
                "shares": 25,
                "avg_cost": 380.00,
                "current_price": 398.75,
                "market_value": 9968.75,
                "unrealized_pnl": 468.75,
                "sector": "Technology"
            },
            "JNJ": {
                "shares": 75,
                "avg_cost": 160.00,
                "current_price": 165.20,
                "market_value": 12390.00,
                "unrealized_pnl": 390.00,
                "sector": "Healthcare"
            }
        }
    
    async def validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order against compliance rules"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check order value limits
        order_value = order["quantity"] * order.get("price", 0)
        if order_value > self.compliance_rules["max_order_value"]:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Order value ${order_value:,.2f} exceeds limit")
        
        # Check position size limits
        total_portfolio_value = sum(pos["market_value"] for pos in self.portfolio_positions.values())
        position_value = order["quantity"] * order.get("price", 100)
        position_percentage = position_value / (total_portfolio_value + position_value) if total_portfolio_value > 0 else 0
        
        if position_percentage > self.compliance_rules["max_position_size"]:
            validation_result["warnings"].append(f"Position would be {position_percentage:.1%} of portfolio")
        
        # Paper trading warning
        validation_result["warnings"].append("Paper trading mode - no real money involved")
        
        return validation_result
    
    async def submit_order(self, symbol: str, side: str, quantity: int, 
                          order_type: str = "market", price: float = None,
                          user_id: str = "default_user") -> Dict[str, Any]:
        """Submit a simulated trading order"""
        
        order_id = str(uuid.uuid4())
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side.lower(),
            "quantity": quantity,
            "order_type": order_type.lower(),
            "price": price,
            "user_id": user_id,
            "status": OrderStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "paper_trading": True
        }
        
        # Validate order
        validation = await self.validate_order(order)
        
        if not validation["valid"]:
            order["status"] = OrderStatus.REJECTED.value
            order["rejection_reason"] = "; ".join(validation["errors"])
            self.orders[order_id] = order
            
            return {
                "status": "rejected",
                "order_id": order_id,
                "errors": validation["errors"],
                "warnings": validation["warnings"]
            }
        
        # Simulate order execution
        execution_price = await self.get_current_price(symbol)
        order["executed_price"] = execution_price
        order["executed_quantity"] = quantity
        order["status"] = OrderStatus.EXECUTED.value
        order["executed_at"] = datetime.now().isoformat()
        
        # Update portfolio positions (simulated)
        await self.update_portfolio_position(symbol, side, quantity, execution_price)
        
        self.orders[order_id] = order
        
        return {
            "status": "executed",
            "order_id": order_id,
            "order": order,
            "warnings": validation["warnings"]
        }
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol (simulated)"""
        price_map = {
            "AAPL": 192.35,
            "MSFT": 398.75,
            "GOOGL": 142.50,
            "NVDA": 465.20,
            "TSLA": 198.50,
            "JNJ": 165.20,
            "PFE": 28.90,
            "JPM": 168.45,
            "BAC": 32.15,
            "KO": 58.75
        }
        base_price = price_map.get(symbol, 100.00)
        # Add small random variation
        return round(base_price * (0.98 + 0.04 * random.random()), 2)
    
    async def update_portfolio_position(self, symbol: str, side: str, 
                                      quantity: int, price: float):
        """Update portfolio position after trade execution (simulated)"""
        if symbol not in self.portfolio_positions:
            self.portfolio_positions[symbol] = {
                "shares": 0,
                "avg_cost": 0,
                "current_price": price,
                "market_value": 0,
                "unrealized_pnl": 0,
                "sector": "Unknown"
            }
        
        position = self.portfolio_positions[symbol]
        
        if side == "buy":
            total_cost = (position["shares"] * position["avg_cost"]) + (quantity * price)
            total_shares = position["shares"] + quantity
            position["avg_cost"] = total_cost / total_shares if total_shares > 0 else 0
            position["shares"] = total_shares
        else:  # sell
            position["shares"] -= quantity
            if position["shares"] <= 0:
                position["shares"] = 0
                position["avg_cost"] = 0
        
        # Update market value and P&L
        position["current_price"] = price
        position["market_value"] = position["shares"] * price
        position["unrealized_pnl"] = (price - position["avg_cost"]) * position["shares"]
    
    async def get_portfolio_positions(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Get current portfolio positions"""
        total_value = sum(pos["market_value"] for pos in self.portfolio_positions.values())
        total_pnl = sum(pos["unrealized_pnl"] for pos in self.portfolio_positions.values())
        
        return {
            "status": "success",
            "user_id": user_id,
            "positions": self.portfolio_positions,
            "summary": {
                "total_market_value": round(total_value, 2),
                "total_unrealized_pnl": round(total_pnl, 2),
                "total_positions": len(self.portfolio_positions),
                "paper_trading": True,
                "updated_at": datetime.now().isoformat()
            }
        }
    
    async def get_order_history(self, user_id: str = "default_user", 
                               limit: int = 50) -> Dict[str, Any]:
        """Get order history for user"""
        user_orders = [
            order for order in self.orders.values() 
            if order["user_id"] == user_id
        ]
        
        # Sort by creation date, most recent first
        user_orders.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "user_id": user_id,
            "orders": user_orders[:limit],
            "total_orders": len(user_orders),
            "paper_trading": True
        }
    
    async def get_compliance_report(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Generate compliance report"""
        total_orders = len([o for o in self.orders.values() if o["user_id"] == user_id])
        executed_orders = len([o for o in self.orders.values() 
                              if o["user_id"] == user_id and o["status"] == "executed"])
        
        return {
            "status": "success",
            "user_id": user_id,
            "compliance_score": 100,  # Perfect score in demo mode
            "total_orders": total_orders,
            "executed_orders": executed_orders,
            "violations": 0,
            "paper_trading": True,
            "report_date": datetime.now().isoformat()
        }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server health status"""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy",
            "uptime": datetime.now().isoformat(),
            "total_orders": len(self.orders),
            "active_positions": len(self.portfolio_positions),
            "paper_trading": True,
            "compliance_rules_loaded": len(self.compliance_rules)
        }

# Global server instance
trading_server = TradingServer()
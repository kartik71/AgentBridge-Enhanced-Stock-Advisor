"""
FastAPI TradingServer - Mock Trading Actions API
Handles simulated buying/selling actions with order management and portfolio tracking
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Enums for order management
class OrderStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL = "partial"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

# Pydantic models
class OrderRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    symbol: str = Field(..., description="Stock symbol")
    side: OrderSide = Field(..., description="Order side: buy or sell")
    quantity: int = Field(..., ge=1, description="Number of shares")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    price: Optional[float] = Field(default=None, description="Limit price (for limit orders)")
    stop_price: Optional[float] = Field(default=None, description="Stop price (for stop orders)")
    time_in_force: str = Field(default="DAY", description="Time in force: DAY, GTC, IOC")

class Order(BaseModel):
    order_id: str
    user_id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    executed_quantity: int = 0
    executed_price: Optional[float] = None
    remaining_quantity: int
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None
    commission: float = 0.0
    paper_trading: bool = True

class Position(BaseModel):
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    day_change: float
    day_change_percent: float
    sector: Optional[str] = None

class Portfolio(BaseModel):
    user_id: str
    cash_balance: float
    total_market_value: float
    total_portfolio_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    day_change: float
    day_change_percent: float
    positions: List[Position]
    buying_power: float
    margin_used: float = 0.0

# Initialize FastAPI app
app = FastAPI(
    title="TradingServer API",
    description="Mock Trading Actions and Portfolio Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trading engine and data storage
class TradingEngine:
    def __init__(self):
        self.orders = {}  # order_id -> Order
        self.portfolios = {}  # user_id -> Portfolio
        self.market_data = {}  # symbol -> price data
        self.trade_history = {}  # user_id -> List[trades]
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Trading configuration
        self.commission_rate = 0.0  # $0 commission for demo
        self.paper_trading = True
        self.market_hours = {"open": "09:30", "close": "16:00"}
        
    async def initialize(self):
        """Initialize trading engine"""
        await self.load_market_data()
        await self.initialize_demo_portfolios()
        await self.load_trading_data()
        
    async def load_market_data(self):
        """Load current market prices"""
        self.market_data = {
            "AAPL": {"price": 192.35, "change": 2.45, "change_percent": 1.29},
            "MSFT": {"price": 398.75, "change": 5.20, "change_percent": 1.32},
            "GOOGL": {"price": 142.50, "change": -1.25, "change_percent": -0.87},
            "NVDA": {"price": 465.20, "change": 12.80, "change_percent": 2.83},
            "TSLA": {"price": 198.50, "change": -3.75, "change_percent": -1.85},
            "JNJ": {"price": 165.20, "change": 0.85, "change_percent": 0.52},
            "PFE": {"price": 28.90, "change": -0.45, "change_percent": -1.53},
            "JPM": {"price": 168.45, "change": 2.15, "change_percent": 1.29},
            "BAC": {"price": 32.15, "change": 0.75, "change_percent": 2.39},
            "KO": {"price": 58.75, "change": -0.25, "change_percent": -0.42}
        }
        
    async def initialize_demo_portfolios(self):
        """Initialize demo portfolios for testing"""
        demo_positions = [
            Position(
                symbol="AAPL",
                shares=50,
                avg_cost=180.00,
                current_price=192.35,
                market_value=9617.50,
                unrealized_pnl=617.50,
                unrealized_pnl_percent=6.85,
                day_change=122.50,
                day_change_percent=1.29,
                sector="Technology"
            ),
            Position(
                symbol="MSFT",
                shares=25,
                avg_cost=380.00,
                current_price=398.75,
                market_value=9968.75,
                unrealized_pnl=468.75,
                unrealized_pnl_percent=4.93,
                day_change=130.00,
                day_change_percent=1.32,
                sector="Technology"
            ),
            Position(
                symbol="JNJ",
                shares=75,
                avg_cost=160.00,
                current_price=165.20,
                market_value=12390.00,
                unrealized_pnl=390.00,
                unrealized_pnl_percent=3.25,
                day_change=63.75,
                day_change_percent=0.52,
                sector="Healthcare"
            )
        ]
        
        total_market_value = sum(pos.market_value for pos in demo_positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in demo_positions)
        day_change = sum(pos.day_change for pos in demo_positions)
        cash_balance = 18023.75
        
        demo_portfolio = Portfolio(
            user_id="demo_user",
            cash_balance=cash_balance,
            total_market_value=total_market_value,
            total_portfolio_value=total_market_value + cash_balance,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_percent=(total_unrealized_pnl / (total_market_value - total_unrealized_pnl)) * 100,
            day_change=day_change,
            day_change_percent=(day_change / (total_market_value - day_change)) * 100,
            positions=demo_positions,
            buying_power=cash_balance * 2,  # 2:1 margin
            margin_used=0.0
        )
        
        self.portfolios["demo_user"] = demo_portfolio
        
    async def load_trading_data(self):
        """Load existing trading data from storage"""
        try:
            # Load orders
            orders_file = self.data_dir / "orders.json"
            if orders_file.exists():
                with open(orders_file, 'r') as f:
                    orders_data = json.load(f)
                    for order_id, order_dict in orders_data.items():
                        order_dict['created_at'] = datetime.fromisoformat(order_dict['created_at'])
                        order_dict['updated_at'] = datetime.fromisoformat(order_dict['updated_at'])
                        if order_dict.get('executed_at'):
                            order_dict['executed_at'] = datetime.fromisoformat(order_dict['executed_at'])
                        self.orders[order_id] = Order(**order_dict)
            
            # Load trade history
            history_file = self.data_dir / "trade_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.trade_history = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load trading data: {e}")
    
    async def save_trading_data(self):
        """Save trading data to storage"""
        try:
            # Save orders
            orders_data = {}
            for order_id, order in self.orders.items():
                order_dict = order.dict()
                order_dict['created_at'] = order_dict['created_at'].isoformat()
                order_dict['updated_at'] = order_dict['updated_at'].isoformat()
                if order_dict.get('executed_at'):
                    order_dict['executed_at'] = order_dict['executed_at'].isoformat()
                orders_data[order_id] = order_dict
            
            with open(self.data_dir / "orders.json", 'w') as f:
                json.dump(orders_data, f, indent=2)
            
            # Save trade history
            with open(self.data_dir / "trade_history.json", 'w') as f:
                json.dump(self.trade_history, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save trading data: {e}")
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol"""
        if symbol in self.market_data:
            return self.market_data[symbol]["price"]
        else:
            # Generate random price for unknown symbols
            return round(random.uniform(50, 500), 2)
    
    async def validate_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Validate order against trading rules and account balance"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if user has portfolio
        if order_request.user_id not in self.portfolios:
            await self.create_user_portfolio(order_request.user_id)
        
        portfolio = self.portfolios[order_request.user_id]
        current_price = await self.get_current_price(order_request.symbol)
        
        # Calculate order value
        if order_request.order_type == OrderType.MARKET:
            order_value = order_request.quantity * current_price
        else:
            order_value = order_request.quantity * (order_request.price or current_price)
        
        # Check buying power for buy orders
        if order_request.side == OrderSide.BUY:
            if order_value > portfolio.buying_power:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Insufficient buying power. Required: ${order_value:,.2f}, Available: ${portfolio.buying_power:,.2f}"
                )
        
        # Check position for sell orders
        elif order_request.side == OrderSide.SELL:
            position = next((pos for pos in portfolio.positions if pos.symbol == order_request.symbol), None)
            if not position or position.shares < order_request.quantity:
                available_shares = position.shares if position else 0
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Insufficient shares. Required: {order_request.quantity}, Available: {available_shares}"
                )
        
        # Check market hours (warning only)
        current_time = datetime.now().time()
        market_open = datetime.strptime(self.market_hours["open"], "%H:%M").time()
        market_close = datetime.strptime(self.market_hours["close"], "%H:%M").time()
        
        if not (market_open <= current_time <= market_close):
            validation_result["warnings"].append("Order placed outside regular market hours")
        
        # Paper trading warning
        validation_result["warnings"].append("Paper trading mode - no real money involved")
        
        return validation_result
    
    async def create_user_portfolio(self, user_id: str):
        """Create new user portfolio with starting cash"""
        new_portfolio = Portfolio(
            user_id=user_id,
            cash_balance=100000.0,  # $100k starting cash
            total_market_value=0.0,
            total_portfolio_value=100000.0,
            total_unrealized_pnl=0.0,
            total_unrealized_pnl_percent=0.0,
            day_change=0.0,
            day_change_percent=0.0,
            positions=[],
            buying_power=200000.0,  # 2:1 margin
            margin_used=0.0
        )
        
        self.portfolios[user_id] = new_portfolio
    
    async def submit_order(self, order_request: OrderRequest) -> Order:
        """Submit and process trading order"""
        # Validate order
        validation = await self.validate_order(order_request)
        
        order_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Create order
        order = Order(
            order_id=order_id,
            user_id=order_request.user_id,
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=order_request.quantity,
            order_type=order_request.order_type,
            price=order_request.price,
            stop_price=order_request.stop_price,
            status=OrderStatus.PENDING,
            remaining_quantity=order_request.quantity,
            created_at=current_time,
            updated_at=current_time,
            commission=self.commission_rate,
            paper_trading=self.paper_trading
        )
        
        if not validation["valid"]:
            order.status = OrderStatus.REJECTED
            self.orders[order_id] = order
            return order
        
        # Execute order immediately (market simulation)
        await self.execute_order(order)
        
        # Save order
        self.orders[order_id] = order
        await self.save_trading_data()
        
        return order
    
    async def execute_order(self, order: Order):
        """Execute order and update portfolio"""
        current_price = await self.get_current_price(order.symbol)
        
        # Simulate execution
        order.executed_quantity = order.quantity
        order.executed_price = current_price
        order.remaining_quantity = 0
        order.status = OrderStatus.EXECUTED
        order.executed_at = datetime.now()
        order.updated_at = datetime.now()
        
        # Update portfolio
        await self.update_portfolio(order)
        
        # Record trade in history
        await self.record_trade(order)
    
    async def update_portfolio(self, order: Order):
        """Update portfolio after order execution"""
        portfolio = self.portfolios[order.user_id]
        
        # Find existing position
        position = next((pos for pos in portfolio.positions if pos.symbol == order.symbol), None)
        
        if order.side == OrderSide.BUY:
            # Buy order
            order_value = order.executed_quantity * order.executed_price
            
            if position:
                # Update existing position
                total_cost = (position.shares * position.avg_cost) + order_value
                total_shares = position.shares + order.executed_quantity
                position.avg_cost = total_cost / total_shares
                position.shares = total_shares
            else:
                # Create new position
                position = Position(
                    symbol=order.symbol,
                    shares=order.executed_quantity,
                    avg_cost=order.executed_price,
                    current_price=order.executed_price,
                    market_value=order_value,
                    unrealized_pnl=0.0,
                    unrealized_pnl_percent=0.0,
                    day_change=0.0,
                    day_change_percent=0.0,
                    sector=self.get_sector(order.symbol)
                )
                portfolio.positions.append(position)
            
            # Update cash balance
            portfolio.cash_balance -= order_value + order.commission
            
        else:
            # Sell order
            if position:
                order_value = order.executed_quantity * order.executed_price
                position.shares -= order.executed_quantity
                
                # Remove position if fully sold
                if position.shares <= 0:
                    portfolio.positions.remove(position)
                
                # Update cash balance
                portfolio.cash_balance += order_value - order.commission
        
        # Recalculate portfolio metrics
        await self.recalculate_portfolio_metrics(portfolio)
    
    async def recalculate_portfolio_metrics(self, portfolio: Portfolio):
        """Recalculate portfolio-level metrics"""
        total_market_value = 0
        total_unrealized_pnl = 0
        total_day_change = 0
        
        for position in portfolio.positions:
            # Update current price
            current_price = await self.get_current_price(position.symbol)
            position.current_price = current_price
            position.market_value = position.shares * current_price
            position.unrealized_pnl = (current_price - position.avg_cost) * position.shares
            position.unrealized_pnl_percent = (position.unrealized_pnl / (position.avg_cost * position.shares)) * 100
            
            # Day change (mock calculation)
            day_change_per_share = self.market_data.get(position.symbol, {}).get("change", 0)
            position.day_change = day_change_per_share * position.shares
            position.day_change_percent = self.market_data.get(position.symbol, {}).get("change_percent", 0)
            
            total_market_value += position.market_value
            total_unrealized_pnl += position.unrealized_pnl
            total_day_change += position.day_change
        
        # Update portfolio totals
        portfolio.total_market_value = total_market_value
        portfolio.total_portfolio_value = total_market_value + portfolio.cash_balance
        portfolio.total_unrealized_pnl = total_unrealized_pnl
        portfolio.total_unrealized_pnl_percent = (total_unrealized_pnl / (total_market_value - total_unrealized_pnl)) * 100 if total_market_value > total_unrealized_pnl else 0
        portfolio.day_change = total_day_change
        portfolio.day_change_percent = (total_day_change / (total_market_value - total_day_change)) * 100 if total_market_value > total_day_change else 0
        portfolio.buying_power = portfolio.cash_balance * 2  # 2:1 margin
    
    def get_sector(self, symbol: str) -> str:
        """Get sector for symbol (simplified mapping)"""
        sector_map = {
            "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "NVDA": "Technology",
            "TSLA": "Automotive", "JNJ": "Healthcare", "PFE": "Healthcare",
            "JPM": "Finance", "BAC": "Finance", "KO": "Consumer Staples"
        }
        return sector_map.get(symbol, "Unknown")
    
    async def record_trade(self, order: Order):
        """Record executed trade in history"""
        if order.user_id not in self.trade_history:
            self.trade_history[order.user_id] = []
        
        trade_record = {
            "trade_id": str(uuid.uuid4()),
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.executed_quantity,
            "price": order.executed_price,
            "value": order.executed_quantity * order.executed_price,
            "commission": order.commission,
            "executed_at": order.executed_at.isoformat(),
            "paper_trading": order.paper_trading
        }
        
        self.trade_history[order.user_id].append(trade_record)

# Initialize trading engine
trading_engine = TradingEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize trading engine on startup"""
    await trading_engine.initialize()
    print("🚀 TradingServer API started successfully")
    print("📊 Paper trading mode enabled")

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TradingServer API",
        "version": "1.0.0",
        "description": "Mock Trading Actions and Portfolio Management",
        "endpoints": {
            "submit_order": "/submit_order",
            "portfolio": "/portfolio/{user_id}",
            "orders": "/orders/{user_id}",
            "trade_history": "/trade_history/{user_id}",
            "market_data": "/market_data",
            "health": "/health"
        },
        "status": "operational",
        "paper_trading": trading_engine.paper_trading,
        "total_orders": len(trading_engine.orders),
        "active_portfolios": len(trading_engine.portfolios)
    }

@app.post("/submit_order")
async def submit_order(order_request: OrderRequest):
    """
    Submit a trading order
    
    Args:
        order_request: Order details including symbol, side, quantity, etc.
    
    Returns:
        Order confirmation with execution details
    """
    try:
        order = await trading_engine.submit_order(order_request)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "order": order.dict(),
                "message": f"Order {order.status.value} successfully",
                "paper_trading": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting order: {str(e)}")

@app.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    """Get user portfolio with positions and metrics"""
    if user_id not in trading_engine.portfolios:
        await trading_engine.create_user_portfolio(user_id)
    
    portfolio = trading_engine.portfolios[user_id]
    await trading_engine.recalculate_portfolio_metrics(portfolio)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "portfolio": portfolio.dict(),
            "paper_trading": True,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/orders/{user_id}")
async def get_orders(
    user_id: str,
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    limit: int = Query(50, ge=1, le=200, description="Number of orders to return")
):
    """Get user's order history"""
    user_orders = [
        order for order in trading_engine.orders.values()
        if order.user_id == user_id
    ]
    
    # Filter by status if specified
    if status:
        user_orders = [order for order in user_orders if order.status == status]
    
    # Sort by creation date (most recent first)
    user_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply limit
    user_orders = user_orders[:limit]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "orders": [order.dict() for order in user_orders],
            "total_orders": len(user_orders),
            "paper_trading": True,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/trade_history/{user_id}")
async def get_trade_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of trades to return")
):
    """Get user's trade execution history"""
    trades = trading_engine.trade_history.get(user_id, [])
    
    # Sort by execution date (most recent first)
    trades.sort(key=lambda x: x["executed_at"], reverse=True)
    
    # Apply limit
    trades = trades[:limit]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "trades": trades,
            "total_trades": len(trades),
            "paper_trading": True,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/market_data")
async def get_market_data():
    """Get current market data for all tracked symbols"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "market_data": trading_engine.market_data,
            "symbols_count": len(trading_engine.market_data),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/market_data/{symbol}")
async def get_symbol_data(symbol: str):
    """Get market data for specific symbol"""
    symbol = symbol.upper()
    
    if symbol not in trading_engine.market_data:
        # Generate mock data for unknown symbols
        price = round(random.uniform(50, 500), 2)
        change = round(random.uniform(-10, 10), 2)
        change_percent = round((change / price) * 100, 2)
        
        data = {
            "price": price,
            "change": change,
            "change_percent": change_percent
        }
    else:
        data = trading_engine.market_data[symbol]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel a pending order"""
    if order_id not in trading_engine.orders:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    
    order = trading_engine.orders[order_id]
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order with status '{order.status}'")
    
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.now()
    
    await trading_engine.save_trading_data()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Order {order_id} cancelled successfully",
            "order": order.dict(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TradingServer API",
        "version": "1.0.0",
        "uptime": datetime.now().isoformat(),
        "trading_status": {
            "paper_trading": trading_engine.paper_trading,
            "total_orders": len(trading_engine.orders),
            "active_portfolios": len(trading_engine.portfolios),
            "market_data_symbols": len(trading_engine.market_data)
        }
    }

# Run server
if __name__ == "__main__":
    print("🚀 Starting TradingServer API...")
    print("📊 Paper trading mode enabled...")
    
    uvicorn.run(
        "trading_server:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
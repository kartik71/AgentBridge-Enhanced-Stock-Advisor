# PortfolioOptimizerReActAgent

A sophisticated LangGraph ReAct agent for portfolio optimization that combines reasoning traces, Modern Portfolio Theory, and human-in-the-loop approval for intelligent investment decisions.

## 🎯 Features

### ReAct Pattern Implementation
- **Explicit Reasoning Traces**: Step-by-step thought process documentation
- **Action-Observation Cycles**: Structured decision-making workflow
- **Error Recovery**: Robust handling of failures with fallback strategies

### Portfolio Optimization
- **Modern Portfolio Theory**: Risk-adjusted allocation optimization
- **Multi-Factor Analysis**: Considers confidence, risk, sector diversification
- **Dynamic Allocation**: Adapts to user risk tolerance and market conditions

### Human-in-the-Loop (HITL)
- **Risk-Based Triggers**: Automatic HITL for high-risk portfolios
- **Approval Workflow**: Structured human review process
- **Override Capabilities**: Human can reject and request re-optimization

### Comprehensive Audit Trail
- **JSON Logging**: Detailed decision records with full context
- **CSV Export**: Structured data for analysis and reporting
- **Compliance Ready**: Maintains regulatory audit requirements

## 🏗️ Architecture

### StateGraph Workflow

```
analyze_inputs → fetch_market_data → reason_about_strategy → generate_recommendations
                                                                        ↓
finalize_portfolio ← [HITL Review] ← optimize_portfolio
        ↓
log_decision → END
```

### Key Components

1. **Input Analysis**: Validates budget, timeframe, and risk parameters
2. **Market Data Fetching**: Retrieves real-time data from MCP servers
3. **Strategy Reasoning**: Applies ReAct pattern for investment strategy
4. **Recommendation Generation**: Gets stock picks from AI recommendation engine
5. **Portfolio Optimization**: Applies MPT for optimal allocation
6. **HITL Review**: Human approval for high-risk scenarios
7. **Decision Logging**: Comprehensive audit trail creation

## 🚀 Usage

### Basic Portfolio Optimization

```python
from agents.portfolio_optimizer_react.agent import PortfolioOptimizerReActAgent

agent = PortfolioOptimizerReActAgent()

result = await agent.optimize_portfolio(
    budget=50000,
    timeframe="Medium",  # Short, Medium, Long
    risk_level="Medium", # Low, Medium, High
    hitl_enabled=True
)

print(f"Portfolio: {result['portfolio']}")
print(f"Reasoning: {result['reasoning_trace']}")
```

### HITL Approval Workflow

The agent automatically triggers HITL approval when:
- Risk score > 2.5/3.0
- Budget > $100,000
- Diversification score < 60%

```python
# High-risk portfolio requiring approval
result = await agent.optimize_portfolio(
    budget=150000,      # Large budget triggers HITL
    timeframe="Short",  # Short-term adds risk
    risk_level="High"   # High risk tolerance
)

if result['hitl_required']:
    print("Human approval required!")
    print(f"Approved: {result['hitl_approved']}")
```

## 📊 Reasoning Trace Example

```
🔍 ANALYZE: Received optimization request with budget=$50,000, timeframe=Medium, risk_level=Medium ✅ Input validation complete

📊 FETCH: Retrieving current market data and indices... ✅ Retrieved 3 market indices 📈 Market sentiment: Fear/Greed Index = 65

🧠 REASON: Analyzing market conditions and developing investment strategy... ⚖️ Market sentiment NEUTRAL - balanced approach recommended ⚖️ MEDIUM RISK profile: Balanced mix of growth and value 📊 MEDIUM-TERM horizon: Balance momentum and fundamentals ✅ Strategy analysis complete

🎯 GENERATE: Creating stock recommendations based on strategy... ✅ Generated 6 stock recommendations 📊 #1: AAPL - BUY (confidence: 87%) 📊 #2: MSFT - BUY (confidence: 83%) 📊 #3: JNJ - BUY (confidence: 81%)

⚖️ OPTIMIZE: Applying portfolio optimization algorithms... 🎯 Optimizing allocation for 5 positions ✅ Portfolio optimized: 5 positions 💰 Total investment: $49,750.00 📈 Expected return: 12.3%

✅ FINALIZE: Portfolio optimization complete 📊 Final Portfolio Summary: - Positions: 5 - Total Investment: $49,750.00 - Expected Return: 12.3% - Risk Score: 2.1/3.0 - Diversification: 80%

📝 LOG: Recording decision to audit trail ✅ Decision logged to audit trail
```

## 📁 Audit Logging

### JSON Audit Log
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "agent_id": "portfolio_optimizer_react",
  "session_id": "session_20240115_143000",
  "inputs": {
    "budget": 50000,
    "timeframe": "Medium",
    "risk_level": "Medium"
  },
  "reasoning_trace": ["🔍 ANALYZE: ...", "📊 FETCH: ..."],
  "final_portfolio": {
    "positions": [...],
    "total_investment": 49750.00,
    "expected_return": 12.3,
    "risk_score": 2.1
  },
  "hitl_required": false,
  "performance_metrics": {
    "processing_time": 4.0,
    "confidence_score": 84.2
  }
}
```

### CSV Decision Log
| timestamp | budget | timeframe | risk_level | num_positions | expected_return | hitl_required |
|-----------|--------|-----------|------------|---------------|-----------------|---------------|
| 2024-01-15T14:30:00Z | 50000 | Medium | Medium | 5 | 12.3 | false |

## 🔧 Configuration

### HITL Criteria
```python
hitl_criteria = {
    "high_risk_threshold": 2.5,      # Risk score trigger
    "large_budget_threshold": 100000, # Budget trigger
    "min_diversification_score": 60   # Diversification trigger
}
```

### Portfolio Constraints
```python
constraints = {
    "max_positions": 5,        # Maximum number of stocks
    "min_allocation": 0.05,    # 5% minimum per position
    "max_allocation": 0.30     # 30% maximum per position
}
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/test_portfolio_optimizer_react.py -v
```

Run examples:
```bash
python examples/portfolio_optimizer_react_example.py
```

## 📈 Performance Metrics

The agent tracks:
- **Processing Time**: End-to-end optimization duration
- **Confidence Score**: Average confidence across recommendations
- **Success Rate**: Percentage of successful optimizations
- **HITL Approval Rate**: Human approval percentage
- **Portfolio Quality**: Risk-adjusted return metrics

## 🔌 MCP Server Integration

Integrates with:
- **RecommendationServer**: AI-powered stock recommendations
- **IndexServer**: Real-time market data and sentiment
- **TradingServer**: Portfolio position tracking (optional)

## 📋 Requirements

- Python 3.11+
- LangGraph 0.1.0+
- LangChain 0.1.0+
- AsyncIO support
- MCP servers (optional, falls back to mock data)

## 🎯 Use Cases

1. **Robo-Advisor Platforms**: Automated portfolio management
2. **Wealth Management**: Human-supervised optimization
3. **Research & Backtesting**: Strategy development and testing
4. **Compliance Monitoring**: Audit trail for regulatory requirements
5. **Educational Tools**: Demonstrating portfolio theory concepts

## 🔮 Future Enhancements

- [ ] Multi-objective optimization (return, risk, ESG)
- [ ] Real-time rebalancing triggers
- [ ] Advanced risk models (VaR, CVaR)
- [ ] Integration with live trading APIs
- [ ] Machine learning-enhanced reasoning
- [ ] Custom constraint support

---

Built with ❤️ using LangGraph and the ReAct pattern for transparent, auditable AI decision-making.
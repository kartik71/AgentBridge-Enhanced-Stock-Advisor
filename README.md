# Stock Advisor Application

A comprehensive multi-agent stock analysis and portfolio optimization system built with LangGraph, MCP servers, and modern web technologies.

## 🏗️ Architecture

```
stock_advisor_app/
├── agents/                    # LangGraph Agents
│   ├── index_scraper/        # Market data collection
│   ├── portfolio_optimizer/  # Portfolio optimization using MPT
│   ├── timing_advisor/       # Market timing analysis
│   └── compliance_checker/   # Regulatory compliance
├── mcp_servers/              # Model Context Protocol Servers
│   ├── index_server.py       # Market index data provider
│   ├── recommendation_server.py # Portfolio recommendations
│   ├── trading_server.py     # Trade execution & compliance
│   └── __init__.py
├── data/                     # Data storage
│   ├── synthetic_index_data.csv
│   └── user_profiles.json
├── app/                      # React Frontend
│   ├── components/           # AG-UI widgets
│   ├── pages/               # Dashboard & Settings
│   └── App.jsx
└── deployment/              # CI/CD and deployment configs
```

## 🚀 Features

### Multi-Agent System
- **Index Scraper Agent**: Real-time market data collection from multiple sources
- **Portfolio Optimizer Agent**: Modern Portfolio Theory-based optimization
- **Timing Advisor Agent**: Technical and fundamental market timing analysis
- **Compliance Checker Agent**: Regulatory compliance and risk management

### MCP Server Integration
- **Index Server**: Provides market index data and historical analysis
- **Recommendation Server**: AI-powered portfolio recommendations
- **Trading Server**: Trade execution with compliance checking

### Advanced Dashboard
- Real-time market ticker with major indices
- Interactive portfolio recommendations with confidence scores
- Agent status monitoring and performance metrics
- A2A (Agent-to-Agent) communication controls
- Risk management and compliance monitoring

## 🛠️ Technology Stack

### Backend
- **LangGraph**: Multi-agent orchestration framework
- **Python 3.11+**: Core backend language
- **MCP Protocol**: Model Context Protocol for agent communication
- **FastAPI**: High-performance API framework
- **AsyncIO**: Asynchronous programming for real-time data

### Frontend
- **React 18**: Modern UI framework
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icon library
- **AG-UI Components**: Custom component library

### Data & APIs
- **Alpha Vantage**: Market data provider
- **Yahoo Finance**: Backup data source
- **Synthetic Data**: Demo data for development
- **Real-time WebSocket**: Live market updates

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock_advisor_app
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Start the development servers**
   ```bash
   # Terminal 1: Start MCP servers
   python -m mcp_servers

   # Terminal 2: Start frontend
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:5173
   - API Documentation: http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
YAHOO_FINANCE_API_KEY=your_key_here

# LangChain Configuration
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=stock-advisor

# Risk Management
MAX_POSITION_SIZE=0.10
MAX_DAILY_LOSS=0.05
STOP_LOSS_THRESHOLD=0.03
```

### Agent Configuration
Agents can be configured through the settings panel or by modifying their respective configuration files.

## 🤖 Agent Details

### Index Scraper Agent
- **Purpose**: Collects real-time market index data
- **Data Sources**: Alpha Vantage, Yahoo Finance, IEX Cloud
- **Update Frequency**: 30 seconds (configurable)
- **Output**: Market indices with price, volume, and change data

### Portfolio Optimizer Agent
- **Purpose**: Optimizes portfolio allocation using Modern Portfolio Theory
- **Methods**: Mean-variance optimization, risk-adjusted returns
- **Inputs**: User risk profile, market data, constraints
- **Output**: Optimized asset allocation with expected returns

### Timing Advisor Agent
- **Purpose**: Provides market timing recommendations
- **Analysis**: Technical indicators, market regime detection
- **Signals**: Buy/Sell/Hold recommendations with confidence scores
- **Timeframes**: Short-term, medium-term, long-term strategies

### Compliance Checker Agent
- **Purpose**: Ensures regulatory compliance for all trades
- **Rules**: Position limits, risk controls, regulatory requirements
- **Monitoring**: Real-time compliance checking and reporting
- **Output**: Compliance score and violation alerts

## 🔄 Agent Communication (A2A)

The system supports Agent-to-Agent communication through configurable connections:

- **Index Scraper → Portfolio Optimizer**: Market data flow
- **Portfolio Optimizer → Timing Advisor**: Optimization results
- **Timing Advisor → Compliance Checker**: Timing recommendations
- **Compliance Checker → Portfolio Optimizer**: Compliance feedback

## 📊 Dashboard Features

### Real-time Market Ticker
- Live updates of major market indices
- Color-coded price changes and trends
- Smooth scrolling animation

### Portfolio Recommendations
- AI-generated stock recommendations
- Confidence scores and risk assessments
- Target prices and potential returns
- Sector diversification analysis

### Agent Management
- Real-time agent status monitoring
- Performance metrics and error tracking
- MCP server connection status
- Agent activation/deactivation controls

### System Configuration
- Risk management parameters
- Data source configuration
- Notification settings
- Compliance rule management

## 🚀 Deployment

### Docker Deployment
```bash
# Build the Docker image
docker build -t stock-advisor .

# Run the container
docker run -p 8000:8000 -p 5173:5173 stock-advisor
```

### Azure Deployment
The application includes Azure CI/CD pipeline configuration:

```bash
# Deploy to Azure App Service
az webapp up --name stock-advisor-app --resource-group stock-advisor-rg
```

### Environment-specific Configurations
- **Development**: Hot reload, debug logging, paper trading
- **Staging**: Production-like environment for testing
- **Production**: Optimized builds, real trading, monitoring

## 🔒 Security & Compliance

### Security Features
- API key encryption and secure storage
- JWT-based authentication
- Rate limiting and request validation
- Audit logging for all transactions

### Compliance Features
- Real-time regulatory compliance checking
- Position and risk limit enforcement
- Trade surveillance and reporting
- SOX and FINRA compliance frameworks

## 📈 Performance & Monitoring

### Metrics Tracked
- Agent performance and response times
- Portfolio optimization accuracy
- Compliance violation rates
- System uptime and reliability

### Monitoring Tools
- Real-time dashboard metrics
- Error tracking and alerting
- Performance analytics
- User activity monitoring

## 🧪 Testing

### Running Tests
```bash
# Python tests
pytest tests/

# Frontend tests
npm test

# Integration tests
npm run test:integration
```

### Test Coverage
- Unit tests for all agents and MCP servers
- Integration tests for agent communication
- End-to-end tests for critical user flows
- Performance and load testing

## 📚 API Documentation

### MCP Server APIs
- **Index Server**: `/api/v1/indices/*`
- **Recommendation Server**: `/api/v1/recommendations/*`
- **Trading Server**: `/api/v1/trading/*`

### Agent APIs
- **Agent Status**: `/api/v1/agents/status`
- **Agent Control**: `/api/v1/agents/control`
- **Performance Metrics**: `/api/v1/agents/metrics`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team

## 🔮 Roadmap

### Upcoming Features
- [ ] Machine learning-based market prediction
- [ ] Social sentiment analysis integration
- [ ] Advanced options trading strategies
- [ ] Mobile application
- [ ] Multi-broker integration
- [ ] Advanced backtesting framework

### Version History
- **v1.0.0**: Initial release with core agent system
- **v1.1.0**: Enhanced compliance and risk management
- **v1.2.0**: Advanced portfolio optimization algorithms
- **v2.0.0**: Machine learning integration (planned)

---

Built with ❤️ by the Stock Advisor Team
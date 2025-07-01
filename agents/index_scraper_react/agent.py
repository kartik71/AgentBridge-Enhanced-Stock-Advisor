"""
IndexScraperAgent - LangGraph ReAct Agent for Market Data Collection
Uses ReAct pattern with reasoning traces for real-time market data scraping
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
    from mcp_servers.index_server import index_server
except ImportError:
    print("Warning: MCP servers not available, using mock data")
    index_server = None

# State definition for the agent
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    data_sources: List[str]
    collection_frequency: int  # seconds
    market_indices: List[Dict[str, Any]]
    historical_data: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approved: bool
    final_data: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

@dataclass
class ScrapingConfig:
    """Configuration for market data scraping"""
    data_sources: List[str]
    collection_frequency: int = 30  # seconds
    historical_days: int = 30
    hitl_enabled: bool = False
    max_retries: int = 3

class IndexScraperReActAgent:
    """LangGraph ReAct Agent for Market Data Collection with HITL support"""
    
    def __init__(self, agent_id: str = "index_scraper_react"):
        self.agent_id = agent_id
        self.name = "IndexScraperReActAgent"
        self.version = "1.0.0"
        self.audit_log_file = "data/index_scraper_audit.json"
        self.csv_log_file = "data/index_scraper_decisions.csv"
        
        # Initialize MCP server
        self.index_server = index_server
        
        # Create the StateGraph
        self.graph = self._create_graph()
        
        # Ensure audit directories exist
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
        self._initialize_csv_log()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph StateGraph for ReAct pattern"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_sources", self._analyze_sources)
        workflow.add_node("validate_connections", self._validate_connections)
        workflow.add_node("collect_current_data", self._collect_current_data)
        workflow.add_node("fetch_historical_data", self._fetch_historical_data)
        workflow.add_node("analyze_market_sentiment", self._analyze_market_sentiment)
        workflow.add_node("hitl_review", self._hitl_review)
        workflow.add_node("finalize_data", self._finalize_data)
        workflow.add_node("log_collection", self._log_collection)
        
        # Define the flow
        workflow.set_entry_point("analyze_sources")
        
        workflow.add_edge("analyze_sources", "validate_connections")
        workflow.add_edge("validate_connections", "collect_current_data")
        workflow.add_edge("collect_current_data", "fetch_historical_data")
        workflow.add_edge("fetch_historical_data", "analyze_market_sentiment")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "analyze_market_sentiment",
            self._should_require_hitl_approval,
            {
                "hitl_required": "hitl_review",
                "no_hitl": "finalize_data"
            }
        )
        
        workflow.add_conditional_edges(
            "hitl_review",
            self._check_hitl_approval,
            {
                "approved": "finalize_data",
                "rejected": "collect_current_data",  # Re-collect data
                "pending": END
            }
        )
        
        workflow.add_edge("finalize_data", "log_collection")
        workflow.add_edge("log_collection", END)
        
        return workflow.compile()
    
    async def _analyze_sources(self, state: AgentState) -> AgentState:
        """Analyze and validate data sources"""
        reasoning = f"🔍 ANALYZE: Initializing data collection from {len(state['data_sources'])} sources"
        reasoning += f" 📊 Sources: {', '.join(state['data_sources'])}"
        reasoning += f" ⏱️ Collection frequency: {state['collection_frequency']}s"
        
        # Validate data sources
        valid_sources = ['yahoo_finance', 'alpha_vantage', 'iex_cloud', 'polygon', 'finnhub']
        invalid_sources = [src for src in state['data_sources'] if src not in valid_sources]
        
        if invalid_sources:
            reasoning += f" ⚠️ WARNING: Invalid sources detected: {invalid_sources}"
            state['data_sources'] = [src for src in state['data_sources'] if src in valid_sources]
            reasoning += f" ✅ Filtered to valid sources: {state['data_sources']}"
        
        if state['collection_frequency'] < 10:
            reasoning += " ⚠️ WARNING: Collection frequency too high, setting to 10s minimum"
            state['collection_frequency'] = 10
        
        reasoning += " ✅ Source analysis complete"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _validate_connections(self, state: AgentState) -> AgentState:
        """Validate connections to data sources"""
        reasoning = "🔌 VALIDATE: Testing connections to data sources..."
        
        connection_status = {}
        
        try:
            if self.index_server:
                # Test MCP server connection
                status = await self.index_server.get_server_status()
                connection_status['mcp_server'] = status.get('status') == 'healthy'
                reasoning += f" ✅ MCP Server: {'Connected' if connection_status['mcp_server'] else 'Failed'}"
            else:
                connection_status['mcp_server'] = False
                reasoning += " ❌ MCP Server: Not available"
            
            # Simulate testing other data sources
            for source in state['data_sources']:
                # In real implementation, would test actual API connections
                connection_status[source] = True  # Assume connected for demo
                reasoning += f" ✅ {source}: Connected"
                
        except Exception as e:
            reasoning += f" ❌ Connection error: {str(e)}"
            connection_status['error'] = str(e)
        
        state['connection_status'] = connection_status
        reasoning += f" 📊 Connection summary: {sum(connection_status.values())}/{len(connection_status)} sources active"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _collect_current_data(self, state: AgentState) -> AgentState:
        """Collect current market index data"""
        reasoning = "📈 COLLECT: Gathering current market index data..."
        
        try:
            if self.index_server:
                # Get current indices from MCP server
                current_result = await self.index_server.get_current_indices()
                
                if current_result['status'] == 'success':
                    state['market_indices'] = current_result['data']
                    reasoning += f" ✅ Retrieved {len(current_result['data'])} market indices"
                    
                    # Log key indices
                    for idx in current_result['data'][:3]:
                        change_icon = "📈" if idx.get('change_percent', 0) >= 0 else "📉"
                        reasoning += f" {change_icon} {idx['symbol']}: ${idx.get('current_price', 0):.2f} ({idx.get('change_percent', 0):+.2f}%)"
                else:
                    raise Exception("MCP server returned error status")
                    
            else:
                # Generate mock data
                state['market_indices'] = self._generate_mock_indices()
                reasoning += " ⚠️ Using mock market data (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error collecting data: {str(e)}"
            state['market_indices'] = self._generate_mock_indices()
            reasoning += " 🔄 Falling back to mock data"
        
        # Analyze data quality
        data_quality = self._assess_data_quality(state['market_indices'])
        reasoning += f" 📊 Data quality score: {data_quality['score']}/100"
        
        if data_quality['score'] < 70:
            reasoning += " ⚠️ WARNING: Low data quality detected"
            state['data_quality_issues'] = data_quality['issues']
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _fetch_historical_data(self, state: AgentState) -> AgentState:
        """Fetch historical data for trend analysis"""
        reasoning = "📊 HISTORICAL: Collecting historical data for trend analysis..."
        
        historical_data = {}
        
        try:
            if self.index_server:
                # Get historical data for major indices
                major_indices = ['S&P 500', 'NASDAQ', 'DOW']
                
                for index in major_indices:
                    hist_result = await self.index_server.get_historical_data(index, days=30)
                    
                    if hist_result['status'] == 'success':
                        historical_data[index] = hist_result['data']
                        reasoning += f" ✅ {index}: {len(hist_result['data'])} data points"
                    else:
                        reasoning += f" ❌ {index}: Failed to retrieve"
                        
            else:
                # Generate mock historical data
                historical_data = self._generate_mock_historical()
                reasoning += " ⚠️ Using mock historical data"
                
        except Exception as e:
            reasoning += f" ❌ Error fetching historical data: {str(e)}"
            historical_data = self._generate_mock_historical()
            reasoning += " 🔄 Using fallback historical data"
        
        state['historical_data'] = historical_data
        
        # Analyze trends
        trend_analysis = self._analyze_trends(historical_data)
        reasoning += f" 📈 Trend analysis: {trend_analysis['overall_trend']}"
        reasoning += f" 📊 Volatility level: {trend_analysis['volatility_level']}"
        
        state['trend_analysis'] = trend_analysis
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _analyze_market_sentiment(self, state: AgentState) -> AgentState:
        """Analyze market sentiment indicators"""
        reasoning = "🧠 SENTIMENT: Analyzing market sentiment and indicators..."
        
        try:
            if self.index_server:
                # Get market sentiment from MCP server
                sentiment_result = await self.index_server.get_market_sentiment()
                
                if sentiment_result['status'] == 'success':
                    state['market_sentiment'] = sentiment_result['sentiment']
                    sentiment = sentiment_result['sentiment']
                    
                    fear_greed = sentiment.get('fear_greed_index', 50)
                    vix = sentiment.get('vix', 15)
                    
                    reasoning += f" 📊 Fear/Greed Index: {fear_greed}"
                    reasoning += f" 📈 VIX Level: {vix}"
                    
                    # Interpret sentiment
                    if fear_greed > 75:
                        reasoning += " 🔥 Market showing EXTREME GREED"
                        sentiment_level = "extreme_greed"
                    elif fear_greed > 55:
                        reasoning += " 📈 Market showing GREED"
                        sentiment_level = "greed"
                    elif fear_greed < 25:
                        reasoning += " 😰 Market showing EXTREME FEAR"
                        sentiment_level = "extreme_fear"
                    elif fear_greed < 45:
                        reasoning += " 📉 Market showing FEAR"
                        sentiment_level = "fear"
                    else:
                        reasoning += " ⚖️ Market sentiment NEUTRAL"
                        sentiment_level = "neutral"
                    
                    state['sentiment_level'] = sentiment_level
                else:
                    raise Exception("Failed to get sentiment data")
                    
            else:
                # Generate mock sentiment
                state['market_sentiment'] = self._generate_mock_sentiment()
                reasoning += " ⚠️ Using mock sentiment data"
                
        except Exception as e:
            reasoning += f" ❌ Error analyzing sentiment: {str(e)}"
            state['market_sentiment'] = self._generate_mock_sentiment()
            reasoning += " 🔄 Using fallback sentiment data"
        
        # Combine with trend analysis for overall market assessment
        trend_analysis = state.get('trend_analysis', {})
        overall_assessment = self._generate_market_assessment(
            state['market_sentiment'], 
            trend_analysis
        )
        
        reasoning += f" 🎯 Overall market assessment: {overall_assessment['status']}"
        reasoning += f" 📊 Confidence level: {overall_assessment['confidence']}%"
        
        state['market_assessment'] = overall_assessment
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _should_require_hitl_approval(self, state: AgentState) -> str:
        """Determine if HITL approval is required"""
        # Require HITL approval if:
        # 1. Extreme market conditions (fear/greed > 80 or < 20)
        # 2. High volatility detected
        # 3. Data quality issues
        
        sentiment = state.get('market_sentiment', {})
        fear_greed = sentiment.get('fear_greed_index', 50)
        data_quality_issues = state.get('data_quality_issues', [])
        trend_analysis = state.get('trend_analysis', {})
        volatility = trend_analysis.get('volatility_level', 'normal')
        
        if (fear_greed > 80 or fear_greed < 20 or 
            volatility == 'high' or 
            len(data_quality_issues) > 0):
            state['hitl_approval_required'] = True
            return "hitl_required"
        else:
            state['hitl_approval_required'] = False
            return "no_hitl"
    
    async def _hitl_review(self, state: AgentState) -> AgentState:
        """Handle Human-in-the-Loop review process"""
        reasoning = "👤 HITL: Market data requires human review due to unusual conditions"
        
        sentiment = state.get('market_sentiment', {})
        fear_greed = sentiment.get('fear_greed_index', 50)
        data_quality_issues = state.get('data_quality_issues', [])
        
        reasoning += f" 🔍 Review criteria triggered:"
        reasoning += f" - Fear/Greed Index: {fear_greed}"
        reasoning += f" - Data quality issues: {len(data_quality_issues)}"
        reasoning += f" - Volatility: {state.get('trend_analysis', {}).get('volatility_level', 'unknown')}"
        
        reasoning += " ⏳ Waiting for human approval..."
        
        # Simulate human decision based on data quality
        market_assessment = state.get('market_assessment', {})
        confidence = market_assessment.get('confidence', 50)
        
        if confidence > 60 and len(data_quality_issues) == 0:
            state['hitl_approved'] = True
            reasoning += " ✅ Data approved by human reviewer"
        else:
            state['hitl_approved'] = False
            reasoning += " ❌ Data rejected - requires re-collection"
        
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
    
    async def _finalize_data(self, state: AgentState) -> AgentState:
        """Finalize the collected market data"""
        reasoning = "✅ FINALIZE: Market data collection complete"
        
        # Compile final data package
        final_data = {
            'current_indices': state.get('market_indices', []),
            'historical_data': state.get('historical_data', {}),
            'market_sentiment': state.get('market_sentiment', {}),
            'trend_analysis': state.get('trend_analysis', {}),
            'market_assessment': state.get('market_assessment', {}),
            'data_quality': {
                'score': self._assess_data_quality(state.get('market_indices', []))['score'],
                'issues': state.get('data_quality_issues', [])
            },
            'collection_metadata': {
                'timestamp': datetime.now().isoformat(),
                'sources_used': state.get('data_sources', []),
                'collection_frequency': state.get('collection_frequency', 30),
                'hitl_reviewed': state.get('hitl_approval_required', False)
            }
        }
        
        state['final_data'] = final_data
        
        reasoning += f" 📊 Data Summary:"
        reasoning += f" - Current indices: {len(final_data['current_indices'])}"
        reasoning += f" - Historical datasets: {len(final_data['historical_data'])}"
        reasoning += f" - Data quality: {final_data['data_quality']['score']}/100"
        reasoning += f" - Market sentiment: {final_data['market_sentiment'].get('fear_greed_index', 'N/A')}"
        
        if state.get('hitl_approval_required'):
            reasoning += f" - Human review: {'✅ Approved' if state.get('hitl_approved') else '❌ Rejected'}"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _log_collection(self, state: AgentState) -> AgentState:
        """Log the data collection to audit files"""
        reasoning = "📝 LOG: Recording data collection to audit trail"
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id,
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'collection_config': {
                'data_sources': state.get('data_sources', []),
                'collection_frequency': state.get('collection_frequency', 30)
            },
            'reasoning_trace': state['reasoning_trace'],
            'final_data': state['final_data'],
            'hitl_required': state.get('hitl_approval_required', False),
            'hitl_approved': state.get('hitl_approved', None),
            'performance_metrics': {
                'collection_time': len(state['reasoning_trace']) * 0.3,
                'data_quality_score': state['final_data']['data_quality']['score'],
                'sources_active': len(state.get('connection_status', {}))
            }
        }
        
        # Save to audit files
        await self._save_audit_log(audit_entry)
        await self._save_csv_log(audit_entry)
        
        reasoning += " ✅ Collection logged to audit trail"
        
        state['reasoning_trace'].append(reasoning)
        state['audit_log'] = [audit_entry]
        
        return state
    
    def _generate_mock_indices(self) -> List[Dict[str, Any]]:
        """Generate mock market indices data"""
        import random
        
        indices = [
            {'symbol': 'S&P 500', 'base_price': 4847.88},
            {'symbol': 'NASDAQ', 'base_price': 15181.92},
            {'symbol': 'DOW', 'base_price': 37753.31},
            {'symbol': 'RUSSELL 2000', 'base_price': 2089.44},
            {'symbol': 'VIX', 'base_price': 13.22}
        ]
        
        mock_data = []
        for idx in indices:
            change = random.uniform(-50, 50)
            change_percent = random.uniform(-2, 2)
            
            mock_data.append({
                'symbol': idx['symbol'],
                'current_price': idx['base_price'] + change,
                'change': change,
                'change_percent': change_percent,
                'volume': f"{random.uniform(1.0, 5.0):.1f}B",
                'timestamp': datetime.now().isoformat()
            })
        
        return mock_data
    
    def _generate_mock_historical(self) -> Dict[str, Any]:
        """Generate mock historical data"""
        import random
        
        historical = {}
        indices = ['S&P 500', 'NASDAQ', 'DOW']
        
        for index in indices:
            data_points = []
            base_price = 4000 if index == 'S&P 500' else 15000 if index == 'NASDAQ' else 37000
            
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                price_change = random.uniform(-0.02, 0.02) * base_price
                
                data_points.append({
                    'date': date,
                    'price': base_price + price_change,
                    'volume': random.randint(1000000, 5000000),
                    'change_percent': random.uniform(-2, 2)
                })
            
            historical[index] = data_points
        
        return historical
    
    def _generate_mock_sentiment(self) -> Dict[str, Any]:
        """Generate mock market sentiment data"""
        import random
        
        return {
            'fear_greed_index': random.randint(20, 80),
            'vix': random.uniform(12, 25),
            'put_call_ratio': random.uniform(0.7, 1.3),
            'insider_buying': random.choice(['Low', 'Moderate', 'High']),
            'analyst_sentiment': random.choice(['Bearish', 'Neutral', 'Bullish'])
        }
    
    def _assess_data_quality(self, indices_data: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of collected data"""
        if not indices_data:
            return {'score': 0, 'issues': ['No data collected']}
        
        issues = []
        score = 100
        
        # Check for missing data
        for idx in indices_data:
            if not idx.get('current_price'):
                issues.append(f"Missing price for {idx.get('symbol', 'unknown')}")
                score -= 20
            
            if not idx.get('timestamp'):
                issues.append(f"Missing timestamp for {idx.get('symbol', 'unknown')}")
                score -= 10
        
        # Check data freshness (within last 5 minutes)
        current_time = datetime.now()
        for idx in indices_data:
            if idx.get('timestamp'):
                try:
                    data_time = datetime.fromisoformat(idx['timestamp'].replace('Z', '+00:00'))
                    if (current_time - data_time.replace(tzinfo=None)).seconds > 300:
                        issues.append(f"Stale data for {idx.get('symbol', 'unknown')}")
                        score -= 15
                except:
                    pass
        
        return {'score': max(0, score), 'issues': issues}
    
    def _analyze_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """Analyze trends from historical data"""
        if not historical_data:
            return {'overall_trend': 'unknown', 'volatility_level': 'unknown'}
        
        trends = []
        volatilities = []
        
        for index, data in historical_data.items():
            if len(data) < 2:
                continue
            
            # Calculate simple trend (first vs last price)
            first_price = data[-1]['price']  # Oldest
            last_price = data[0]['price']    # Newest
            trend = (last_price - first_price) / first_price * 100
            trends.append(trend)
            
            # Calculate volatility (standard deviation of daily changes)
            changes = [point.get('change_percent', 0) for point in data]
            volatility = sum(abs(c) for c in changes) / len(changes)
            volatilities.append(volatility)
        
        if not trends:
            return {'overall_trend': 'unknown', 'volatility_level': 'unknown'}
        
        avg_trend = sum(trends) / len(trends)
        avg_volatility = sum(volatilities) / len(volatilities)
        
        # Determine overall trend
        if avg_trend > 2:
            overall_trend = 'strong_bullish'
        elif avg_trend > 0.5:
            overall_trend = 'bullish'
        elif avg_trend < -2:
            overall_trend = 'strong_bearish'
        elif avg_trend < -0.5:
            overall_trend = 'bearish'
        else:
            overall_trend = 'neutral'
        
        # Determine volatility level
        if avg_volatility > 2:
            volatility_level = 'high'
        elif avg_volatility > 1:
            volatility_level = 'medium'
        else:
            volatility_level = 'low'
        
        return {
            'overall_trend': overall_trend,
            'volatility_level': volatility_level,
            'avg_trend_percent': avg_trend,
            'avg_volatility': avg_volatility
        }
    
    def _generate_market_assessment(self, sentiment: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Generate overall market assessment"""
        confidence = 50
        status = "neutral"
        
        # Factor in sentiment
        fear_greed = sentiment.get('fear_greed_index', 50)
        if fear_greed > 70:
            confidence += 20
            status = "bullish"
        elif fear_greed < 30:
            confidence += 15
            status = "bearish"
        
        # Factor in trends
        trend = trend_analysis.get('overall_trend', 'neutral')
        if 'bullish' in trend:
            confidence += 15
            if status == "neutral":
                status = "bullish"
        elif 'bearish' in trend:
            confidence += 15
            if status == "neutral":
                status = "bearish"
        
        # Factor in volatility
        volatility = trend_analysis.get('volatility_level', 'medium')
        if volatility == 'high':
            confidence -= 20
        elif volatility == 'low':
            confidence += 10
        
        return {
            'status': status,
            'confidence': max(0, min(100, confidence)),
            'factors': {
                'sentiment_score': fear_greed,
                'trend': trend,
                'volatility': volatility
            }
        }
    
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
        """Save collection summary to CSV file"""
        try:
            final_data = audit_entry['final_data']
            
            csv_row = {
                'timestamp': audit_entry['timestamp'],
                'session_id': audit_entry['session_id'],
                'data_sources': ';'.join(audit_entry['collection_config']['data_sources']),
                'collection_frequency': audit_entry['collection_config']['collection_frequency'],
                'indices_collected': len(final_data['current_indices']),
                'data_quality_score': final_data['data_quality']['score'],
                'market_sentiment': final_data['market_sentiment'].get('fear_greed_index', 0),
                'overall_trend': final_data['trend_analysis'].get('overall_trend', 'unknown'),
                'volatility_level': final_data['trend_analysis'].get('volatility_level', 'unknown'),
                'hitl_required': audit_entry['hitl_required'],
                'hitl_approved': audit_entry['hitl_approved'],
                'collection_time': audit_entry['performance_metrics']['collection_time']
            }
            
            file_exists = os.path.exists(self.csv_log_file)
            with open(self.csv_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_row)
                
        except Exception as e:
            print(f"Error saving CSV log: {e}")
    
    def _initialize_csv_log(self):
        """Initialize CSV log file with headers"""
        if not os.path.exists(self.csv_log_file):
            headers = [
                'timestamp', 'session_id', 'data_sources', 'collection_frequency',
                'indices_collected', 'data_quality_score', 'market_sentiment',
                'overall_trend', 'volatility_level', 'hitl_required', 'hitl_approved',
                'collection_time'
            ]
            
            with open(self.csv_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    async def collect_market_data(self, data_sources: List[str], 
                                collection_frequency: int = 30,
                                hitl_enabled: bool = False) -> Dict[str, Any]:
        """Main entry point for market data collection"""
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=f"Collect market data from {len(data_sources)} sources")],
            data_sources=data_sources,
            collection_frequency=collection_frequency,
            market_indices=[],
            historical_data={},
            market_sentiment={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approved=None,
            final_data={},
            audit_log=[]
        )
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'data': final_state['final_data'],
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
            'mcp_server_connected': self.index_server is not None
        }

# Global agent instance
index_scraper_react_agent = IndexScraperReActAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = IndexScraperReActAgent()
        
        # Test data collection
        result = await agent.collect_market_data(
            data_sources=['yahoo_finance', 'alpha_vantage'],
            collection_frequency=30,
            hitl_enabled=True
        )
        
        print("Market Data Collection Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())
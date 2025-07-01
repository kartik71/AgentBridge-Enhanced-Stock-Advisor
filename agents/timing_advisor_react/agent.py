"""
TimingAdvisorAgent - LangGraph ReAct Agent for Market Timing Analysis
Uses ReAct pattern with reasoning traces for market timing recommendations
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
    timeframe: str
    analysis_depth: str
    market_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    timing_signals: Dict[str, Any]
    market_regime: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approved: bool
    final_recommendations: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

@dataclass
class TimingConfig:
    """Configuration for market timing analysis"""
    timeframe: str = "medium"  # short, medium, long
    analysis_depth: str = "advanced"  # basic, medium, advanced
    indicators: List[str] = None
    hitl_enabled: bool = False
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = ["rsi", "macd", "bollinger_bands", "moving_averages", "volume"]

class TimingAdvisorReActAgent:
    """LangGraph ReAct Agent for Market Timing Analysis with HITL support"""
    
    def __init__(self, agent_id: str = "timing_advisor_react"):
        self.agent_id = agent_id
        self.name = "TimingAdvisorReActAgent"
        self.version = "1.0.0"
        self.audit_log_file = "data/timing_advisor_audit.json"
        self.csv_log_file = "data/timing_advisor_decisions.csv"
        
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
        workflow.add_node("analyze_timeframe", self._analyze_timeframe)
        workflow.add_node("collect_market_data", self._collect_market_data)
        workflow.add_node("calculate_technical_indicators", self._calculate_technical_indicators)
        workflow.add_node("generate_timing_signals", self._generate_timing_signals)
        workflow.add_node("determine_market_regime", self._determine_market_regime)
        workflow.add_node("reason_about_timing", self._reason_about_timing)
        workflow.add_node("hitl_review", self._hitl_review)
        workflow.add_node("finalize_recommendations", self._finalize_recommendations)
        workflow.add_node("log_analysis", self._log_analysis)
        
        # Define the flow
        workflow.set_entry_point("analyze_timeframe")
        
        workflow.add_edge("analyze_timeframe", "collect_market_data")
        workflow.add_edge("collect_market_data", "calculate_technical_indicators")
        workflow.add_edge("calculate_technical_indicators", "generate_timing_signals")
        workflow.add_edge("generate_timing_signals", "determine_market_regime")
        workflow.add_edge("determine_market_regime", "reason_about_timing")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "reason_about_timing",
            self._should_require_hitl_approval,
            {
                "hitl_required": "hitl_review",
                "no_hitl": "finalize_recommendations"
            }
        )
        
        workflow.add_conditional_edges(
            "hitl_review",
            self._check_hitl_approval,
            {
                "approved": "finalize_recommendations",
                "rejected": "generate_timing_signals",  # Re-analyze signals
                "pending": END
            }
        )
        
        workflow.add_edge("finalize_recommendations", "log_analysis")
        workflow.add_edge("log_analysis", END)
        
        return workflow.compile()
    
    async def _analyze_timeframe(self, state: AgentState) -> AgentState:
        """Analyze and validate timeframe parameters"""
        reasoning = f"🔍 ANALYZE: Initializing timing analysis for {state['timeframe']} timeframe"
        reasoning += f" 📊 Analysis depth: {state['analysis_depth']}"
        
        # Validate timeframe
        valid_timeframes = ['short', 'medium', 'long']
        if state['timeframe'] not in valid_timeframes:
            reasoning += f" ⚠️ WARNING: Invalid timeframe '{state['timeframe']}', defaulting to 'medium'"
            state['timeframe'] = 'medium'
        
        # Set analysis parameters based on timeframe
        if state['timeframe'] == 'short':
            reasoning += " ⏱️ SHORT-TERM: Focus on intraday momentum and technical levels"
            state['analysis_params'] = {
                'lookback_days': 5,
                'signal_sensitivity': 'high',
                'primary_indicators': ['rsi', 'macd', 'volume']
            }
        elif state['timeframe'] == 'long':
            reasoning += " 📅 LONG-TERM: Emphasize fundamental trends and macro indicators"
            state['analysis_params'] = {
                'lookback_days': 90,
                'signal_sensitivity': 'low',
                'primary_indicators': ['moving_averages', 'trend_lines', 'support_resistance']
            }
        else:
            reasoning += " 📊 MEDIUM-TERM: Balance technical and fundamental factors"
            state['analysis_params'] = {
                'lookback_days': 30,
                'signal_sensitivity': 'medium',
                'primary_indicators': ['rsi', 'macd', 'bollinger_bands', 'moving_averages']
            }
        
        reasoning += " ✅ Timeframe analysis complete"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _collect_market_data(self, state: AgentState) -> AgentState:
        """Collect market data for timing analysis"""
        reasoning = "📈 COLLECT: Gathering market data for timing analysis..."
        
        try:
            if self.index_server:
                # Get current market data
                current_result = await self.index_server.get_current_indices()
                sentiment_result = await self.index_server.get_market_sentiment()
                
                # Get historical data based on timeframe
                lookback_days = state['analysis_params']['lookback_days']
                historical_data = {}
                
                major_indices = ['S&P 500', 'NASDAQ', 'DOW', 'VIX']
                for index in major_indices:
                    hist_result = await self.index_server.get_historical_data(index, days=lookback_days)
                    if hist_result['status'] == 'success':
                        historical_data[index] = hist_result['data']
                
                state['market_data'] = {
                    'current_indices': current_result.get('data', []),
                    'market_sentiment': sentiment_result.get('sentiment', {}),
                    'historical_data': historical_data,
                    'timestamp': datetime.now().isoformat()
                }
                
                reasoning += f" ✅ Retrieved data for {len(current_result.get('data', []))} indices"
                reasoning += f" 📊 Historical data: {lookback_days} days for {len(historical_data)} indices"
                
            else:
                # Generate mock data
                state['market_data'] = self._generate_mock_market_data(state['analysis_params'])
                reasoning += " ⚠️ Using mock market data (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error collecting data: {str(e)}"
            state['market_data'] = self._generate_mock_market_data(state['analysis_params'])
            reasoning += " 🔄 Falling back to mock data"
        
        # Assess data completeness
        data_completeness = self._assess_data_completeness(state['market_data'])
        reasoning += f" 📊 Data completeness: {data_completeness['score']}/100"
        
        state['data_completeness'] = data_completeness
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _calculate_technical_indicators(self, state: AgentState) -> AgentState:
        """Calculate technical indicators for timing analysis"""
        reasoning = "📊 INDICATORS: Calculating technical indicators..."
        
        market_data = state['market_data']
        indicators = {}
        
        try:
            # Calculate indicators for major indices
            for index_name, historical_data in market_data.get('historical_data', {}).items():
                if not historical_data or len(historical_data) < 10:
                    continue
                
                index_indicators = {}
                
                # RSI (Relative Strength Index)
                rsi = self._calculate_rsi(historical_data)
                index_indicators['rsi'] = rsi
                reasoning += f" 📈 {index_name} RSI: {rsi['current']:.1f}"
                
                # MACD
                macd = self._calculate_macd(historical_data)
                index_indicators['macd'] = macd
                reasoning += f" 📊 {index_name} MACD: {'Bullish' if macd['signal'] > 0 else 'Bearish'}"
                
                # Moving Averages
                ma = self._calculate_moving_averages(historical_data)
                index_indicators['moving_averages'] = ma
                reasoning += f" 📉 {index_name} MA Trend: {ma['trend']}"
                
                # Bollinger Bands
                bb = self._calculate_bollinger_bands(historical_data)
                index_indicators['bollinger_bands'] = bb
                
                # Volume Analysis
                volume = self._analyze_volume(historical_data)
                index_indicators['volume'] = volume
                
                indicators[index_name] = index_indicators
            
            state['technical_indicators'] = indicators
            reasoning += f" ✅ Calculated indicators for {len(indicators)} indices"
            
        except Exception as e:
            reasoning += f" ❌ Error calculating indicators: {str(e)}"
            state['technical_indicators'] = self._generate_mock_indicators()
            reasoning += " 🔄 Using fallback indicator calculations"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _generate_timing_signals(self, state: AgentState) -> AgentState:
        """Generate timing signals based on technical indicators"""
        reasoning = "🎯 SIGNALS: Generating timing signals from technical analysis..."
        
        indicators = state['technical_indicators']
        signals = {}
        
        try:
            for index_name, index_indicators in indicators.items():
                index_signals = {}
                signal_strength = 0
                signal_count = 0
                
                # RSI Signals
                rsi = index_indicators.get('rsi', {})
                if rsi.get('current', 50) < 30:
                    index_signals['rsi'] = {'signal': 'oversold', 'strength': 0.8}
                    signal_strength += 0.8
                    reasoning += f" 🔴 {index_name}: RSI Oversold ({rsi.get('current', 0):.1f})"
                elif rsi.get('current', 50) > 70:
                    index_signals['rsi'] = {'signal': 'overbought', 'strength': -0.8}
                    signal_strength -= 0.8
                    reasoning += f" 🟢 {index_name}: RSI Overbought ({rsi.get('current', 0):.1f})"
                else:
                    index_signals['rsi'] = {'signal': 'neutral', 'strength': 0}
                signal_count += 1
                
                # MACD Signals
                macd = index_indicators.get('macd', {})
                if macd.get('signal', 0) > 0:
                    index_signals['macd'] = {'signal': 'bullish_crossover', 'strength': 0.6}
                    signal_strength += 0.6
                    reasoning += f" 📈 {index_name}: MACD Bullish Crossover"
                elif macd.get('signal', 0) < 0:
                    index_signals['macd'] = {'signal': 'bearish_crossover', 'strength': -0.6}
                    signal_strength -= 0.6
                    reasoning += f" 📉 {index_name}: MACD Bearish Crossover"
                else:
                    index_signals['macd'] = {'signal': 'neutral', 'strength': 0}
                signal_count += 1
                
                # Moving Average Signals
                ma = index_indicators.get('moving_averages', {})
                if ma.get('trend') == 'bullish':
                    index_signals['trend'] = {'signal': 'uptrend', 'strength': 0.5}
                    signal_strength += 0.5
                    reasoning += f" ⬆️ {index_name}: Uptrend confirmed"
                elif ma.get('trend') == 'bearish':
                    index_signals['trend'] = {'signal': 'downtrend', 'strength': -0.5}
                    signal_strength -= 0.5
                    reasoning += f" ⬇️ {index_name}: Downtrend confirmed"
                else:
                    index_signals['trend'] = {'signal': 'sideways', 'strength': 0}
                signal_count += 1
                
                # Volume Confirmation
                volume = index_indicators.get('volume', {})
                if volume.get('trend') == 'increasing':
                    # Volume confirms the price movement
                    volume_multiplier = 1.2
                    reasoning += f" 📊 {index_name}: Volume confirms movement"
                else:
                    volume_multiplier = 0.8
                    reasoning += f" 📊 {index_name}: Weak volume"
                
                # Calculate overall signal
                avg_signal_strength = (signal_strength / signal_count) * volume_multiplier
                
                # Determine overall recommendation
                if avg_signal_strength > 0.4:
                    overall_signal = 'STRONG_BUY'
                elif avg_signal_strength > 0.1:
                    overall_signal = 'BUY'
                elif avg_signal_strength < -0.4:
                    overall_signal = 'STRONG_SELL'
                elif avg_signal_strength < -0.1:
                    overall_signal = 'SELL'
                else:
                    overall_signal = 'HOLD'
                
                index_signals['overall'] = {
                    'signal': overall_signal,
                    'strength': avg_signal_strength,
                    'confidence': min(95, abs(avg_signal_strength) * 100 + 60)
                }
                
                signals[index_name] = index_signals
                reasoning += f" 🎯 {index_name} Overall: {overall_signal} (strength: {avg_signal_strength:.2f})"
            
            state['timing_signals'] = signals
            reasoning += f" ✅ Generated signals for {len(signals)} indices"
            
        except Exception as e:
            reasoning += f" ❌ Error generating signals: {str(e)}"
            state['timing_signals'] = self._generate_mock_signals()
            reasoning += " 🔄 Using fallback signal generation"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _determine_market_regime(self, state: AgentState) -> AgentState:
        """Determine current market regime"""
        reasoning = "🌍 REGIME: Determining current market regime..."
        
        market_data = state['market_data']
        timing_signals = state['timing_signals']
        
        try:
            sentiment = market_data.get('market_sentiment', {})
            vix_level = sentiment.get('vix', 15)
            fear_greed = sentiment.get('fear_greed_index', 50)
            
            # Analyze VIX for volatility regime
            if vix_level < 15:
                volatility_regime = 'low_volatility'
                reasoning += f" 📉 Low volatility regime (VIX: {vix_level:.1f})"
            elif vix_level > 25:
                volatility_regime = 'high_volatility'
                reasoning += f" 📈 High volatility regime (VIX: {vix_level:.1f})"
            else:
                volatility_regime = 'normal_volatility'
                reasoning += f" ⚖️ Normal volatility regime (VIX: {vix_level:.1f})"
            
            # Analyze sentiment regime
            if fear_greed > 75:
                sentiment_regime = 'extreme_greed'
                reasoning += f" 🔥 Extreme greed detected (F&G: {fear_greed})"
            elif fear_greed > 55:
                sentiment_regime = 'greed'
                reasoning += f" 📈 Greedy sentiment (F&G: {fear_greed})"
            elif fear_greed < 25:
                sentiment_regime = 'extreme_fear'
                reasoning += f" 😰 Extreme fear detected (F&G: {fear_greed})"
            elif fear_greed < 45:
                sentiment_regime = 'fear'
                reasoning += f" 📉 Fearful sentiment (F&G: {fear_greed})"
            else:
                sentiment_regime = 'neutral'
                reasoning += f" ⚖️ Neutral sentiment (F&G: {fear_greed})"
            
            # Analyze trend regime from signals
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            
            for index_signals in timing_signals.values():
                overall = index_signals.get('overall', {})
                signal = overall.get('signal', 'HOLD')
                
                if 'BUY' in signal:
                    bullish_signals += 1
                elif 'SELL' in signal:
                    bearish_signals += 1
                total_signals += 1
            
            if total_signals > 0:
                bullish_ratio = bullish_signals / total_signals
                if bullish_ratio > 0.6:
                    trend_regime = 'bullish'
                    reasoning += f" 🐂 Bullish trend regime ({bullish_signals}/{total_signals} bullish)"
                elif bullish_ratio < 0.4:
                    trend_regime = 'bearish'
                    reasoning += f" 🐻 Bearish trend regime ({bearish_signals}/{total_signals} bearish)"
                else:
                    trend_regime = 'neutral'
                    reasoning += f" ⚖️ Neutral trend regime (mixed signals)"
            else:
                trend_regime = 'unknown'
            
            # Combine regimes for overall assessment
            market_regime = {
                'volatility_regime': volatility_regime,
                'sentiment_regime': sentiment_regime,
                'trend_regime': trend_regime,
                'vix_level': vix_level,
                'fear_greed_index': fear_greed,
                'regime_confidence': self._calculate_regime_confidence(volatility_regime, sentiment_regime, trend_regime),
                'description': f"{sentiment_regime.replace('_', ' ').title()} market in {volatility_regime.replace('_', ' ')} environment"
            }
            
            state['market_regime'] = market_regime
            reasoning += f" 🎯 Market regime: {market_regime['description']}"
            reasoning += f" 📊 Regime confidence: {market_regime['regime_confidence']}%"
            
        except Exception as e:
            reasoning += f" ❌ Error determining regime: {str(e)}"
            state['market_regime'] = self._generate_mock_regime()
            reasoning += " 🔄 Using fallback regime analysis"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _reason_about_timing(self, state: AgentState) -> AgentState:
        """Apply ReAct reasoning about market timing"""
        reasoning = "🧠 REASON: Synthesizing timing analysis and generating recommendations..."
        
        timing_signals = state['timing_signals']
        market_regime = state['market_regime']
        timeframe = state['timeframe']
        
        try:
            # Aggregate signals across indices
            total_strength = 0
            signal_count = 0
            recommendations = []
            
            for index_name, index_signals in timing_signals.items():
                overall = index_signals.get('overall', {})
                strength = overall.get('strength', 0)
                signal = overall.get('signal', 'HOLD')
                confidence = overall.get('confidence', 50)
                
                total_strength += strength
                signal_count += 1
                
                recommendations.append({
                    'index': index_name,
                    'signal': signal,
                    'strength': strength,
                    'confidence': confidence,
                    'reasoning': self._generate_signal_reasoning(index_signals, market_regime)
                })
            
            # Calculate overall market timing
            avg_strength = total_strength / signal_count if signal_count > 0 else 0
            
            # Adjust for market regime
            regime_adjustment = self._calculate_regime_adjustment(market_regime, timeframe)
            adjusted_strength = avg_strength * regime_adjustment
            
            reasoning += f" 📊 Raw signal strength: {avg_strength:.2f}"
            reasoning += f" ⚖️ Regime adjustment: {regime_adjustment:.2f}"
            reasoning += f" 🎯 Adjusted strength: {adjusted_strength:.2f}"
            
            # Generate overall timing recommendation
            if adjusted_strength > 0.5:
                overall_timing = 'STRONG_BUY_SIGNAL'
                timing_confidence = min(95, abs(adjusted_strength) * 80 + 70)
                reasoning += " 🚀 STRONG BUY signal detected"
            elif adjusted_strength > 0.2:
                overall_timing = 'BUY_SIGNAL'
                timing_confidence = min(90, abs(adjusted_strength) * 70 + 60)
                reasoning += " 📈 BUY signal detected"
            elif adjusted_strength < -0.5:
                overall_timing = 'STRONG_SELL_SIGNAL'
                timing_confidence = min(95, abs(adjusted_strength) * 80 + 70)
                reasoning += " 🔻 STRONG SELL signal detected"
            elif adjusted_strength < -0.2:
                overall_timing = 'SELL_SIGNAL'
                timing_confidence = min(90, abs(adjusted_strength) * 70 + 60)
                reasoning += " 📉 SELL signal detected"
            else:
                overall_timing = 'NEUTRAL'
                timing_confidence = 60
                reasoning += " ⚖️ NEUTRAL - no clear timing signal"
            
            # Generate timeframe-specific advice
            timeframe_advice = self._generate_timeframe_advice(overall_timing, timeframe, market_regime)
            reasoning += f" ⏰ {timeframe.upper()}-term advice: {timeframe_advice['summary']}"
            
            # Risk management recommendations
            risk_advice = self._generate_risk_advice(market_regime, overall_timing)
            reasoning += f" 🛡️ Risk management: {risk_advice['primary_recommendation']}"
            
            state['timing_analysis'] = {
                'overall_timing': overall_timing,
                'timing_confidence': timing_confidence,
                'signal_strength': adjusted_strength,
                'individual_recommendations': recommendations,
                'timeframe_advice': timeframe_advice,
                'risk_advice': risk_advice,
                'market_regime_impact': regime_adjustment
            }
            
            reasoning += " ✅ Timing analysis complete"
            
        except Exception as e:
            reasoning += f" ❌ Error in timing reasoning: {str(e)}"
            state['timing_analysis'] = self._generate_mock_timing_analysis()
            reasoning += " 🔄 Using fallback timing analysis"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _should_require_hitl_approval(self, state: AgentState) -> str:
        """Determine if HITL approval is required"""
        # Require HITL approval if:
        # 1. Strong signals in extreme market conditions
        # 2. Conflicting signals across indices
        # 3. Low confidence in regime analysis
        
        timing_analysis = state.get('timing_analysis', {})
        market_regime = state.get('market_regime', {})
        
        overall_timing = timing_analysis.get('overall_timing', 'NEUTRAL')
        timing_confidence = timing_analysis.get('timing_confidence', 50)
        regime_confidence = market_regime.get('regime_confidence', 50)
        sentiment_regime = market_regime.get('sentiment_regime', 'neutral')
        
        if ('STRONG' in overall_timing or 
            sentiment_regime in ['extreme_fear', 'extreme_greed'] or
            timing_confidence < 60 or 
            regime_confidence < 60):
            state['hitl_approval_required'] = True
            return "hitl_required"
        else:
            state['hitl_approval_required'] = False
            return "no_hitl"
    
    async def _hitl_review(self, state: AgentState) -> AgentState:
        """Handle Human-in-the-Loop review process"""
        reasoning = "👤 HITL: Timing analysis requires human review due to market conditions"
        
        timing_analysis = state.get('timing_analysis', {})
        market_regime = state.get('market_regime', {})
        
        reasoning += f" 🔍 Review criteria triggered:"
        reasoning += f" - Overall timing: {timing_analysis.get('overall_timing', 'unknown')}"
        reasoning += f" - Timing confidence: {timing_analysis.get('timing_confidence', 0)}%"
        reasoning += f" - Market regime: {market_regime.get('sentiment_regime', 'unknown')}"
        reasoning += f" - Regime confidence: {market_regime.get('regime_confidence', 0)}%"
        
        reasoning += " ⏳ Waiting for human approval..."
        
        # Simulate human decision based on analysis quality
        timing_confidence = timing_analysis.get('timing_confidence', 50)
        regime_confidence = market_regime.get('regime_confidence', 50)
        overall_confidence = (timing_confidence + regime_confidence) / 2
        
        if overall_confidence > 65:
            state['hitl_approved'] = True
            reasoning += " ✅ Analysis approved by human reviewer"
        else:
            state['hitl_approved'] = False
            reasoning += " ❌ Analysis rejected - requires re-evaluation"
        
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
    
    async def _finalize_recommendations(self, state: AgentState) -> AgentState:
        """Finalize timing recommendations"""
        reasoning = "✅ FINALIZE: Market timing analysis complete"
        
        timing_analysis = state.get('timing_analysis', {})
        market_regime = state.get('market_regime', {})
        
        # Compile final recommendations
        final_recommendations = {
            'overall_timing': timing_analysis.get('overall_timing', 'NEUTRAL'),
            'confidence': timing_analysis.get('timing_confidence', 50),
            'signal_strength': timing_analysis.get('signal_strength', 0),
            'market_regime': market_regime,
            'individual_signals': timing_analysis.get('individual_recommendations', []),
            'timeframe_advice': timing_analysis.get('timeframe_advice', {}),
            'risk_management': timing_analysis.get('risk_advice', {}),
            'next_review': (datetime.now() + timedelta(hours=4)).isoformat(),
            'analysis_metadata': {
                'timeframe': state.get('timeframe', 'medium'),
                'analysis_depth': state.get('analysis_depth', 'advanced'),
                'hitl_reviewed': state.get('hitl_approval_required', False),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        state['final_recommendations'] = final_recommendations
        
        reasoning += f" 🎯 Final Timing: {final_recommendations['overall_timing']}"
        reasoning += f" 📊 Confidence: {final_recommendations['confidence']}%"
        reasoning += f" ⚖️ Signal Strength: {final_recommendations['signal_strength']:.2f}"
        reasoning += f" 🌍 Market Regime: {market_regime.get('description', 'unknown')}"
        
        if state.get('hitl_approval_required'):
            reasoning += f" - Human Review: {'✅ Approved' if state.get('hitl_approved') else '❌ Rejected'}"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _log_analysis(self, state: AgentState) -> AgentState:
        """Log the timing analysis to audit files"""
        reasoning = "📝 LOG: Recording timing analysis to audit trail"
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id,
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'analysis_config': {
                'timeframe': state.get('timeframe', 'medium'),
                'analysis_depth': state.get('analysis_depth', 'advanced')
            },
            'reasoning_trace': state['reasoning_trace'],
            'final_recommendations': state['final_recommendations'],
            'hitl_required': state.get('hitl_approval_required', False),
            'hitl_approved': state.get('hitl_approved', None),
            'performance_metrics': {
                'analysis_time': len(state['reasoning_trace']) * 0.4,
                'confidence_score': state['final_recommendations']['confidence'],
                'signal_strength': abs(state['final_recommendations']['signal_strength'])
            }
        }
        
        # Save to audit files
        await self._save_audit_log(audit_entry)
        await self._save_csv_log(audit_entry)
        
        reasoning += " ✅ Analysis logged to audit trail"
        
        state['reasoning_trace'].append(reasoning)
        state['audit_log'] = [audit_entry]
        
        return state
    
    # Helper methods for calculations and mock data generation
    def _calculate_rsi(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate RSI indicator"""
        if len(historical_data) < 14:
            return {'current': 50, 'trend': 'neutral'}
        
        # Simplified RSI calculation
        import random
        rsi_value = random.uniform(25, 75)  # Mock RSI
        
        if rsi_value < 30:
            trend = 'oversold'
        elif rsi_value > 70:
            trend = 'overbought'
        else:
            trend = 'neutral'
        
        return {'current': rsi_value, 'trend': trend}
    
    def _calculate_macd(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate MACD indicator"""
        import random
        
        # Mock MACD calculation
        macd_line = random.uniform(-2, 2)
        signal_line = random.uniform(-2, 2)
        histogram = macd_line - signal_line
        
        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram,
            'signal': 1 if macd_line > signal_line else -1
        }
    
    def _calculate_moving_averages(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate moving averages"""
        if len(historical_data) < 20:
            return {'trend': 'neutral', 'ma_20': 0, 'ma_50': 0}
        
        # Simplified MA calculation
        prices = [float(item.get('price', 0)) for item in historical_data[:20]]
        ma_20 = sum(prices) / len(prices)
        
        current_price = float(historical_data[0].get('price', 0))
        
        if current_price > ma_20 * 1.02:
            trend = 'bullish'
        elif current_price < ma_20 * 0.98:
            trend = 'bearish'
        else:
            trend = 'neutral'
        
        return {'trend': trend, 'ma_20': ma_20, 'current_price': current_price}
    
    def _calculate_bollinger_bands(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate Bollinger Bands"""
        import random
        
        # Mock Bollinger Bands
        return {
            'upper_band': random.uniform(4900, 5000),
            'middle_band': random.uniform(4800, 4900),
            'lower_band': random.uniform(4700, 4800),
            'position': random.choice(['upper', 'middle', 'lower'])
        }
    
    def _analyze_volume(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze volume trends"""
        import random
        
        return {
            'trend': random.choice(['increasing', 'decreasing', 'stable']),
            'relative_volume': random.uniform(0.5, 2.0),
            'volume_confirmation': random.choice([True, False])
        }
    
    def _generate_mock_market_data(self, analysis_params: Dict) -> Dict[str, Any]:
        """Generate mock market data"""
        import random
        
        return {
            'current_indices': [
                {'symbol': 'S&P 500', 'price': 4847.88, 'change_percent': random.uniform(-2, 2)},
                {'symbol': 'NASDAQ', 'price': 15181.92, 'change_percent': random.uniform(-2.5, 2.5)},
                {'symbol': 'DOW', 'price': 37753.31, 'change_percent': random.uniform(-1.5, 1.5)}
            ],
            'market_sentiment': {
                'fear_greed_index': random.randint(20, 80),
                'vix': random.uniform(12, 30)
            },
            'historical_data': {
                'S&P 500': [{'price': 4800 + random.uniform(-100, 100), 'date': f"2024-01-{i:02d}"} for i in range(1, 31)]
            }
        }
    
    def _generate_mock_indicators(self) -> Dict[str, Any]:
        """Generate mock technical indicators"""
        import random
        
        return {
            'S&P 500': {
                'rsi': {'current': random.uniform(30, 70), 'trend': 'neutral'},
                'macd': {'signal': random.choice([-1, 0, 1])},
                'moving_averages': {'trend': random.choice(['bullish', 'bearish', 'neutral'])},
                'volume': {'trend': 'increasing'}
            }
        }
    
    def _generate_mock_signals(self) -> Dict[str, Any]:
        """Generate mock timing signals"""
        import random
        
        return {
            'S&P 500': {
                'overall': {
                    'signal': random.choice(['BUY', 'SELL', 'HOLD']),
                    'strength': random.uniform(-1, 1),
                    'confidence': random.randint(60, 90)
                }
            }
        }
    
    def _generate_mock_regime(self) -> Dict[str, Any]:
        """Generate mock market regime"""
        import random
        
        return {
            'volatility_regime': random.choice(['low_volatility', 'normal_volatility', 'high_volatility']),
            'sentiment_regime': random.choice(['fear', 'neutral', 'greed']),
            'trend_regime': random.choice(['bearish', 'neutral', 'bullish']),
            'regime_confidence': random.randint(50, 90)
        }
    
    def _generate_mock_timing_analysis(self) -> Dict[str, Any]:
        """Generate mock timing analysis"""
        import random
        
        return {
            'overall_timing': random.choice(['BUY_SIGNAL', 'SELL_SIGNAL', 'NEUTRAL']),
            'timing_confidence': random.randint(60, 90),
            'signal_strength': random.uniform(-1, 1)
        }
    
    def _assess_data_completeness(self, market_data: Dict) -> Dict[str, Any]:
        """Assess completeness of market data"""
        score = 100
        issues = []
        
        if not market_data.get('current_indices'):
            score -= 30
            issues.append('Missing current indices data')
        
        if not market_data.get('historical_data'):
            score -= 40
            issues.append('Missing historical data')
        
        if not market_data.get('market_sentiment'):
            score -= 20
            issues.append('Missing sentiment data')
        
        return {'score': max(0, score), 'issues': issues}
    
    def _calculate_regime_confidence(self, volatility: str, sentiment: str, trend: str) -> int:
        """Calculate confidence in regime analysis"""
        confidence = 50
        
        # Clear regimes increase confidence
        if volatility in ['low_volatility', 'high_volatility']:
            confidence += 15
        
        if sentiment in ['extreme_fear', 'extreme_greed']:
            confidence += 20
        elif sentiment in ['fear', 'greed']:
            confidence += 10
        
        if trend in ['bullish', 'bearish']:
            confidence += 15
        
        return min(95, confidence)
    
    def _generate_signal_reasoning(self, index_signals: Dict, market_regime: Dict) -> str:
        """Generate reasoning for individual signals"""
        overall = index_signals.get('overall', {})
        signal = overall.get('signal', 'HOLD')
        
        if 'BUY' in signal:
            return "Technical indicators show bullish momentum with volume confirmation"
        elif 'SELL' in signal:
            return "Technical indicators show bearish momentum with negative divergence"
        else:
            return "Mixed signals suggest waiting for clearer direction"
    
    def _calculate_regime_adjustment(self, market_regime: Dict, timeframe: str) -> float:
        """Calculate adjustment factor based on market regime"""
        adjustment = 1.0
        
        sentiment = market_regime.get('sentiment_regime', 'neutral')
        volatility = market_regime.get('volatility_regime', 'normal_volatility')
        
        # Extreme conditions require more caution
        if sentiment in ['extreme_fear', 'extreme_greed']:
            adjustment *= 0.8
        
        if volatility == 'high_volatility':
            adjustment *= 0.9
        
        # Short-term trading in volatile conditions
        if timeframe == 'short' and volatility == 'high_volatility':
            adjustment *= 0.7
        
        return adjustment
    
    def _generate_timeframe_advice(self, overall_timing: str, timeframe: str, market_regime: Dict) -> Dict[str, Any]:
        """Generate timeframe-specific advice"""
        advice = {
            'short': {
                'BUY_SIGNAL': "Consider intraday long positions with tight stops",
                'SELL_SIGNAL': "Look for short-term shorting opportunities",
                'NEUTRAL': "Wait for clearer intraday signals"
            },
            'medium': {
                'BUY_SIGNAL': "Initiate swing positions over 1-4 week horizon",
                'SELL_SIGNAL': "Consider reducing exposure or hedging",
                'NEUTRAL': "Maintain current positions, monitor for changes"
            },
            'long': {
                'BUY_SIGNAL': "Accumulate positions for long-term holdings",
                'SELL_SIGNAL': "Consider portfolio rebalancing",
                'NEUTRAL': "Focus on fundamental analysis for entries"
            }
        }
        
        base_advice = advice.get(timeframe, {}).get(overall_timing, "Monitor market conditions")
        
        return {
            'summary': base_advice,
            'timeframe': timeframe,
            'regime_consideration': f"Account for {market_regime.get('description', 'current market')} conditions"
        }
    
    def _generate_risk_advice(self, market_regime: Dict, overall_timing: str) -> Dict[str, Any]:
        """Generate risk management advice"""
        volatility = market_regime.get('volatility_regime', 'normal_volatility')
        sentiment = market_regime.get('sentiment_regime', 'neutral')
        
        if volatility == 'high_volatility':
            primary = "Use tighter stop losses and smaller position sizes"
        elif sentiment in ['extreme_fear', 'extreme_greed']:
            primary = "Exercise extra caution due to extreme sentiment"
        elif 'STRONG' in overall_timing:
            primary = "Strong signals warrant normal position sizing with stops"
        else:
            primary = "Standard risk management applies"
        
        return {
            'primary_recommendation': primary,
            'stop_loss_suggestion': "2-3% for normal volatility, 1-2% for high volatility",
            'position_sizing': "Reduce size in extreme conditions"
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
        """Save analysis summary to CSV file"""
        try:
            final_recs = audit_entry['final_recommendations']
            
            csv_row = {
                'timestamp': audit_entry['timestamp'],
                'session_id': audit_entry['session_id'],
                'timeframe': audit_entry['analysis_config']['timeframe'],
                'analysis_depth': audit_entry['analysis_config']['analysis_depth'],
                'overall_timing': final_recs['overall_timing'],
                'confidence': final_recs['confidence'],
                'signal_strength': final_recs['signal_strength'],
                'market_regime': final_recs['market_regime'].get('description', 'unknown'),
                'volatility_regime': final_recs['market_regime'].get('volatility_regime', 'unknown'),
                'sentiment_regime': final_recs['market_regime'].get('sentiment_regime', 'unknown'),
                'hitl_required': audit_entry['hitl_required'],
                'hitl_approved': audit_entry['hitl_approved'],
                'analysis_time': audit_entry['performance_metrics']['analysis_time']
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
                'timestamp', 'session_id', 'timeframe', 'analysis_depth',
                'overall_timing', 'confidence', 'signal_strength', 'market_regime',
                'volatility_regime', 'sentiment_regime', 'hitl_required', 'hitl_approved',
                'analysis_time'
            ]
            
            with open(self.csv_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    async def analyze_market_timing(self, timeframe: str = "medium", 
                                  analysis_depth: str = "advanced",
                                  hitl_enabled: bool = False) -> Dict[str, Any]:
        """Main entry point for market timing analysis"""
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=f"Analyze market timing for {timeframe} timeframe")],
            timeframe=timeframe,
            analysis_depth=analysis_depth,
            market_data={},
            technical_indicators={},
            timing_signals={},
            market_regime={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approved=None,
            final_recommendations={},
            audit_log=[]
        )
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'recommendations': final_state['final_recommendations'],
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
timing_advisor_react_agent = TimingAdvisorReActAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = TimingAdvisorReActAgent()
        
        # Test timing analysis
        result = await agent.analyze_market_timing(
            timeframe="medium",
            analysis_depth="advanced",
            hitl_enabled=True
        )
        
        print("Market Timing Analysis Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())
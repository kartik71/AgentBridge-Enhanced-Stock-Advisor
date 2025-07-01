"""
Example: A2A Communication in LangGraph Stock Advisor
Demonstrates enhanced portfolio optimization with agent-to-agent communication
"""

import asyncio
import json
from datetime import datetime

from agents.enhanced_portfolio_optimizer import EnhancedPortfolioOptimizerAgent

async def example_a2a_enabled_optimization():
    """Example: Portfolio optimization with A2A communication enabled"""
    print("🚀 Example 1: A2A-Enhanced Portfolio Optimization")
    print("=" * 60)
    
    agent = EnhancedPortfolioOptimizerAgent()
    
    user_config = {
        "budget": 75000,
        "timeframe": "Medium",
        "riskLevel": "Medium",
        "goals": "Growth",
        "user_id": "demo_user"
    }
    
    # Run optimization with A2A enabled
    result = await agent.optimize_portfolio_with_a2a(user_config, a2a_enabled=True)
    
    if result['status'] == 'success':
        print("✅ A2A-Enhanced optimization successful!")
        
        # Show A2A data integration
        if result['market_data']:
            print(f"📊 Market Data: {result['market_data']['status']}")
            
        if result['timing_analysis']:
            print(f"⏰ Timing Analysis: {result['timing_analysis']['status']}")
            
        if result['compliance_check']:
            print(f"🛡️ Compliance Check: {result['compliance_check']['status']}")
        
        # Show enhanced recommendations
        recommendations = result['portfolio_recommendations']
        print(f"\n🏆 Enhanced Recommendations ({len(recommendations)} stocks):")
        
        for rec in recommendations:
            enhancement = " (A2A Enhanced)" if rec.get('a2a_enhanced') else ""
            print(f"  • {rec['symbol']}: {rec['allocation']}% - {rec['action']} ({rec['confidence']}% confidence){enhancement}")
        
        # Show reasoning trace
        print("\n🧠 A2A Communication Trace:")
        for i, step in enumerate(result['reasoning_trace'], 1):
            if 'A2A' in step:
                print(f"  {i}. {step}")
    else:
        print(f"❌ Optimization failed: {result.get('error')}")

async def example_a2a_disabled_optimization():
    """Example: Portfolio optimization with A2A communication disabled"""
    print("\n🚀 Example 2: Standalone Portfolio Optimization")
    print("=" * 60)
    
    agent = EnhancedPortfolioOptimizerAgent()
    
    user_config = {
        "budget": 75000,
        "timeframe": "Medium", 
        "riskLevel": "Medium",
        "goals": "Growth",
        "user_id": "demo_user"
    }
    
    # Run optimization with A2A disabled
    result = await agent.optimize_portfolio_with_a2a(user_config, a2a_enabled=False)
    
    if result['status'] == 'success':
        print("✅ Standalone optimization successful!")
        
        recommendations = result['portfolio_recommendations']
        print(f"\n📊 Standard Recommendations ({len(recommendations)} stocks):")
        
        for rec in recommendations:
            print(f"  • {rec['symbol']}: {rec['allocation']}% - {rec['action']} ({rec['confidence']}% confidence)")
        
        print("\n🔍 Comparison Notes:")
        print("  • Lower confidence scores without real-time data")
        print("  • No timing analysis integration")
        print("  • No automated compliance checking")
        print("  • Faster execution but less informed decisions")
    else:
        print(f"❌ Optimization failed: {result.get('error')}")

async def example_a2a_performance_comparison():
    """Example: Compare A2A vs standalone performance"""
    print("\n🚀 Example 3: A2A vs Standalone Performance Comparison")
    print("=" * 60)
    
    agent = EnhancedPortfolioOptimizerAgent()
    
    user_config = {
        "budget": 50000,
        "timeframe": "Short",
        "riskLevel": "High",
        "goals": "Aggressive Growth"
    }
    
    # Run both modes
    print("🔗 Running A2A-enabled optimization...")
    a2a_result = await agent.optimize_portfolio_with_a2a(user_config, a2a_enabled=True)
    
    print("🚫 Running standalone optimization...")
    standalone_result = await agent.optimize_portfolio_with_a2a(user_config, a2a_enabled=False)
    
    # Compare results
    if a2a_result['status'] == 'success' and standalone_result['status'] == 'success':
        a2a_recs = a2a_result['portfolio_recommendations']
        standalone_recs = standalone_result['portfolio_recommendations']
        
        print("\n📊 Performance Comparison:")
        print(f"{'Metric':<25} {'A2A Mode':<15} {'Standalone':<15} {'Difference'}")
        print("-" * 70)
        
        # Average confidence
        a2a_confidence = sum(r['confidence'] for r in a2a_recs) / len(a2a_recs)
        standalone_confidence = sum(r['confidence'] for r in standalone_recs) / len(standalone_recs)
        confidence_diff = a2a_confidence - standalone_confidence
        
        print(f"{'Avg Confidence':<25} {a2a_confidence:<15.1f} {standalone_confidence:<15.1f} {confidence_diff:+.1f}")
        
        # Number of recommendations
        print(f"{'Recommendations':<25} {len(a2a_recs):<15} {len(standalone_recs):<15} {len(a2a_recs) - len(standalone_recs):+}")
        
        # Data sources used
        a2a_sources = 0
        if a2a_result.get('market_data', {}).get('status') == 'success':
            a2a_sources += 1
        if a2a_result.get('timing_analysis', {}).get('status') == 'success':
            a2a_sources += 1
        if a2a_result.get('compliance_check', {}).get('status') == 'success':
            a2a_sources += 1
        
        print(f"{'Data Sources':<25} {a2a_sources:<15} {'0':<15} {a2a_sources:+}")
        
        print("\n🎯 A2A Advantages:")
        print("  ✅ Higher confidence scores from real-time data")
        print("  ✅ Market timing integration for better entry points")
        print("  ✅ Automated compliance validation")
        print("  ✅ Enhanced reasoning with multi-agent insights")

async def example_a2a_communication_flow():
    """Example: Detailed A2A communication flow"""
    print("\n🚀 Example 4: A2A Communication Flow Analysis")
    print("=" * 60)
    
    agent = EnhancedPortfolioOptimizerAgent()
    
    user_config = {
        "budget": 100000,
        "timeframe": "Long",
        "riskLevel": "Low",
        "goals": "Income"
    }
    
    result = await agent.optimize_portfolio_with_a2a(user_config, a2a_enabled=True)
    
    if result['status'] == 'success':
        print("✅ A2A communication flow completed successfully")
        
        print("\n🔄 A2A Communication Flow:")
        print("  1. EnhancedPortfolioOptimizer → IndexScraperAgent")
        print("     ↳ Requests real-time market data and sentiment")
        
        print("  2. IndexScraperAgent → EnhancedPortfolioOptimizer")
        print("     ↳ Returns current indices, sentiment, and historical data")
        
        print("  3. EnhancedPortfolioOptimizer → TimingAdvisorAgent")
        print("     ↳ Requests timing analysis with market context")
        
        print("  4. TimingAdvisorAgent → EnhancedPortfolioOptimizer")
        print("     ↳ Returns timing signals, market regime, and recommendations")
        
        print("  5. EnhancedPortfolioOptimizer generates portfolio")
        print("     ↳ Integrates market data and timing analysis")
        
        print("  6. EnhancedPortfolioOptimizer → ComplianceLoggerAgent")
        print("     ↳ Requests compliance validation of portfolio")
        
        print("  7. ComplianceLoggerAgent → EnhancedPortfolioOptimizer")
        print("     ↳ Returns compliance score, violations, and recommendations")
        
        print("  8. EnhancedPortfolioOptimizer finalizes recommendations")
        print("     ↳ Adjusts portfolio based on compliance feedback")
        
        print("\n📊 Data Exchange Summary:")
        for step in result['reasoning_trace']:
            if 'A2A QUERY' in step:
                print(f"  • {step}")

async def main():
    """Run all examples"""
    print("🎯 A2A Communication in LangGraph Stock Advisor")
    print("=" * 70)
    
    try:
        await example_a2a_enabled_optimization()
        await example_a2a_disabled_optimization()
        await example_a2a_performance_comparison()
        await example_a2a_communication_flow()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 Key A2A Features Demonstrated:")
        print("  ✅ Direct agent-to-agent method calls")
        print("  ✅ Sequential multi-agent workflow")
        print("  ✅ Conditional A2A communication based on toggle")
        print("  ✅ Enhanced decision quality with multi-agent insights")
        print("  ✅ Graceful fallback when A2A is disabled")
        print("  ✅ UI controls for A2A management")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
Example usage of PortfolioOptimizerReActAgent
Demonstrates the ReAct pattern with reasoning traces and HITL approval
"""

import asyncio
import json
from datetime import datetime

from agents.portfolio_optimizer_react.agent import PortfolioOptimizerReActAgent

async def example_basic_optimization():
    """Example: Basic portfolio optimization"""
    print("🚀 Example 1: Basic Portfolio Optimization")
    print("=" * 50)
    
    agent = PortfolioOptimizerReActAgent()
    
    result = await agent.optimize_portfolio(
        budget=50000,
        timeframe="Medium",
        risk_level="Medium"
    )
    
    if result['status'] == 'success':
        print("✅ Optimization successful!")
        print(f"📊 Portfolio: {len(result['portfolio']['positions'])} positions")
        print(f"💰 Total Investment: ${result['portfolio']['total_investment']:,.2f}")
        print(f"📈 Expected Return: {result['portfolio']['expected_return']:.1f}%")
        
        print("\n🧠 Reasoning Trace:")
        for i, step in enumerate(result['reasoning_trace'], 1):
            print(f"{i}. {step}")
        
        print("\n📋 Portfolio Positions:")
        for pos in result['portfolio']['positions']:
            print(f"  • {pos['symbol']}: {pos['allocation_percent']}% (${pos['investment_amount']:,.2f})")
    else:
        print(f"❌ Optimization failed: {result.get('error')}")

async def example_high_risk_with_hitl():
    """Example: High-risk portfolio requiring HITL approval"""
    print("\n🚀 Example 2: High-Risk Portfolio with HITL")
    print("=" * 50)
    
    agent = PortfolioOptimizerReActAgent()
    
    result = await agent.optimize_portfolio(
        budget=150000,  # Large budget to trigger HITL
        timeframe="Short",
        risk_level="High",
        hitl_enabled=True
    )
    
    if result['status'] == 'success':
        print("✅ Optimization completed!")
        print(f"👤 HITL Required: {result['hitl_required']}")
        print(f"✅ HITL Approved: {result['hitl_approved']}")
        
        if result['hitl_required']:
            print("\n🔍 HITL Review Criteria Met:")
            portfolio = result['portfolio']
            print(f"  • Risk Score: {portfolio['risk_score']:.1f}/3.0")
            print(f"  • Budget: ${result['portfolio']['total_investment']:,.2f}")
            print(f"  • Diversification: {portfolio['diversification_score']}%")
        
        print("\n🧠 Key Reasoning Steps:")
        for step in result['reasoning_trace']:
            if any(keyword in step for keyword in ['HITL', 'RISK', 'APPROVE']):
                print(f"  • {step}")
    else:
        print(f"❌ Optimization failed: {result.get('error')}")

async def example_conservative_portfolio():
    """Example: Conservative, low-risk portfolio"""
    print("\n🚀 Example 3: Conservative Portfolio")
    print("=" * 50)
    
    agent = PortfolioOptimizerReActAgent()
    
    result = await agent.optimize_portfolio(
        budget=25000,
        timeframe="Long",
        risk_level="Low"
    )
    
    if result['status'] == 'success':
        portfolio = result['portfolio']
        
        print("✅ Conservative portfolio optimized!")
        print(f"🛡️ Risk Score: {portfolio['risk_score']:.1f}/3.0 (Lower is safer)")
        print(f"🏢 Diversification: {portfolio['diversification_score']}%")
        print(f"💰 Cash Remaining: ${portfolio['cash_remaining']:,.2f}")
        
        print("\n📊 Risk Analysis from Reasoning:")
        for step in result['reasoning_trace']:
            if 'RISK' in step or 'LOW' in step:
                print(f"  • {step}")
        
        print("\n🏆 Top Holdings:")
        for pos in sorted(portfolio['positions'], key=lambda x: x['allocation_percent'], reverse=True)[:3]:
            print(f"  • {pos['symbol']}: {pos['allocation_percent']}% - {pos['risk_level']} Risk")

async def example_audit_trail_analysis():
    """Example: Analyze audit trail"""
    print("\n🚀 Example 4: Audit Trail Analysis")
    print("=" * 50)
    
    agent = PortfolioOptimizerReActAgent()
    
    # Run a few optimizations to generate audit data
    for i in range(3):
        await agent.optimize_portfolio(
            budget=30000 + (i * 10000),
            timeframe=["Short", "Medium", "Long"][i],
            risk_level=["Low", "Medium", "High"][i]
        )
    
    # Analyze audit log
    try:
        with open(agent.audit_log_file, 'r') as f:
            audit_log = json.load(f)
        
        print(f"📝 Total audit entries: {len(audit_log)}")
        
        if audit_log:
            latest = audit_log[-1]
            print(f"🕒 Latest optimization: {latest['timestamp']}")
            print(f"💰 Budget: ${latest['inputs']['budget']:,.2f}")
            print(f"⚖️ Risk Level: {latest['inputs']['risk_level']}")
            print(f"🎯 Positions: {len(latest['final_portfolio']['positions'])}")
            print(f"📈 Expected Return: {latest['final_portfolio']['expected_return']:.1f}%")
            
            # Show reasoning trace length
            print(f"🧠 Reasoning steps: {len(latest['reasoning_trace'])}")
    
    except FileNotFoundError:
        print("📝 No audit log found yet")

async def example_agent_status():
    """Example: Check agent status and capabilities"""
    print("\n🚀 Example 5: Agent Status")
    print("=" * 50)
    
    agent = PortfolioOptimizerReActAgent()
    status = await agent.get_agent_status()
    
    print("🤖 Agent Information:")
    print(f"  • Name: {status['name']}")
    print(f"  • Version: {status['version']}")
    print(f"  • Status: {status['status']}")
    print(f"  • Graph Nodes: {status['graph_nodes']}")
    
    print("\n🔌 MCP Server Connections:")
    for server, connected in status['mcp_servers'].items():
        status_icon = "✅" if connected else "❌"
        print(f"  • {server}: {status_icon}")
    
    print(f"\n📁 Audit Files:")
    print(f"  • JSON Log: {status['audit_log_file']}")
    print(f"  • CSV Log: {status['csv_log_file']}")

async def main():
    """Run all examples"""
    print("🎯 PortfolioOptimizerReActAgent Examples")
    print("=" * 60)
    
    try:
        await example_basic_optimization()
        await example_high_risk_with_hitl()
        await example_conservative_portfolio()
        await example_audit_trail_analysis()
        await example_agent_status()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 Key Features Demonstrated:")
        print("  ✅ ReAct reasoning pattern with explicit traces")
        print("  ✅ Modern Portfolio Theory optimization")
        print("  ✅ Human-in-the-loop approval for high-risk portfolios")
        print("  ✅ Comprehensive audit logging (JSON + CSV)")
        print("  ✅ Risk-based allocation and diversification")
        print("  ✅ MCP server integration for real-time data")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(main())
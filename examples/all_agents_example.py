"""
Example usage of all LangGraph ReAct Agents
Demonstrates the complete multi-agent system for stock analysis
"""

import asyncio
import json
from datetime import datetime

from agents.portfolio_optimizer_react.agent import PortfolioOptimizerReActAgent
from agents.index_scraper_react.agent import IndexScraperReActAgent
from agents.timing_advisor_react.agent import TimingAdvisorReActAgent
from agents.compliance_logger_react.agent import ComplianceLoggerReActAgent

async def example_complete_workflow():
    """Example: Complete multi-agent workflow"""
    print("🚀 Complete Multi-Agent Stock Analysis Workflow")
    print("=" * 60)
    
    # Initialize all agents
    index_scraper = IndexScraperReActAgent()
    portfolio_optimizer = PortfolioOptimizerReActAgent()
    timing_advisor = TimingAdvisorReActAgent()
    compliance_logger = ComplianceLoggerReActAgent()
    
    try:
        # Step 1: Collect Market Data
        print("\n📊 Step 1: Market Data Collection")
        print("-" * 40)
        
        market_data_result = await index_scraper.collect_market_data(
            data_sources=['yahoo_finance', 'alpha_vantage'],
            collection_frequency=30,
            hitl_enabled=True
        )
        
        if market_data_result['status'] == 'success':
            print("✅ Market data collected successfully")
            market_data = market_data_result['data']
            print(f"📈 Indices collected: {len(market_data['current_indices'])}")
            print(f"📊 Data quality: {market_data['data_quality']['score']}/100")
            
            # Show key reasoning steps
            print("\n🧠 Key Market Data Insights:")
            for step in market_data_result['reasoning_trace']:
                if any(keyword in step for keyword in ['SENTIMENT', 'TREND', 'QUALITY']):
                    print(f"  • {step}")
        else:
            print(f"❌ Market data collection failed: {market_data_result.get('error')}")
            return
        
        # Step 2: Market Timing Analysis
        print("\n⏰ Step 2: Market Timing Analysis")
        print("-" * 40)
        
        timing_result = await timing_advisor.analyze_market_timing(
            timeframe="medium",
            analysis_depth="advanced",
            hitl_enabled=True
        )
        
        if timing_result['status'] == 'success':
            print("✅ Market timing analysis completed")
            timing_recs = timing_result['recommendations']
            print(f"🎯 Overall timing: {timing_recs['overall_timing']}")
            print(f"📊 Confidence: {timing_recs['confidence']}%")
            print(f"⚖️ Signal strength: {timing_recs['signal_strength']:.2f}")
            
            # Show market regime
            regime = timing_recs['market_regime']
            print(f"🌍 Market regime: {regime.get('description', 'unknown')}")
            
            print("\n🧠 Key Timing Insights:")
            for step in timing_result['reasoning_trace']:
                if any(keyword in step for keyword in ['SIGNALS', 'REGIME', 'TIMING']):
                    print(f"  • {step}")
        else:
            print(f"❌ Timing analysis failed: {timing_result.get('error')}")
            return
        
        # Step 3: Portfolio Optimization
        print("\n💼 Step 3: Portfolio Optimization")
        print("-" * 40)
        
        portfolio_result = await portfolio_optimizer.optimize_portfolio(
            budget=75000,
            timeframe="Medium",
            risk_level="Medium",
            hitl_enabled=True
        )
        
        if portfolio_result['status'] == 'success':
            print("✅ Portfolio optimization completed")
            portfolio = portfolio_result['portfolio']
            print(f"📊 Positions: {len(portfolio['positions'])}")
            print(f"💰 Total invested: ${portfolio['total_investment']:,.2f}")
            print(f"📈 Expected return: {portfolio['expected_return']:.1f}%")
            print(f"🛡️ Risk score: {portfolio['risk_score']:.1f}/3.0")
            
            print("\n🏆 Top Holdings:")
            for pos in portfolio['positions'][:3]:
                print(f"  • {pos['symbol']}: {pos['allocation_percent']}% (${pos['investment_amount']:,.2f})")
            
            print("\n🧠 Key Optimization Insights:")
            for step in portfolio_result['reasoning_trace']:
                if any(keyword in step for keyword in ['OPTIMIZE', 'STRATEGY', 'ALLOCATION']):
                    print(f"  • {step}")
        else:
            print(f"❌ Portfolio optimization failed: {portfolio_result.get('error')}")
            return
        
        # Step 4: Compliance Monitoring
        print("\n🛡️ Step 4: Compliance Monitoring")
        print("-" * 40)
        
        compliance_result = await compliance_logger.monitor_compliance(
            monitoring_scope="full",
            hitl_enabled=True
        )
        
        if compliance_result['status'] == 'success':
            print("✅ Compliance monitoring completed")
            compliance_report = compliance_result['compliance_report']
            print(f"📊 Compliance score: {compliance_report['compliance_score']:.1f}/100")
            print(f"🚨 Total violations: {compliance_report['total_violations']}")
            print(f"📋 Status: {compliance_report['compliance_status']}")
            
            # Show violations by severity
            violations = compliance_report['violations_by_severity']
            print(f"🔴 High severity: {violations['high']}")
            print(f"🟡 Medium severity: {violations['medium']}")
            print(f"🟢 Low severity: {violations['low']}")
            
            print("\n🧠 Key Compliance Insights:")
            for step in compliance_result['reasoning_trace']:
                if any(keyword in step for keyword in ['VIOLATIONS', 'COMPLIANCE', 'RISK']):
                    print(f"  • {step}")
        else:
            print(f"❌ Compliance monitoring failed: {compliance_result.get('error')}")
            return
        
        # Step 5: Integrated Analysis Summary
        print("\n📋 Step 5: Integrated Analysis Summary")
        print("-" * 40)
        
        print("🎯 Multi-Agent Analysis Results:")
        print(f"  📊 Market Data Quality: {market_data['data_quality']['score']}/100")
        print(f"  ⏰ Market Timing: {timing_recs['overall_timing']}")
        print(f"  💼 Portfolio Expected Return: {portfolio['expected_return']:.1f}%")
        print(f"  🛡️ Compliance Score: {compliance_report['compliance_score']:.1f}/100")
        
        # Generate integrated recommendation
        overall_score = (
            market_data['data_quality']['score'] * 0.2 +
            timing_recs['confidence'] * 0.3 +
            (portfolio['expected_return'] * 5) * 0.3 +  # Scale return to 0-100
            compliance_report['compliance_score'] * 0.2
        )
        
        print(f"\n🏆 Overall System Confidence: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            recommendation = "PROCEED with portfolio implementation"
            print(f"✅ {recommendation}")
        elif overall_score >= 60:
            recommendation = "PROCEED with CAUTION - monitor closely"
            print(f"⚠️ {recommendation}")
        else:
            recommendation = "HOLD - address issues before proceeding"
            print(f"🚨 {recommendation}")
        
        # HITL Summary
        hitl_required = [
            market_data_result.get('hitl_required', False),
            timing_result.get('hitl_required', False),
            portfolio_result.get('hitl_required', False),
            compliance_result.get('hitl_required', False)
        ]
        
        print(f"\n👤 Human Reviews Required: {sum(hitl_required)}/4 agents")
        
        print("\n🎉 Multi-agent analysis workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")

async def example_agent_status_check():
    """Example: Check status of all agents"""
    print("\n🤖 Agent Status Check")
    print("=" * 40)
    
    agents = [
        ("Index Scraper", IndexScraperReActAgent()),
        ("Portfolio Optimizer", PortfolioOptimizerReActAgent()),
        ("Timing Advisor", TimingAdvisorReActAgent()),
        ("Compliance Logger", ComplianceLoggerReActAgent())
    ]
    
    for name, agent in agents:
        try:
            status = await agent.get_agent_status()
            print(f"\n{name}:")
            print(f"  Status: {status['status']}")
            print(f"  Version: {status['version']}")
            print(f"  Graph Nodes: {status['graph_nodes']}")
            print(f"  MCP Connected: {status.get('mcp_server_connected', 'N/A')}")
        except Exception as e:
            print(f"\n{name}: ❌ Error - {e}")

async def example_parallel_analysis():
    """Example: Run multiple agents in parallel"""
    print("\n⚡ Parallel Agent Analysis")
    print("=" * 40)
    
    # Initialize agents
    index_scraper = IndexScraperReActAgent()
    timing_advisor = TimingAdvisorReActAgent()
    compliance_logger = ComplianceLoggerReActAgent()
    
    # Run agents in parallel (independent operations)
    print("🚀 Starting parallel analysis...")
    
    tasks = [
        index_scraper.collect_market_data(['yahoo_finance'], 30, False),
        timing_advisor.analyze_market_timing("short", "medium", False),
        compliance_logger.monitor_compliance("portfolio", False)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("✅ Parallel analysis completed!")
    
    for i, (name, result) in enumerate([
        ("Market Data Collection", results[0]),
        ("Timing Analysis", results[1]),
        ("Compliance Monitoring", results[2])
    ]):
        if isinstance(result, Exception):
            print(f"❌ {name}: Error - {result}")
        elif result.get('status') == 'success':
            print(f"✅ {name}: Success")
        else:
            print(f"⚠️ {name}: {result.get('status', 'unknown')}")

async def example_audit_trail_analysis():
    """Example: Analyze audit trails across all agents"""
    print("\n📝 Audit Trail Analysis")
    print("=" * 40)
    
    audit_files = [
        ("Portfolio Optimizer", "data/portfolio_optimizer_audit.json"),
        ("Index Scraper", "data/index_scraper_audit.json"),
        ("Timing Advisor", "data/timing_advisor_audit.json"),
        ("Compliance Logger", "data/compliance_logger_audit.json")
    ]
    
    total_entries = 0
    
    for agent_name, file_path in audit_files:
        try:
            import os
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    audit_data = json.load(f)
                
                entries = len(audit_data)
                total_entries += entries
                
                print(f"{agent_name}: {entries} audit entries")
                
                if entries > 0:
                    latest = audit_data[-1]
                    print(f"  Latest: {latest.get('timestamp', 'unknown')}")
                    print(f"  Session: {latest.get('session_id', 'unknown')}")
            else:
                print(f"{agent_name}: No audit file found")
                
        except Exception as e:
            print(f"{agent_name}: Error reading audit - {e}")
    
    print(f"\nTotal audit entries across all agents: {total_entries}")

async def main():
    """Run all examples"""
    print("🎯 Multi-Agent Stock Analysis System Examples")
    print("=" * 70)
    
    try:
        # Run complete workflow
        await example_complete_workflow()
        
        # Check agent status
        await example_agent_status_check()
        
        # Demonstrate parallel processing
        await example_parallel_analysis()
        
        # Analyze audit trails
        await example_audit_trail_analysis()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 System Features Demonstrated:")
        print("  ✅ Multi-agent coordination and workflow")
        print("  ✅ ReAct reasoning with explicit thought traces")
        print("  ✅ Human-in-the-loop approval workflows")
        print("  ✅ Comprehensive audit logging and compliance")
        print("  ✅ Market data collection and quality assessment")
        print("  ✅ Technical analysis and market timing")
        print("  ✅ Portfolio optimization with Modern Portfolio Theory")
        print("  ✅ Regulatory compliance monitoring")
        print("  ✅ Parallel processing capabilities")
        print("  ✅ Integrated analysis and recommendations")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
Example: Human-in-the-Loop (HITL) Capabilities in LangGraph Agents
Demonstrates HITL decision points, approval workflow, and autonomous mode
"""

import asyncio
import json
from datetime import datetime

from agents.hitl_portfolio_optimizer import HITLPortfolioOptimizerAgent
from agents.hitl_timing_advisor import HITLTimingAdvisorAgent
from agents.hitl_compliance_logger import HITLComplianceLoggerAgent
from agents.hitl_index_scraper import HITLIndexScraperAgent
from agents.hitl_manager import hitl_manager, HITLStatus

async def example_hitl_portfolio_optimization():
    """Example: HITL-enabled portfolio optimization"""
    print("🚀 Example 1: HITL-Enabled Portfolio Optimization")
    print("=" * 60)
    
    agent = HITLPortfolioOptimizerAgent()
    
    # Enable HITL, disable autonomous mode
    agent.set_hitl_enabled(True)
    agent.set_autonomous_mode(False)
    
    # Run optimization with HITL enabled
    result = await agent.optimize_portfolio(
        budget=150000,  # Large budget to trigger HITL
        timeframe="Medium",
        risk_level="High",  # High risk to trigger HITL
        hitl_enabled=True,
        autonomous_mode=False
    )
    
    if result['status'] == 'success':
        print("✅ Portfolio optimization initiated")
        print(f"👤 HITL Required: {result['hitl_required']}")
        print(f"🔍 HITL Status: {result['hitl_status']}")
        print(f"🆔 HITL Decision ID: {result['hitl_decision_id']}")
        
        # Show pending decision
        decision_id = result['hitl_decision_id']
        if decision_id:
            decision = hitl_manager.get_decision(decision_id)
            if decision:
                print("\n📋 Pending Decision Details:")
                print(f"  • Type: {decision['decision_type']}")
                print(f"  • Description: {decision['description']}")
                print(f"  • Created: {decision['created_at']}")
                print(f"  • Timeout: {decision['timeout_seconds']} seconds")
                
                # Simulate human approval
                print("\n👤 Simulating human approval...")
                hitl_manager.approve_decision(decision_id, "Looks good, approved by human reviewer")
                
                # Check updated status
                updated_decision = hitl_manager.get_decision(decision_id)
                print(f"✅ Decision now {updated_decision['status']}")
                print(f"💬 Comments: {updated_decision['user_comments']}")
        
        # Show reasoning trace
        print("\n🧠 Key HITL Reasoning Steps:")
        for step in result['reasoning_trace']:
            if 'HITL' in step:
                print(f"  • {step}")
    else:
        print(f"❌ Optimization failed: {result.get('error')}")

async def example_autonomous_mode():
    """Example: Autonomous mode bypassing HITL"""
    print("\n🚀 Example 2: Autonomous Mode (HITL Bypass)")
    print("=" * 60)
    
    agent = HITLTimingAdvisorAgent()
    
    # Enable HITL, but also enable autonomous mode to bypass it
    agent.set_hitl_enabled(True)
    agent.set_autonomous_mode(True)
    
    # Run timing analysis with autonomous mode
    result = await agent.analyze_market_timing(
        timeframe="short",
        analysis_depth="advanced",
        hitl_enabled=True,
        autonomous_mode=True
    )
    
    if result['status'] == 'success':
        print("✅ Timing analysis completed automatically")
        print(f"👤 HITL Required: {result['hitl_required']}")
        print(f"🔍 HITL Status: {result['hitl_status']}")
        
        # Show reasoning trace
        print("\n🧠 Key Autonomous Mode Steps:")
        for step in result['reasoning_trace']:
            if 'HITL' in step or 'Autonomous' in step:
                print(f"  • {step}")
        
        # Show decision history
        decisions = hitl_manager.get_decision_history(agent.agent_id)
        if decisions:
            print("\n📋 Decision History:")
            for decision in decisions[:2]:
                print(f"  • {decision['decision_type']}: {decision['status']}")
                print(f"    {decision['description']}")
                print(f"    Created: {decision['created_at']}")
                if decision['status'] == 'bypassed':
                    print(f"    Reason: {decision['resolution_reason']}")
    else:
        print(f"❌ Timing analysis failed: {result.get('error')}")

async def example_hitl_rejection_workflow():
    """Example: HITL rejection and rework workflow"""
    print("\n🚀 Example 3: HITL Rejection Workflow")
    print("=" * 60)
    
    agent = HITLComplianceLoggerAgent()
    
    # Enable HITL, disable autonomous mode
    agent.set_hitl_enabled(True)
    agent.set_autonomous_mode(False)
    
    # Run compliance monitoring with HITL enabled
    result = await agent.monitor_compliance(
        monitoring_scope="full",
        hitl_enabled=True,
        autonomous_mode=False
    )
    
    if result['status'] == 'success':
        print("✅ Compliance monitoring initiated")
        print(f"👤 HITL Required: {result['hitl_required']}")
        print(f"🔍 HITL Status: {result['hitl_status']}")
        
        # Show pending decision
        decision_id = result['hitl_decision_id']
        if decision_id:
            decision = hitl_manager.get_decision(decision_id)
            if decision:
                print("\n📋 Pending Compliance Decision:")
                print(f"  • Type: {decision['decision_type']}")
                print(f"  • Description: {decision['description']}")
                
                # Simulate human rejection
                print("\n👤 Simulating human rejection...")
                hitl_manager.reject_decision(
                    decision_id, 
                    "Compliance report is incomplete, please include sector concentration analysis"
                )
                
                # Check updated status
                updated_decision = hitl_manager.get_decision(decision_id)
                print(f"❌ Decision now {updated_decision['status']}")
                print(f"💬 Feedback: {updated_decision['user_comments']}")
                
                print("\n🔄 In a real implementation, the agent would now:")
                print("  1. Process the rejection feedback")
                print("  2. Return to the violation detection phase")
                print("  3. Add the requested sector concentration analysis")
                print("  4. Generate a new compliance report")
                print("  5. Request HITL approval again")
    else:
        print(f"❌ Compliance monitoring failed: {result.get('error')}")

async def example_hitl_manager_overview():
    """Example: HITL Manager overview and capabilities"""
    print("\n🚀 Example 4: HITL Manager Overview")
    print("=" * 60)
    
    # Set global autonomous mode
    hitl_manager.set_global_autonomous_mode(False)
    print("✅ Global autonomous mode disabled")
    
    # Set agent-specific HITL overrides
    hitl_manager.set_agent_hitl_override("portfolio-optimizer", True)
    hitl_manager.set_agent_hitl_override("timing-advisor", True)
    hitl_manager.set_agent_hitl_override("compliance-logger", False)
    print("✅ Agent-specific HITL overrides configured")
    
    # Show pending decisions
    pending = hitl_manager.get_pending_decisions()
    print(f"\n📋 Pending Decisions: {len(pending)}")
    
    # Show decision history
    history = hitl_manager.get_decision_history(limit=5)
    print(f"📜 Decision History: {len(history)} entries")
    
    print("\n🔍 HITL Manager Capabilities:")
    print("  • Global autonomous mode toggle")
    print("  • Per-agent HITL override settings")
    print("  • Decision timeout management")
    print("  • Decision history and audit trail")
    print("  • Human feedback collection")
    print("  • Decision status tracking")

async def example_multi_agent_hitl_coordination():
    """Example: Multi-agent HITL coordination"""
    print("\n🚀 Example 5: Multi-Agent HITL Coordination")
    print("=" * 60)
    
    # Initialize all agents
    portfolio_agent = HITLPortfolioOptimizerAgent()
    timing_agent = HITLTimingAdvisorAgent()
    compliance_agent = HITLComplianceLoggerAgent()
    index_agent = HITLIndexScraperAgent()
    
    # Configure HITL settings
    for agent in [portfolio_agent, timing_agent, compliance_agent, index_agent]:
        agent.set_hitl_enabled(True)
        agent.set_autonomous_mode(False)
    
    print("✅ All agents configured with HITL enabled")
    
    # Simulate a multi-agent workflow
    print("\n🔄 Simulating multi-agent workflow with HITL coordination:")
    print("  1. Index Scraper collects market data")
    print("  2. Timing Advisor analyzes market conditions")
    print("  3. Portfolio Optimizer generates recommendations")
    print("  4. Compliance Logger validates regulatory compliance")
    
    print("\n👤 HITL Decision Points:")
    print("  • Market data quality issues → Human review")
    print("  • Extreme market conditions → Human review")
    print("  • High-risk portfolio allocations → Human review")
    print("  • Compliance violations → Human review")
    
    print("\n🔄 HITL Workflow Benefits:")
    print("  ✅ Human expertise at critical decision points")
    print("  ✅ Regulatory oversight and compliance")
    print("  ✅ Risk management for extreme market conditions")
    print("  ✅ Transparency and explainability")
    print("  ✅ Audit trail of human decisions")

async def main():
    """Run all examples"""
    print("🎯 Human-in-the-Loop (HITL) Capabilities in LangGraph Agents")
    print("=" * 70)
    
    try:
        await example_hitl_portfolio_optimization()
        await example_autonomous_mode()
        await example_hitl_rejection_workflow()
        await example_hitl_manager_overview()
        await example_multi_agent_hitl_coordination()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 Key HITL Features Demonstrated:")
        print("  ✅ Human approval workflow for critical decisions")
        print("  ✅ Autonomous mode to bypass HITL when appropriate")
        print("  ✅ Feedback loop for rejected decisions")
        print("  ✅ Decision history and audit trail")
        print("  ✅ Global and per-agent HITL configuration")
        print("  ✅ Multi-agent HITL coordination")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(main())
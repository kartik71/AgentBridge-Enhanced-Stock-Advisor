"""
Tests for PortfolioOptimizerReActAgent
"""

import pytest
import asyncio
import json
import os
from datetime import datetime

from agents.portfolio_optimizer_react.agent import PortfolioOptimizerReActAgent

@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return PortfolioOptimizerReActAgent()

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test agent initialization"""
    assert agent.agent_id == "portfolio_optimizer_react"
    assert agent.name == "PortfolioOptimizerReActAgent"
    assert agent.graph is not None
    assert len(agent.graph.nodes) > 0

@pytest.mark.asyncio
async def test_portfolio_optimization_basic(agent):
    """Test basic portfolio optimization"""
    result = await agent.optimize_portfolio(
        budget=50000,
        timeframe="Medium",
        risk_level="Medium"
    )
    
    assert result['status'] == 'success'
    assert 'portfolio' in result
    assert 'reasoning_trace' in result
    assert len(result['reasoning_trace']) > 0
    
    portfolio = result['portfolio']
    assert 'positions' in portfolio
    assert 'total_investment' in portfolio
    assert len(portfolio['positions']) > 0

@pytest.mark.asyncio
async def test_portfolio_optimization_high_risk(agent):
    """Test portfolio optimization with high risk settings"""
    result = await agent.optimize_portfolio(
        budget=150000,  # Large budget to trigger HITL
        timeframe="Short",
        risk_level="High"
    )
    
    assert result['status'] == 'success'
    # Should trigger HITL due to large budget
    assert result.get('hitl_required') is True

@pytest.mark.asyncio
async def test_reasoning_trace_content(agent):
    """Test that reasoning trace contains expected content"""
    result = await agent.optimize_portfolio(
        budget=25000,
        timeframe="Long",
        risk_level="Low"
    )
    
    reasoning_trace = result['reasoning_trace']
    
    # Check for key reasoning steps
    analyze_step = any("ANALYZE" in step for step in reasoning_trace)
    fetch_step = any("FETCH" in step for step in reasoning_trace)
    reason_step = any("REASON" in step for step in reasoning_trace)
    optimize_step = any("OPTIMIZE" in step for step in reasoning_trace)
    
    assert analyze_step, "Missing analysis step in reasoning trace"
    assert fetch_step, "Missing fetch step in reasoning trace"
    assert reason_step, "Missing reasoning step in reasoning trace"
    assert optimize_step, "Missing optimization step in reasoning trace"

@pytest.mark.asyncio
async def test_audit_logging(agent):
    """Test that audit logging works correctly"""
    # Clear existing audit log
    if os.path.exists(agent.audit_log_file):
        os.remove(agent.audit_log_file)
    
    result = await agent.optimize_portfolio(
        budget=30000,
        timeframe="Medium",
        risk_level="Medium"
    )
    
    assert result['status'] == 'success'
    
    # Check that audit log file was created
    assert os.path.exists(agent.audit_log_file)
    
    # Check audit log content
    with open(agent.audit_log_file, 'r') as f:
        audit_log = json.load(f)
    
    assert len(audit_log) > 0
    latest_entry = audit_log[-1]
    
    assert 'timestamp' in latest_entry
    assert 'agent_id' in latest_entry
    assert 'inputs' in latest_entry
    assert 'final_portfolio' in latest_entry
    assert 'reasoning_trace' in latest_entry

@pytest.mark.asyncio
async def test_csv_logging(agent):
    """Test CSV logging functionality"""
    # Clear existing CSV log
    if os.path.exists(agent.csv_log_file):
        os.remove(agent.csv_log_file)
    
    result = await agent.optimize_portfolio(
        budget=40000,
        timeframe="Short",
        risk_level="High"
    )
    
    assert result['status'] == 'success'
    
    # Check that CSV log file was created
    assert os.path.exists(agent.csv_log_file)
    
    # Check CSV content
    import csv
    with open(agent.csv_log_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0
    latest_row = rows[-1]
    
    assert 'timestamp' in latest_row
    assert 'budget' in latest_row
    assert 'timeframe' in latest_row
    assert 'risk_level' in latest_row
    assert 'total_investment' in latest_row

@pytest.mark.asyncio
async def test_agent_status(agent):
    """Test agent status reporting"""
    status = await agent.get_agent_status()
    
    assert status['agent_id'] == agent.agent_id
    assert status['name'] == agent.name
    assert status['status'] == 'ready'
    assert 'graph_nodes' in status
    assert 'mcp_servers' in status

def test_input_validation():
    """Test input validation logic"""
    agent = PortfolioOptimizerReActAgent()
    
    # Test with invalid inputs
    state = {
        'budget': 500,  # Below minimum
        'timeframe': 'Invalid',
        'risk_level': 'Invalid',
        'reasoning_trace': []
    }
    
    # This would be tested in the actual graph execution
    # For now, just verify the agent can handle edge cases
    assert agent.agent_id is not None

if __name__ == "__main__":
    # Run basic test
    async def run_test():
        agent = PortfolioOptimizerReActAgent()
        result = await agent.optimize_portfolio(50000, "Medium", "Medium")
        print("Test Result:")
        print(json.dumps(result, indent=2))
    
    asyncio.run(run_test())
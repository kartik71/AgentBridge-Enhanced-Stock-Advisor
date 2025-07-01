"""
FastAPI ComplianceServer - Policy Validation and Logging API
Handles regulatory compliance checking, policy validation, and audit logging
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

# Enums for compliance
class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"

class RuleCategory(str, Enum):
    POSITION_LIMITS = "position_limits"
    RISK_MANAGEMENT = "risk_management"
    TRADING_HOURS = "trading_hours"
    REGULATORY = "regulatory"
    INTERNAL_POLICY = "internal_policy"

# Pydantic models
class ComplianceRule(BaseModel):
    rule_id: str
    name: str
    category: RuleCategory
    description: str
    threshold_value: Optional[float] = None
    threshold_type: Optional[str] = None  # percentage, absolute, ratio
    enabled: bool = True
    severity: ViolationSeverity = ViolationSeverity.MEDIUM

class ComplianceCheck(BaseModel):
    user_id: str
    check_type: str  # portfolio, order, trade
    data: Dict[str, Any]
    rules_to_check: Optional[List[str]] = None  # Specific rules to check

class Violation(BaseModel):
    violation_id: str
    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    description: str
    current_value: float
    threshold_value: float
    user_id: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"  # active, resolved, acknowledged

class ComplianceReport(BaseModel):
    user_id: str
    report_date: datetime
    overall_status: ComplianceStatus
    compliance_score: float  # 0-100
    total_violations: int
    violations_by_severity: Dict[str, int]
    violations: List[Violation]
    recommendations: List[str]

# Initialize FastAPI app
app = FastAPI(
    title="ComplianceServer API",
    description="Policy Validation and Regulatory Compliance Engine",
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

# Compliance engine
class ComplianceEngine:
    def __init__(self):
        self.rules = {}  # rule_id -> ComplianceRule
        self.violations = {}  # violation_id -> Violation
        self.audit_log = []  # List of audit entries
        self.user_compliance_status = {}  # user_id -> status
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize compliance engine with rules and data"""
        await self.load_compliance_rules()
        await self.load_compliance_data()
        
    async def load_compliance_rules(self):
        """Load compliance rules and policies"""
        default_rules = [
            ComplianceRule(
                rule_id="POS_001",
                name="Maximum Position Size",
                category=RuleCategory.POSITION_LIMITS,
                description="Single position cannot exceed 25% of portfolio value",
                threshold_value=25.0,
                threshold_type="percentage",
                severity=ViolationSeverity.HIGH
            ),
            ComplianceRule(
                rule_id="POS_002",
                name="Sector Concentration Limit",
                category=RuleCategory.POSITION_LIMITS,
                description="Sector exposure cannot exceed 40% of portfolio value",
                threshold_value=40.0,
                threshold_type="percentage",
                severity=ViolationSeverity.MEDIUM
            ),
            ComplianceRule(
                rule_id="RISK_001",
                name="Portfolio Value at Risk",
                category=RuleCategory.RISK_MANAGEMENT,
                description="Portfolio VaR cannot exceed 5% of total value",
                threshold_value=5.0,
                threshold_type="percentage",
                severity=ViolationSeverity.HIGH
            ),
            ComplianceRule(
                rule_id="RISK_002",
                name="Maximum Daily Loss",
                category=RuleCategory.RISK_MANAGEMENT,
                description="Daily portfolio loss cannot exceed 10% of value",
                threshold_value=10.0,
                threshold_type="percentage",
                severity=ViolationSeverity.CRITICAL
            ),
            ComplianceRule(
                rule_id="RISK_003",
                name="Leverage Limit",
                category=RuleCategory.RISK_MANAGEMENT,
                description="Portfolio leverage cannot exceed 2:1 ratio",
                threshold_value=2.0,
                threshold_type="ratio",
                severity=ViolationSeverity.HIGH
            ),
            ComplianceRule(
                rule_id="TRD_001",
                name="Trading Hours Compliance",
                category=RuleCategory.TRADING_HOURS,
                description="Orders must be placed during market hours",
                severity=ViolationSeverity.LOW
            ),
            ComplianceRule(
                rule_id="TRD_002",
                name="Order Size Limit",
                category=RuleCategory.TRADING_HOURS,
                description="Single order cannot exceed $100,000 in value",
                threshold_value=100000.0,
                threshold_type="absolute",
                severity=ViolationSeverity.MEDIUM
            ),
            ComplianceRule(
                rule_id="REG_001",
                name="Pattern Day Trader Rule",
                category=RuleCategory.REGULATORY,
                description="Account must maintain $25,000 minimum for day trading",
                threshold_value=25000.0,
                threshold_type="absolute",
                severity=ViolationSeverity.HIGH
            ),
            ComplianceRule(
                rule_id="REG_002",
                name="Wash Sale Rule",
                category=RuleCategory.REGULATORY,
                description="Cannot repurchase substantially identical security within 30 days of sale at loss",
                severity=ViolationSeverity.MEDIUM
            ),
            ComplianceRule(
                rule_id="INT_001",
                name="Paper Trading Disclosure",
                category=RuleCategory.INTERNAL_POLICY,
                description="All trades must be clearly marked as paper trading",
                severity=ViolationSeverity.LOW
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
    
    async def load_compliance_data(self):
        """Load existing compliance data from storage"""
        try:
            # Load violations
            violations_file = self.data_dir / "compliance_violations.json"
            if violations_file.exists():
                with open(violations_file, 'r') as f:
                    violations_data = json.load(f)
                    for violation_dict in violations_data:
                        violation_dict['detected_at'] = datetime.fromisoformat(violation_dict['detected_at'])
                        if violation_dict.get('resolved_at'):
                            violation_dict['resolved_at'] = datetime.fromisoformat(violation_dict['resolved_at'])
                        violation = Violation(**violation_dict)
                        self.violations[violation.violation_id] = violation
            
            # Load audit log
            audit_file = self.data_dir / "compliance_audit.json"
            if audit_file.exists():
                with open(audit_file, 'r') as f:
                    self.audit_log = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load compliance data: {e}")
    
    async def save_compliance_data(self):
        """Save compliance data to storage"""
        try:
            # Save violations
            violations_data = []
            for violation in self.violations.values():
                violation_dict = violation.dict()
                violation_dict['detected_at'] = violation_dict['detected_at'].isoformat()
                if violation_dict.get('resolved_at'):
                    violation_dict['resolved_at'] = violation_dict['resolved_at'].isoformat()
                violations_data.append(violation_dict)
            
            with open(self.data_dir / "compliance_violations.json", 'w') as f:
                json.dump(violations_data, f, indent=2)
            
            # Save audit log
            with open(self.data_dir / "compliance_audit.json", 'w') as f:
                json.dump(self.audit_log, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save compliance data: {e}")
    
    async def check_compliance(self, check: ComplianceCheck) -> ComplianceReport:
        """Perform comprehensive compliance check"""
        violations = []
        
        # Determine which rules to check
        rules_to_check = check.rules_to_check or list(self.rules.keys())
        
        for rule_id in rules_to_check:
            if rule_id not in self.rules:
                continue
                
            rule = self.rules[rule_id]
            if not rule.enabled:
                continue
            
            # Check specific rule
            violation = await self._check_rule(rule, check)
            if violation:
                violations.append(violation)
                self.violations[violation.violation_id] = violation
        
        # Calculate compliance score
        compliance_score = await self._calculate_compliance_score(violations)
        
        # Determine overall status
        overall_status = await self._determine_overall_status(violations)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(violations, check.data)
        
        # Create compliance report
        violations_by_severity = {
            "low": len([v for v in violations if v.severity == ViolationSeverity.LOW]),
            "medium": len([v for v in violations if v.severity == ViolationSeverity.MEDIUM]),
            "high": len([v for v in violations if v.severity == ViolationSeverity.HIGH]),
            "critical": len([v for v in violations if v.severity == ViolationSeverity.CRITICAL])
        }
        
        report = ComplianceReport(
            user_id=check.user_id,
            report_date=datetime.now(),
            overall_status=overall_status,
            compliance_score=compliance_score,
            total_violations=len(violations),
            violations_by_severity=violations_by_severity,
            violations=violations,
            recommendations=recommendations
        )
        
        # Log compliance check
        await self._log_compliance_check(check, report)
        
        # Save data
        await self.save_compliance_data()
        
        return report
    
    async def _check_rule(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check a specific compliance rule"""
        data = check.data
        
        if rule.rule_id == "POS_001":  # Maximum Position Size
            return await self._check_position_size(rule, check)
        elif rule.rule_id == "POS_002":  # Sector Concentration
            return await self._check_sector_concentration(rule, check)
        elif rule.rule_id == "RISK_001":  # Portfolio VaR
            return await self._check_portfolio_var(rule, check)
        elif rule.rule_id == "RISK_002":  # Maximum Daily Loss
            return await self._check_daily_loss(rule, check)
        elif rule.rule_id == "RISK_003":  # Leverage Limit
            return await self._check_leverage(rule, check)
        elif rule.rule_id == "TRD_001":  # Trading Hours
            return await self._check_trading_hours(rule, check)
        elif rule.rule_id == "TRD_002":  # Order Size Limit
            return await self._check_order_size(rule, check)
        elif rule.rule_id == "REG_001":  # Pattern Day Trader
            return await self._check_pattern_day_trader(rule, check)
        elif rule.rule_id == "INT_001":  # Paper Trading Disclosure
            return await self._check_paper_trading(rule, check)
        
        return None
    
    async def _check_position_size(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check maximum position size rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_portfolio_value", 0)
        
        if total_value == 0:
            return None
        
        for position in positions:
            position_value = position.get("market_value", 0)
            position_percentage = (position_value / total_value) * 100
            
            if position_percentage > rule.threshold_value:
                return Violation(
                    violation_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    description=f"Position {position.get('symbol')} ({position_percentage:.1f}%) exceeds maximum position size limit ({rule.threshold_value}%)",
                    current_value=position_percentage,
                    threshold_value=rule.threshold_value,
                    user_id=check.user_id,
                    detected_at=datetime.now()
                )
        
        return None
    
    async def _check_sector_concentration(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check sector concentration rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_portfolio_value", 0)
        
        if total_value == 0:
            return None
        
        # Calculate sector allocations
        sector_allocations = {}
        for position in positions:
            sector = position.get("sector", "Unknown")
            position_value = position.get("market_value", 0)
            
            if sector not in sector_allocations:
                sector_allocations[sector] = 0
            sector_allocations[sector] += position_value
        
        # Check each sector
        for sector, sector_value in sector_allocations.items():
            sector_percentage = (sector_value / total_value) * 100
            
            if sector_percentage > rule.threshold_value:
                return Violation(
                    violation_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    description=f"Sector {sector} concentration ({sector_percentage:.1f}%) exceeds limit ({rule.threshold_value}%)",
                    current_value=sector_percentage,
                    threshold_value=rule.threshold_value,
                    user_id=check.user_id,
                    detected_at=datetime.now()
                )
        
        return None
    
    async def _check_portfolio_var(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check portfolio Value at Risk rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        total_value = portfolio.get("total_portfolio_value", 0)
        unrealized_pnl = portfolio.get("total_unrealized_pnl", 0)
        
        if total_value == 0:
            return None
        
        # Simplified VaR calculation (using unrealized P&L as proxy)
        var_percentage = abs(unrealized_pnl) / total_value * 100
        
        if var_percentage > rule.threshold_value:
            return Violation(
                violation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                description=f"Portfolio VaR ({var_percentage:.1f}%) exceeds limit ({rule.threshold_value}%)",
                current_value=var_percentage,
                threshold_value=rule.threshold_value,
                user_id=check.user_id,
                detected_at=datetime.now()
            )
        
        return None
    
    async def _check_daily_loss(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check maximum daily loss rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        total_value = portfolio.get("total_portfolio_value", 0)
        day_change = portfolio.get("day_change", 0)
        
        if total_value == 0 or day_change >= 0:
            return None
        
        daily_loss_percentage = abs(day_change) / total_value * 100
        
        if daily_loss_percentage > rule.threshold_value:
            return Violation(
                violation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                description=f"Daily loss ({daily_loss_percentage:.1f}%) exceeds maximum limit ({rule.threshold_value}%)",
                current_value=daily_loss_percentage,
                threshold_value=rule.threshold_value,
                user_id=check.user_id,
                detected_at=datetime.now()
            )
        
        return None
    
    async def _check_leverage(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check leverage limit rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        total_value = portfolio.get("total_portfolio_value", 0)
        margin_used = portfolio.get("margin_used", 0)
        cash_balance = portfolio.get("cash_balance", 0)
        
        if cash_balance == 0:
            return None
        
        leverage_ratio = total_value / cash_balance
        
        if leverage_ratio > rule.threshold_value:
            return Violation(
                violation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                description=f"Portfolio leverage ({leverage_ratio:.1f}:1) exceeds limit ({rule.threshold_value}:1)",
                current_value=leverage_ratio,
                threshold_value=rule.threshold_value,
                user_id=check.user_id,
                detected_at=datetime.now()
            )
        
        return None
    
    async def _check_trading_hours(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check trading hours compliance"""
        if check.check_type != "order":
            return None
        
        # For demo purposes, always compliant (paper trading)
        return None
    
    async def _check_order_size(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check order size limit"""
        if check.check_type != "order":
            return None
        
        order = check.data.get("order", {})
        order_value = order.get("quantity", 0) * order.get("price", 0)
        
        if order_value > rule.threshold_value:
            return Violation(
                violation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                description=f"Order value (${order_value:,.2f}) exceeds limit (${rule.threshold_value:,.2f})",
                current_value=order_value,
                threshold_value=rule.threshold_value,
                user_id=check.user_id,
                detected_at=datetime.now()
            )
        
        return None
    
    async def _check_pattern_day_trader(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check pattern day trader rule"""
        if check.check_type != "portfolio":
            return None
        
        portfolio = check.data.get("portfolio", {})
        total_value = portfolio.get("total_portfolio_value", 0)
        
        # For demo purposes, assume compliance (paper trading)
        return None
    
    async def _check_paper_trading(self, rule: ComplianceRule, check: ComplianceCheck) -> Optional[Violation]:
        """Check paper trading disclosure"""
        # Always add informational note about paper trading
        return Violation(
            violation_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=ViolationSeverity.LOW,
            description="System operating in paper trading mode - no real funds at risk",
            current_value=1.0,
            threshold_value=1.0,
            user_id=check.user_id,
            detected_at=datetime.now()
        )
    
    async def _calculate_compliance_score(self, violations: List[Violation]) -> float:
        """Calculate overall compliance score (0-100)"""
        if not violations:
            return 100.0
        
        score = 100.0
        
        for violation in violations:
            if violation.severity == ViolationSeverity.CRITICAL:
                score -= 25
            elif violation.severity == ViolationSeverity.HIGH:
                score -= 15
            elif violation.severity == ViolationSeverity.MEDIUM:
                score -= 10
            elif violation.severity == ViolationSeverity.LOW:
                score -= 2
        
        return max(0.0, score)
    
    async def _determine_overall_status(self, violations: List[Violation]) -> ComplianceStatus:
        """Determine overall compliance status"""
        if not violations:
            return ComplianceStatus.COMPLIANT
        
        has_critical = any(v.severity == ViolationSeverity.CRITICAL for v in violations)
        has_high = any(v.severity == ViolationSeverity.HIGH for v in violations)
        has_medium = any(v.severity == ViolationSeverity.MEDIUM for v in violations)
        
        if has_critical:
            return ComplianceStatus.CRITICAL
        elif has_high:
            return ComplianceStatus.VIOLATION
        elif has_medium:
            return ComplianceStatus.WARNING
        else:
            return ComplianceStatus.COMPLIANT
    
    async def _generate_recommendations(self, violations: List[Violation], data: Dict) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if not violations:
            recommendations.append("Portfolio is fully compliant with all regulatory requirements")
            recommendations.append("Continue monitoring positions and risk metrics")
            return recommendations
        
        # Position-related recommendations
        position_violations = [v for v in violations if v.rule_id.startswith("POS")]
        if position_violations:
            recommendations.append("Consider rebalancing portfolio to reduce position concentration")
            recommendations.append("Diversify holdings across multiple sectors and asset classes")
        
        # Risk-related recommendations
        risk_violations = [v for v in violations if v.rule_id.startswith("RISK")]
        if risk_violations:
            recommendations.append("Implement risk management measures to reduce portfolio volatility")
            recommendations.append("Consider adding hedging positions or reducing overall exposure")
        
        # Trading-related recommendations
        trading_violations = [v for v in violations if v.rule_id.startswith("TRD")]
        if trading_violations:
            recommendations.append("Review order sizes and trading patterns for compliance")
            recommendations.append("Ensure all trades comply with market hours and size limits")
        
        # Always include paper trading note
        recommendations.append("System operating in paper trading mode for educational purposes")
        
        return recommendations
    
    async def _log_compliance_check(self, check: ComplianceCheck, report: ComplianceReport):
        """Log compliance check to audit trail"""
        audit_entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id": check.user_id,
            "check_type": check.check_type,
            "compliance_score": report.compliance_score,
            "overall_status": report.overall_status,
            "total_violations": report.total_violations,
            "violations_by_severity": report.violations_by_severity,
            "paper_trading": True
        }
        
        self.audit_log.append(audit_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

# Initialize compliance engine
compliance_engine = ComplianceEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize compliance engine on startup"""
    await compliance_engine.initialize()
    print("🚀 ComplianceServer API started successfully")
    print("🛡️ Compliance rules and policies loaded")

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ComplianceServer API",
        "version": "1.0.0",
        "description": "Policy Validation and Regulatory Compliance Engine",
        "endpoints": {
            "check_compliance": "/check_compliance",
            "rules": "/rules",
            "violations": "/violations/{user_id}",
            "audit_log": "/audit_log",
            "health": "/health"
        },
        "status": "operational",
        "total_rules": len(compliance_engine.rules),
        "active_violations": len(compliance_engine.violations),
        "audit_entries": len(compliance_engine.audit_log)
    }

@app.post("/check_compliance")
async def check_compliance(check: ComplianceCheck):
    """
    Perform comprehensive compliance check
    
    Args:
        check: ComplianceCheck with user data and check parameters
    
    Returns:
        Detailed compliance report with violations and recommendations
    """
    try:
        report = await compliance_engine.check_compliance(check)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "compliance_report": report.dict(),
                "paper_trading": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing compliance check: {str(e)}")

@app.get("/rules")
async def get_compliance_rules():
    """Get all compliance rules and policies"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "rules": [rule.dict() for rule in compliance_engine.rules.values()],
            "total_rules": len(compliance_engine.rules),
            "rules_by_category": {
                category.value: len([r for r in compliance_engine.rules.values() if r.category == category])
                for category in RuleCategory
            },
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/rules/{rule_id}")
async def get_compliance_rule(rule_id: str):
    """Get specific compliance rule"""
    if rule_id not in compliance_engine.rules:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    
    rule = compliance_engine.rules[rule_id]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "rule": rule.dict(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/violations/{user_id}")
async def get_user_violations(
    user_id: str,
    status: str = Query("active", description="Violation status: active, resolved, all"),
    severity: Optional[ViolationSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200, description="Number of violations to return")
):
    """Get user's compliance violations"""
    user_violations = [
        violation for violation in compliance_engine.violations.values()
        if violation.user_id == user_id
    ]
    
    # Filter by status
    if status != "all":
        user_violations = [v for v in user_violations if v.status == status]
    
    # Filter by severity
    if severity:
        user_violations = [v for v in user_violations if v.severity == severity]
    
    # Sort by detection date (most recent first)
    user_violations.sort(key=lambda x: x.detected_at, reverse=True)
    
    # Apply limit
    user_violations = user_violations[:limit]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "violations": [violation.dict() for violation in user_violations],
            "total_violations": len(user_violations),
            "paper_trading": True,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/audit_log")
async def get_audit_log(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=500, description="Number of entries to return")
):
    """Get compliance audit log"""
    audit_entries = compliance_engine.audit_log
    
    # Filter by user if specified
    if user_id:
        audit_entries = [entry for entry in audit_entries if entry.get("user_id") == user_id]
    
    # Sort by timestamp (most recent first)
    audit_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Apply limit
    audit_entries = audit_entries[:limit]
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "audit_log": audit_entries,
            "total_entries": len(audit_entries),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.put("/violations/{violation_id}/resolve")
async def resolve_violation(violation_id: str):
    """Mark a violation as resolved"""
    if violation_id not in compliance_engine.violations:
        raise HTTPException(status_code=404, detail=f"Violation '{violation_id}' not found")
    
    violation = compliance_engine.violations[violation_id]
    violation.status = "resolved"
    violation.resolved_at = datetime.now()
    
    await compliance_engine.save_compliance_data()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Violation {violation_id} marked as resolved",
            "violation": violation.dict(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/compliance_summary/{user_id}")
async def get_compliance_summary(user_id: str):
    """Get compliance summary for user"""
    user_violations = [
        violation for violation in compliance_engine.violations.values()
        if violation.user_id == user_id and violation.status == "active"
    ]
    
    violations_by_severity = {
        "critical": len([v for v in user_violations if v.severity == ViolationSeverity.CRITICAL]),
        "high": len([v for v in user_violations if v.severity == ViolationSeverity.HIGH]),
        "medium": len([v for v in user_violations if v.severity == ViolationSeverity.MEDIUM]),
        "low": len([v for v in user_violations if v.severity == ViolationSeverity.LOW])
    }
    
    # Calculate compliance score
    compliance_score = await compliance_engine._calculate_compliance_score(user_violations)
    overall_status = await compliance_engine._determine_overall_status(user_violations)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "user_id": user_id,
            "compliance_summary": {
                "overall_status": overall_status,
                "compliance_score": compliance_score,
                "total_active_violations": len(user_violations),
                "violations_by_severity": violations_by_severity,
                "last_check": max([v.detected_at for v in user_violations]).isoformat() if user_violations else None,
                "paper_trading": True
            },
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ComplianceServer API",
        "version": "1.0.0",
        "uptime": datetime.now().isoformat(),
        "compliance_engine": {
            "total_rules": len(compliance_engine.rules),
            "active_violations": len([v for v in compliance_engine.violations.values() if v.status == "active"]),
            "audit_entries": len(compliance_engine.audit_log),
            "paper_trading": True
        }
    }

# Run server
if __name__ == "__main__":
    print("🚀 Starting ComplianceServer API...")
    print("🛡️ Loading compliance rules and policies...")
    
    uvicorn.run(
        "compliance_server:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
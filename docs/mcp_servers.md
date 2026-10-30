# MCP Servers Layer Documentation

## Overview

The MCP (Model Context Protocol) servers layer provides standardized access to data and decision-making tools for AI agents. Four specialized servers handle distinct responsibilities:

1. **ApplicantDB MCP** - Applicant profile and history queries
2. **RiskRulesDB MCP** - Risk thresholds and classification rules
3. **DecisionSynthesis MCP** - Decision logic and risk scoring
4. **NotificationSystem MCP** - Notifications, audit logging, and case management

Each server is independent and can run in separate processes, enabling horizontal scaling.

---

## Architecture

### Design Principles

- **Isolation**: Each server handles one domain; agents call servers via standardized tools
- **Fault Tolerance**: Server failures don't crash agents; failures are logged and handled gracefully
- **Observability**: All tool calls are logged with trace_id for debugging
- **Consistency**: All servers follow the same `BaseMCPServer` pattern
- **Auditability**: All decisions and notifications are persisted in audit logs

### Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestration                       │
│  (Applicant Profile, Financial Risk, Decision, Compliance)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                  ┌───────────┼───────────┐
                  │           │           │
                  ▼           ▼           ▼
        ┌──────────────────────────────────────────┐
        │      MCP Servers (HTTP or Stdio)        │
        ├──────────────────────────────────────────┤
        │ • ApplicantDB      (localhost:8001)      │
        │ • RiskRulesDB      (localhost:8002)      │
        │ • DecisionSynthesis (localhost:8003)     │
        │ • NotificationSystem (localhost:8004)    │
        └──────────────────────────────────────────┘
                  │           │           │
                  ▼           ▼           ▼
        ┌──────────────────────────────────────────┐
        │         Persistent Data Layer            │
        ├──────────────────────────────────────────┤
        │ • SQLite (applicants, employment, etc)  │
        │ • Risk rules & thresholds (cached)       │
        │ • Audit trail (immutable)                │
        │ • Notifications & cases                  │
        └──────────────────────────────────────────┘
```

---

## Server Specifications

### 1. ApplicantDB MCP Server

**Responsibility:** Provide access to applicant profile and history data.

**Tools:**

#### `get_applicant_history(applicant_id: str) -> Dict`

Returns complete applicant profile and employment history.

**Returns:**
```python
{
    "applicant": {
        "id": str,
        "age": int,
        "income": float,
        "employment_type": str,
        "credit_score": int,
        "location": str,
    },
    "employment_history": [
        {
            "job_title": str,
            "company": str,
            "start_date": ISO8601,
            "end_date": ISO8601 | null,
            "tenure_months": int,
        },
        ...
    ],
    "tenure_years": float,
    "recent_gap_months": int,
}
```

**Use case:** Applicant Profile Agent uses this to assess employment stability and tenure.

#### `get_employment_data(applicant_id: str) -> Dict`

Returns detailed employment metrics including stability score and job change frequency.

**Returns:**
```python
{
    "applicant_id": str,
    "jobs": [...],
    "current_tenure_months": int,
    "total_jobs": int,
    "employment_gaps": [{"months": int}, ...],
    "stability_score": int,  # 0-100
    "status": "STABLE" | "MODERATE" | "UNSTABLE",
}
```

**Use case:** Detect employment instability patterns and flag high-risk profiles.

#### `get_credit_inquiries(applicant_id: str) -> Dict`

Returns credit inquiry history for anomaly detection.

**Returns:**
```python
{
    "applicant_id": str,
    "inquiries": [
        {
            "date": ISO8601,
            "type": str,  # "hard", "soft", etc
            "notes": str,
        },
        ...
    ],
    "recent_inquiries_3m": int,
    "inquiry_types": {"hard": 2, "soft": 1},
    "anomaly_flag": bool,  # True if > 3 inquiries in 90 days
}
```

**Use case:** Detect multiple credit applications (anomaly indicator).

---

### 2. RiskRulesDB MCP Server

**Responsibility:** Provide risk classification rules and decision thresholds.

**Tools:**

#### `get_risk_thresholds() -> Dict`

Returns current DTI, credit score, and LTI classification thresholds.

**Returns:**
```python
{
    "dti_favorable_max": 0.36,
    "dti_acceptable_max": 0.50,
    "dti_borderline_max": 0.63,
    "credit_excellent_min": 750,
    "credit_good_min": 700,
    "credit_fair_min": 650,
    "credit_poor_min": 550,
    "lti_favorable_max": 2.5,
    "lti_acceptable_max": 4.0,
    "lti_high_risk_min": 4.0,
}
```

**Use case:** Financial Risk Agent uses thresholds to classify applicant metrics.

#### `get_anomaly_rules() -> Dict`

Returns rules for detecting financial anomalies.

**Returns:**
```python
{
    "income_spike_threshold": 1.5,  # 150% = anomaly
    "employment_gap_months_threshold": 6,
    "credit_inquiries_3m_threshold": 3,
    "liabilities_spike_threshold": 1.3,
    "rules": [
        {
            "name": "income_spike",
            "description": "Income increased >150%",
            "action": "FLAG",
            "severity": "MEDIUM",
        },
        ...
    ],
}
```

**Use case:** Applicant Profile Agent and Financial Risk Agent use anomaly rules to flag suspicious patterns.

#### `classify_by_rules(dti: float, credit_score: int, lti: float) -> Dict`

Classify applicant metrics against current rules.

**Returns:**
```python
{
    "dti": {
        "value": 0.35,
        "classification": "FAVORABLE" | "ACCEPTABLE" | "BORDERLINE" | "HIGH_RISK",
    },
    "credit_score": {
        "value": 745,
        "classification": "EXCELLENT" | "GOOD" | "FAIR" | "POOR" | "VERY_POOR",
        "risk_level": "LOW" | "MODERATE" | "MEDIUM" | "HIGH" | "VERY_HIGH",
    },
    "lti": {
        "value": 2.8,
        "classification": "FAVORABLE" | "ACCEPTABLE" | "HIGH_RISK",
    },
}
```

**Use case:** Financial Risk Agent uses this to get consistent classifications.

---

### 3. DecisionSynthesis MCP Server

**Responsibility:** Provide decision logic, policy rules, and risk scoring.

**Tools:**

#### `get_decision_policy() -> Dict`

Returns approval, rejection, and manual review criteria.

**Returns:**
```python
{
    "approval_criteria": {
        "all_required": [
            "credit_score >= 750",
            "dti < 0.36",
            "lti < 2.5",
            "employment_risk == LOW",
            "anomaly_detected == false",
        ],
        "description": "All criteria must be true to auto-approve",
    },
    "rejection_criteria": {
        "any_trigger": [
            "credit_score < 550",
            "dti > 0.63",
            "lti > 4.0",
            "employment_type == Unemployed AND income_stability < 50",
        ],
        "description": "Any criterion triggers auto-reject",
    },
    "manual_review_criteria": {
        "any_trigger": [
            "confidence < 0.75",
            "dti in range (0.50, 0.63)",
            "anomaly_score > 0.5",
            "age < 21 OR age > 70 WITH strong_other_factors",
            "recent_employment_gap > 6",
        ],
        "description": "Any criterion routes to manual review",
    },
}
```

**Use case:** Loan Decision Agent uses this policy to route applications.

#### `score_applicant(credit_score, dti, lti, income_stability, employment_risk, anomaly_score) -> Dict`

Calculate composite risk score based on weighted metrics.

**Returns:**
```python
{
    "risk_score": 35,  # 0 (safest) to 100 (riskiest)
    "components": {
        "credit_score": 25,
        "dti": 30,
        "lti": 15,
        "income_stability": 20,
        "employment_risk": 10,
        "anomaly": 5,
    },
    "weights": {
        "credit": 0.35,
        "dti": 0.25,
        "lti": 0.15,
        "income_stability": 0.10,
        "employment": 0.10,
        "anomaly": 0.05,
    },
    "interpretation": "Low Risk",
}
```

**Use case:** Loan Decision Agent uses risk score for confidence and explanation.

---

### 4. NotificationSystem MCP Server

**Responsibility:** Manage notifications, case creation, and audit logging.

**Tools:**

#### `send_notification(applicant_id, case_id, notification_type, message) -> Dict`

Send notification to applicant (email, SMS, letter).

**Returns:**
```python
{
    "status": "SENT" | "PENDING" | "FAILED",
    "notification_id": str,
    "sent_at": ISO8601,
    "applicant_id": str,
    "case_id": str,
}
```

**Use case:** Compliance Agent uses this to notify applicants of decisions.

#### `create_case(trace_id, applicant_id, decision, action_taken) -> Dict`

Create immutable case record for audit trail.

**Returns:**
```python
{
    "case_id": "CASE-2026-10-29-00001",
    "trace_id": str,
    "applicant_id": str,
    "decision": "APPROVED" | "REJECTED" | "REQUIRES_REVIEW",
    "created_at": ISO8601,
}
```

**Use case:** Compliance Agent creates case for each application.

#### `write_audit_log(trace_id, case_id, applicant_id, decision, risk_score, confidence, explanation, agents_run, decision_factors) -> Dict`

Write immutable audit log entry (never updated/deleted).

**Returns:**
```python
{
    "audit_id": int,
    "trace_id": str,
    "case_id": str,
    "applicant_id": str,
    "status": "LOGGED",
    "created_at": ISO8601,
}
```

**Use case:** Compliance Agent logs all decisions for regulatory compliance.

---

## Base MCP Server Implementation

All servers inherit from `BaseMCPServer` which provides:

- **Tool Registration**: `register_tools([(name, func), ...])`
- **Error Handling**: Wraps all tools with exception handling and logging
- **Database Session Management**: `get_session()` for connection pooling
- **Response Formatting**: `format_response(data, status, error)`
- **Health Checks**: `health_check()` for server monitoring

### Example: Implementing a Custom Server

```python
from src.mcp_servers.base import BaseMCPServer

class CustomServer(BaseMCPServer):
    def __init__(self):
        super().__init__()
        self.mcp_name = "custom_server"
        
        # Register tools
        self.register_tools([
            ("get_data", self.get_data),
            ("process_data", self.process_data),
        ])
    
    @staticmethod
    def get_data(key: str) -> Dict[str, Any]:
        """Get data by key."""
        return {"key": key, "value": "..."}
    
    @staticmethod
    def process_data(data: Dict) -> Dict[str, Any]:
        """Process data and return result."""
        return {"processed": data}

# Start server
server = CustomServer()
server.run_server(port=8005)
```

---

## Running MCP Servers

### Option 1: Individual Servers (Development)

Start each server in separate terminals:

```bash
# Terminal 1: ApplicantDB
python -m src.mcp_servers.applicant_db

# Terminal 2: RiskRulesDB
python -m src.mcp_servers.risk_rules_db

# Terminal 3: DecisionSynthesis
python -m src.mcp_servers.decision_synthesis

# Terminal 4: NotificationSystem
python -m src.mcp_servers.notification_system
```

### Option 2: Docker Compose (Production)

```bash
# Start all MCP servers
docker-compose -f docker-compose.yml up mcp_applicant_db mcp_risk_rules_db \
  mcp_decision_synthesis mcp_notification_system

# View logs
docker-compose logs -f mcp_applicant_db
```

### Option 3: Programmatically

```python
from src.mcp_servers.applicant_db import ApplicantDBServer
from src.mcp_servers.risk_rules_db import RiskRulesDBServer

# Start servers
applicant_server = ApplicantDBServer()
risk_server = RiskRulesDBServer()

# Run in background (in production, use process manager)
import threading
threading.Thread(target=applicant_server.run_server, kwargs={"port": 8001}).start()
threading.Thread(target=risk_server.run_server, kwargs={"port": 8002}).start()
```

---

## Monitoring & Debugging

### Health Checks

All servers provide health check endpoint:

```bash
curl http://localhost:8001/health
# Returns: {"status": "healthy", "server": "applicant_db", "database": "connected"}
```

### Logging

All server activity is logged with structured JSON:

```bash
tail -f logs/app.log | jq 'select(.server == "applicant_db")'
```

### Tool Tracing

All tool calls include trace_id for request tracking:

```bash
grep "trace-abc123" logs/app.log | jq '.'
```

---

## Testing

Run MCP server tests:

```bash
# All MCP tests
pytest tests/unit/test_mcp_servers.py -v

# Specific server tests
pytest tests/unit/test_mcp_servers.py::TestApplicantDBServer -v

# Integration tests
pytest tests/integration/test_mcp_servers.py -v
```

---

## Best Practices

1. **Use connection pooling**: BaseMCPServer provides `get_session()` which reuses connections
2. **Log all errors**: Use `logger.error()` with context; don't silently fail
3. **Validate input**: Use Pydantic models for tool parameters
4. **Cache results**: Anomaly rules and thresholds can be cached (expires every 24h)
5. **Handle timeouts**: Tools should complete in < 2 seconds; else escalate to manual review
6. **Never delete data**: Audit logs are immutable; use soft deletes if needed
7. **Trace everything**: Include trace_id in all database writes for debugging

---

## Migration & Versioning

When updating decision rules or thresholds:

1. **Add new rule** to database
2. **Keep old rule** for backward compatibility (1 week grace period)
3. **Log migration** with timestamp and reason
4. **Monitor errors** in agents using new thresholds

Example:

```python
# Add new rule
new_rule = RiskRule(
    rule_name="dti_favorable_max_v2",
    rule_type="dti",
    float_value=0.35,  # Changed from 0.36
    description="Updated DTI threshold (2026-11-01)",
)
db.add(new_rule)
db.commit()

# Agents can opt-in to new rule:
thresholds = server.get_risk_thresholds()
dti_max = thresholds["dti_favorable_max_v2"]  # or fallback to v1
```

---

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/anthropics/fastmcp)
- [System Design Document](./system_design.md)
- [Requirements Specification](./requirements.md)

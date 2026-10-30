"""
Export LangGraph workflow as Mermaid diagram.

Generates a visual representation of the workflow structure.
"""


def get_mermaid_diagram() -> str:
    """
    Generate Mermaid diagram of loan application workflow.
    
    Returns:
        Mermaid flowchart definition
    """
    diagram = """
graph TD
    Start([Start]) --> Validate["<b>VALIDATE</b><br/>Input Validation<br/>- Check required fields<br/>- Validate data types<br/>- Check ranges"]
    
    Validate -->|Valid| Profile["<b>AGENT 1: PROFILE</b><br/>Applicant Profile Analysis<br/>- Query ApplicantDB MCP<br/>- Assess employment stability<br/>- Flag anomalies"]
    
    Validate -->|Invalid| Manual1["Manual Review"]
    
    Profile --> Financial["<b>AGENT 2: FINANCIAL</b><br/>Financial Risk Analysis<br/>- Calculate DTI, LTI<br/>- Classify credit risk<br/>- Detect anomalies"]
    
    Financial --> Decision["<b>AGENT 3: DECISION</b><br/>Loan Decision Synthesis<br/>- Apply decision rules<br/>- Calculate risk score<br/>- Determine confidence"]
    
    Decision --> Route{"Escalate to<br/>Manual Review?<br/>- Confidence < 0.75?<br/>- Anomalies?<br/>- Error state?"}
    
    Route -->|Yes| Manual2["<b>MANUAL REVIEW</b><br/>Human Underwriter<br/>- Review case details<br/>- Override decision<br/>- Provide assessment"]
    
    Route -->|No| Compliance["<b>AGENT 4: COMPLIANCE</b><br/>Compliance & Action<br/>- Create case ID<br/>- Send notification<br/>- Log audit trail"]
    
    Manual1 --> End([End])
    Manual2 --> End
    Compliance --> End
    
    style Start fill:#90EE90
    style End fill:#FFB6C6
    style Validate fill:#87CEEB
    style Profile fill:#FFD700
    style Financial fill:#FFD700
    style Decision fill:#FFD700
    style Compliance fill:#DDA0DD
    style Manual1 fill:#FFA500
    style Manual2 fill:#FFA500
    style Route fill:#87CEEB
"""
    return diagram.strip()


def export_mermaid_file(filepath: str) -> None:
    """
    Export Mermaid diagram to file.
    
    Args:
        filepath: Path to write Mermaid diagram
    """
    diagram = get_mermaid_diagram()
    with open(filepath, "w") as f:
        f.write(diagram)
    print(f"Mermaid diagram exported to {filepath}")


def get_decision_tree() -> str:
    """
    Generate decision tree explanation.
    
    Returns:
        Text representation of decision logic
    """
    tree = """
LOAN DECISION TREE
==================

INPUT: Applicant Profile + Financial Metrics

DECISION LOGIC:

1. AUTO-APPROVE if ALL:
   - Employment Risk: LOW
   - DTI Classification: FAVORABLE or ACCEPTABLE
   - Credit Risk: LOW or MODERATE
   - LTI Classification: FAVORABLE or ACCEPTABLE
   - No anomalies detected
   - Confidence >= 0.85
   → Decision: APPROVED

2. AUTO-REJECT if ANY:
   - Employment Risk: HIGH
   - DTI Classification: HIGH_RISK
   - Credit Risk: HIGH or VERY_HIGH
   - LTI Classification: HIGH_RISK
   - Anomalies detected
   → Decision: REJECTED

3. MANUAL REVIEW if:
   - Does not match auto-approve OR auto-reject criteria
   - Confidence < 0.75
   - Missing data or incomplete profile
   → Decision: REQUIRES_REVIEW

OUTPUT: Final Decision + Case ID + Notification

ROUTING:
- APPROVED → Notify applicant + Create case + Log audit
- REJECTED → Notify applicant + Create case + Log audit
- REQUIRES_REVIEW → Flag for manual underwriter review
"""
    return tree.strip()


if __name__ == "__main__":
    # Export to file
    export_mermaid_file("./WORKFLOW_DIAGRAM.md")
    print("\nDECISION TREE:")
    print(get_decision_tree())

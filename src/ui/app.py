"""
Enhanced Streamlit Chatbot UI for Loan Applications.

Features:
- Conversational form collection
- Chat-style interface
- Agent-by-agent trace display
- Colored decision badges
- Comprehensive error handling
- Real-time feedback
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, List
import time

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Loan Approval Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .decision-approved {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .decision-rejected {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .decision-review {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .agent-trace {
        background-color: #e7f3ff;
        border-left: 5px solid #2196F3;
        padding: 12px;
        margin: 5px 0;
        border-radius: 3px;
        font-family: monospace;
        font-size: 12px;
    }
    
    .agent-trace.success {
        background-color: #e8f5e9;
        border-left-color: #4caf50;
    }
    
    .agent-trace.error {
        background-color: #ffebee;
        border-left-color: #f44336;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_application" not in st.session_state:
    st.session_state.current_application = {}

if "application_fields" not in st.session_state:
    st.session_state.application_fields = [
        "applicant_id",
        "age",
        "income",
        "employment_type",
        "credit_score",
        "loan_amount",
        "tenure_months",
        "existing_liabilities",
        "location",
    ]

if "field_index" not in st.session_state:
    st.session_state.field_index = 0

if "decision_result" not in st.session_state:
    st.session_state.decision_result = None

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.session_state.api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="FastAPI backend URL"
    )
    
    if st.button("🧪 Test API Connection"):
        try:
            response = requests.get(f"{st.session_state.api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API is healthy")
            else:
                st.error(f"API returned: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
    
    st.markdown("---")
    
    st.title("📊 Session Info")
    if st.session_state.current_application:
        st.write(f"**Applicant ID:** {st.session_state.current_application.get('applicant_id', 'N/A')}")
        st.write(f"**Fields Completed:** {len(st.session_state.current_application)}/9")
    else:
        st.write("No application started yet")
    
    if st.button("🔄 Start New Application"):
        st.session_state.messages = []
        st.session_state.current_application = {}
        st.session_state.field_index = 0
        st.session_state.decision_result = None
        st.rerun()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_field_prompt(field: str) -> str:
    """Get a conversational prompt for each field."""
    prompts = {
        "applicant_id": "What is your unique applicant ID? (auto-generated if blank)",
        "age": "What is your age? (18-80)",
        "income": "What is your annual gross income?",
        "employment_type": "What is your employment type?",
        "credit_score": "What is your credit score? (300-850)",
        "loan_amount": "What loan amount are you requesting?",
        "tenure_months": "What is your desired loan term in months? (12-360)",
        "existing_liabilities": "What are your existing liabilities/debts?",
        "location": "What is your location (country code, e.g., US, CA)?",
    }
    return prompts.get(field, f"Please provide: {field}")


def parse_field_value(field: str, value: str) -> Any:
    """Parse and validate field value."""
    try:
        if field == "applicant_id":
            return value if value else f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elif field == "age":
            age = int(value)
            if 18 <= age <= 80:
                return age
            else:
                raise ValueError("Age must be between 18 and 80")
        elif field == "income":
            return float(value)
        elif field == "employment_type":
            valid = ["Salaried", "Self-Employed", "Unemployed", "Retired"]
            if value in valid:
                return value
            else:
                raise ValueError(f"Must be one of: {', '.join(valid)}")
        elif field == "credit_score":
            score = int(value)
            if 300 <= score <= 850:
                return score
            else:
                raise ValueError("Credit score must be between 300 and 850")
        elif field == "loan_amount":
            return float(value)
        elif field == "tenure_months":
            months = int(value)
            if 12 <= months <= 360:
                return months
            else:
                raise ValueError("Tenure must be between 12 and 360 months")
        elif field == "existing_liabilities":
            return float(value)
        elif field == "location":
            if len(value) == 2 and value.isupper():
                return value
            else:
                raise ValueError("Location must be a 2-letter country code")
    except ValueError as e:
        raise ValueError(f"Invalid {field}: {str(e)}")


def call_api(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call FastAPI endpoint."""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/api/v1/applications",
            json=application_data,
            timeout=10
        )
        
        if response.status_code == 202:
            trace_id = response.json().get("trace_id")
            
            # Get decision
            decision_response = requests.get(
                f"{st.session_state.api_url}/api/v1/applications/{trace_id}",
                timeout=10
            )
            
            if decision_response.status_code == 200:
                decision_data = decision_response.json()
                
                # Get audit trail
                audit_response = requests.get(
                    f"{st.session_state.api_url}/api/v1/applications/{trace_id}/audit",
                    timeout=10
                )
                
                audit_data = audit_response.json() if audit_response.status_code == 200 else {}
                decision_data["audit"] = audit_data
                
                return decision_data
        
        return {"error": f"API returned status {response.status_code}"}
    
    except requests.ConnectionError:
        return {"error": "Cannot connect to API. Make sure FastAPI is running."}
    except requests.Timeout:
        return {"error": "API request timeout"}
    except Exception as e:
        return {"error": f"API error: {str(e)}"}


# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

st.title("🤖 AI Loan Approval Chatbot")
st.markdown("""
Welcome! I'm your AI loan assistant. I'll collect your application information 
and provide an instant decision based on our evaluation criteria.
""")

# Display chat history
st.markdown("---")
st.subheader("💬 Conversation")

chat_container = st.container(height=400)

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.write(message["content"])

# ============================================================================
# DECISION DISPLAY
# ============================================================================

if st.session_state.decision_result:
    st.markdown("---")
    st.subheader("📋 Decision Results")
    
    result = st.session_state.decision_result
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    risk_score = result.get("risk_score", 0)
    case_id = result.get("case_id", "N/A")
    
    # Decision badge with color
    if decision == "APPROVED":
        badge_html = '<div class="decision-approved">'
        badge_emoji = "✅"
    elif decision == "REJECTED":
        badge_html = '<div class="decision-rejected">'
        badge_emoji = "❌"
    else:
        badge_html = '<div class="decision-review">'
        badge_emoji = "⚠️"
    
    badge_html += f"""
    <h2 style="margin: 0; color: {'#28a745' if decision == 'APPROVED' else '#dc3545' if decision == 'REJECTED' else '#ff9800'};">
        {badge_emoji} {decision}
    </h2>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Decision", decision)
    
    with col2:
        st.metric("Confidence", f"{confidence:.1%}")
    
    with col3:
        st.metric("Risk Score", f"{risk_score}/100")
    
    with col4:
        st.metric("Case ID", case_id[:15])
    
    # Explanation
    st.markdown("### 📝 Explanation")
    st.info(result.get("explanation", "No explanation available"))
    
    # Decision factors
    factors = result.get("decision_factors", [])
    if factors:
        st.markdown("### 🎯 Decision Factors")
        
        for i, factor in enumerate(factors, 1):
            with st.expander(f"{i}. {factor.get('factor', 'N/A')} - {factor.get('impact', 'N/A')}"):
                st.write(f"**Value:** {factor.get('value', 'N/A')}")
                st.write(f"**Impact:** {factor.get('impact', 'N/A')}")
                st.write(f"**Description:** {factor.get('description', 'N/A')}")
    
    # Agent-by-agent trace
    st.markdown("---")
    st.markdown("### 🔍 Agent-by-Agent Trace")
    
    audit = result.get("audit", {})
    agents_run = audit.get("agents_run", [])
    
    if agents_run:
        agent_details = {
            "validate": "🔍 Input Validation - Checked all required fields",
            "profile": "👤 Profile Analysis - Analyzed employment & credit history",
            "financial": "💳 Financial Risk - Calculated DTI, LTI, and risk scores",
            "decision": "⚖️ Decision Synthesis - Applied lending rules",
            "manual_review": "👨‍⚖️ Manual Review - Escalated for human review",
            "compliance": "📝 Compliance - Logged audit trail & notifications",
        }
        
        trace_html = ""
        for agent in agents_run:
            detail = agent_details.get(agent, f"Agent: {agent}")
            trace_html += f'<div class="agent-trace success">✅ {detail}</div>'
        
        st.markdown(trace_html, unsafe_allow_html=True)
    
    # Application summary
    st.markdown("---")
    st.markdown("### 📄 Application Summary")
    
    if st.session_state.current_application:
        app_data = st.session_state.current_application
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Applicant ID:** {app_data.get('applicant_id')}")
            st.write(f"**Age:** {app_data.get('age')}")
            st.write(f"**Income:** ${app_data.get('income'):,.0f}")
        
        with col2:
            st.write(f"**Loan Amount:** ${app_data.get('loan_amount'):,.0f}")
            st.write(f"**Term:** {app_data.get('tenure_months')} months")
            st.write(f"**Employment:** {app_data.get('employment_type')}")
        
        with col3:
            st.write(f"**Credit Score:** {app_data.get('credit_score')}")
            st.write(f"**Liabilities:** ${app_data.get('existing_liabilities'):,.0f}")
            st.write(f"**Location:** {app_data.get('location')}")

# ============================================================================
# CHAT INPUT & FORM COLLECTION
# ============================================================================

if not st.session_state.decision_result:
    # If no application started, show intro
    if st.session_state.field_index == 0 and not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 Hello! I'm your AI Loan Assistant. Let's start by collecting your information. First, what is your applicant ID? (Or I can generate one for you)"
        })
    
    # Display current field prompt
    if st.session_state.field_index < len(st.session_state.application_fields):
        current_field = st.session_state.application_fields[st.session_state.field_index]
        
        # Show the prompt if not already shown
        if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
            prompt_text = get_field_prompt(current_field)
            st.session_state.messages.append({
                "role": "assistant",
                "content": prompt_text
            })
        
        # Input field
        user_input = st.chat_input(
            f"Your response for {current_field}:",
            key=f"input_{st.session_state.field_index}"
        )
        
        if user_input:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Parse and validate
            try:
                parsed_value = parse_field_value(current_field, user_input)
                st.session_state.current_application[current_field] = parsed_value
                
                # Add confirmation
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Got it! {current_field}: {parsed_value}"
                })
                
                # Move to next field or submit
                st.session_state.field_index += 1
                
                if st.session_state.field_index >= len(st.session_state.application_fields):
                    # All fields collected, submit
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "🔄 Processing your application..."
                    })
                    
                    # Call API
                    result = call_api(st.session_state.current_application)
                    
                    if "error" in result:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error: {result['error']}"
                        })
                    else:
                        st.session_state.decision_result = result
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "✅ Decision complete! See the results below."
                        })
                
                st.rerun()
            
            except ValueError as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Invalid input: {str(e)}. Please try again."
                })
                st.rerun()


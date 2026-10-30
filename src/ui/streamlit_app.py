"""
Streamlit web application for loan applications.

Provides:
- Application form (10 fields)
- Real-time decision display
- Decision factor explanation
- Audit trail viewer
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any
import time

# Set page config
st.set_page_config(
    page_title="Loan Application System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("💰 Intelligent Loan Approval System")
st.markdown("""
Multi-agent AI system for fast, fair, and explainable loan decisions.
Powered by Claude Sonnet 4.6 and LangGraph orchestration.
""")

# Sidebar: System status
st.sidebar.title("System Status")

# Initialize session state
if "trace_id" not in st.session_state:
    st.session_state.trace_id = None
if "application_data" not in st.session_state:
    st.session_state.application_data = None
if "decision_result" not in st.session_state:
    st.session_state.decision_result = None
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None

# Tab structure
tab1, tab2, tab3 = st.tabs(["📋 Application", "📊 Decision", "🔍 Audit Trail"])

# ============================================================================
# TAB 1: APPLICATION FORM
# ============================================================================
with tab1:
    st.header("Loan Application Form")
    
    col1, col2 = st.columns(2)
    
    with col1:
        applicant_id = st.text_input(
            "Applicant ID",
            value="APP-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            help="Unique identifier (auto-generated)"
        )
        
        age = st.slider(
            "Age",
            min_value=18,
            max_value=80,
            value=35,
            step=1
        )
        
        income = st.number_input(
            "Annual Gross Income ($)",
            min_value=1000,
            max_value=10000000,
            value=85000,
            step=5000,
            format="%d"
        )
        
        employment_type = st.selectbox(
            "Employment Type",
            ["Salaried", "Self-Employed", "Retired", "Unemployed"]
        )
        
        credit_score = st.slider(
            "Credit Score",
            min_value=300,
            max_value=850,
            value=745,
            step=5
        )
    
    with col2:
        loan_amount = st.number_input(
            "Requested Loan Amount ($)",
            min_value=1000,
            max_value=5000000,
            value=150000,
            step=5000,
            format="%d"
        )
        
        tenure_months = st.slider(
            "Loan Term (Months)",
            min_value=12,
            max_value=360,
            value=180,
            step=12
        )
        
        existing_liabilities = st.number_input(
            "Existing Liabilities ($)",
            min_value=0,
            max_value=10000000,
            value=12000,
            step=1000,
            format="%d"
        )
        
        location = st.selectbox(
            "Location (Country Code)",
            ["US", "CA", "UK", "AU", "NZ", "IE"]
        )
    
    # Submit button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit_button = st.button("📤 Submit Application", use_container_width=True)
    
    with col2:
        clear_button = st.button("🔄 Clear Form", use_container_width=True)
    
    # Handle clear
    if clear_button:
        st.session_state.trace_id = None
        st.session_state.application_data = None
        st.session_state.decision_result = None
        st.rerun()
    
    # Handle submit
    if submit_button:
        application_data = {
            "applicant_id": applicant_id,
            "age": age,
            "income": float(income),
            "employment_type": employment_type,
            "credit_score": credit_score,
            "loan_amount": float(loan_amount),
            "tenure_months": tenure_months,
            "existing_liabilities": float(existing_liabilities),
            "location": location,
        }
        
        st.session_state.application_data = application_data
        
        # Show processing status
        with st.spinner("⏳ Processing application..."):
            try:
                # Call API (increased timeout to 15s for agent processing)
                response = requests.post(
                    "http://localhost:8000/api/v1/applications",
                    json=application_data,
                    timeout=15
                )
                
                if response.status_code == 202:
                    result = response.json()
                    st.session_state.trace_id = result.get("trace_id")
                    # Store decision result if returned in submission response
                    if "decision" in result:
                        st.session_state.decision_result = result
                    st.success(f"✅ Application submitted! Trace ID: {st.session_state.trace_id}")
                    st.info("📊 Switch to 'Decision' tab to view results!")
                else:
                    st.error(f"❌ Submission failed: {response.text}")
            
            except requests.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure FastAPI is running on http://localhost:8000")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ============================================================================
# TAB 2: DECISION DISPLAY
# ============================================================================
with tab2:
    st.header("Decision Results")

    if st.session_state.trace_id:
        # Auto-fetch decision if not already fetched
        if not st.session_state.decision_result:
            try:
                response = requests.get(
                    f"http://localhost:8000/api/v1/applications/{st.session_state.trace_id}",
                    timeout=15
                )

                if response.status_code == 200:
                    st.session_state.decision_result = response.json()
            except Exception as e:
                st.warning(f"⏳ Processing... Please wait a moment and refresh.")

        # Refresh button
        if st.button("🔄 Refresh Decision", key="refresh_decision"):
            try:
                response = requests.get(
                    f"http://localhost:8000/api/v1/applications/{st.session_state.trace_id}",
                    timeout=15
                )

                if response.status_code == 200:
                    st.session_state.decision_result = response.json()
                    st.success("✅ Decision refreshed!")
            except Exception as e:
                st.error(f"Error retrieving decision: {str(e)}")

        if st.session_state.decision_result:
            result = st.session_state.decision_result
            
            # Decision banner
            decision = result.get("decision", "UNKNOWN")
            confidence = result.get("confidence", 0.0)
            risk_score = result.get("risk_score", 0)
            
            # Color based on decision
            if decision == "APPROVED":
                st.success(f"✅ **APPROVED**")
                color = "green"
            elif decision == "REJECTED":
                st.error(f"❌ **REJECTED**")
                color = "red"
            else:
                st.warning(f"⚠️ **REQUIRES MANUAL REVIEW**")
                color = "orange"
            
            # Decision metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Decision", decision, delta=None)
            
            with col2:
                st.metric("Confidence", f"{confidence:.1%}", delta=None)
            
            with col3:
                st.metric("Risk Score", f"{risk_score}/100", delta=None)
            
            with col4:
                case_id = result.get("case_id", "N/A")
                st.metric("Case ID", case_id[:15] + "..." if len(str(case_id)) > 15 else case_id)
            
            # Explanation
            st.subheader("📝 Decision Explanation")
            st.info(result.get("explanation", "No explanation available"))
            
            # Decision factors
            factors = result.get("decision_factors", [])
            if factors:
                st.subheader("🎯 Decision Factors")
                
                factor_cols = st.columns(len(factors[:3]))  # Show first 3
                for i, factor in enumerate(factors[:3]):
                    with factor_cols[i]:
                        st.markdown(f"""
                        **{factor.get('factor', 'N/A')}**
                        
                        Value: {factor.get('value', 'N/A')}
                        
                        Impact: {factor.get('impact', 'N/A')}
                        """)
        else:
            st.info("👈 Submit an application to see the decision")
    else:
        st.info("👈 Submit an application in the form to see results")


# ============================================================================
# TAB 3: AUDIT TRAIL
# ============================================================================
with tab3:
    st.header("Audit Trail & Compliance")

    if st.session_state.trace_id:
        # Auto-fetch audit trail if not already fetched
        if not st.session_state.audit_result:
            try:
                response = requests.get(
                    f"http://localhost:8000/api/v1/applications/{st.session_state.trace_id}/audit",
                    timeout=15
                )

                if response.status_code == 200:
                    st.session_state.audit_result = response.json()
            except Exception as e:
                st.warning(f"⏳ Processing... Please wait a moment and refresh.")

        # Refresh button
        if st.button("🔄 Refresh Audit Trail", key="refresh_audit"):
            try:
                response = requests.get(
                    f"http://localhost:8000/api/v1/applications/{st.session_state.trace_id}/audit",
                    timeout=15
                )

                if response.status_code == 200:
                    st.session_state.audit_result = response.json()
                    st.success("✅ Audit trail refreshed!")
            except Exception as e:
                st.error(f"Error retrieving audit trail: {str(e)}")

        if st.session_state.audit_result:
            audit = st.session_state.audit_result

            # Audit information
            col1, col2, col3 = st.columns(3)

            with col1:
                trace_id = audit.get("trace_id", "N/A")
                trace_display = trace_id[:20] if isinstance(trace_id, str) else "N/A"
                st.metric("Trace ID", trace_display)

            with col2:
                case_id = audit.get("case_id", "N/A")
                case_display = case_id[:20] if isinstance(case_id, str) else "N/A"
                st.metric("Case ID", case_display)

            with col3:
                st.metric("Decision", audit.get("decision", "N/A"))
            
            # Agents run (audit trail)
            st.subheader("📋 Processing Pipeline")
            agents_run = audit.get("agents_run", [])
            
            if agents_run:
                # Timeline visualization
                steps = {
                    "validate": "🔍 Input Validation",
                    "profile": "👤 Profile Analysis",
                    "financial": "💳 Financial Risk",
                    "decision": "⚖️ Decision Synthesis",
                    "manual_review": "👨‍⚖️ Manual Review",
                    "compliance": "📝 Compliance Logging",
                }
                
                for agent in agents_run:
                    st.write(f"✅ {steps.get(agent, agent)}")
            
            # Application data
            st.subheader("📄 Application Details")
            if st.session_state.application_data:
                app_data = st.session_state.application_data
                
                data_col1, data_col2 = st.columns(2)
                
                with data_col1:
                    st.write(f"**Applicant ID:** {app_data.get('applicant_id')}")
                    st.write(f"**Age:** {app_data.get('age')}")
                    st.write(f"**Income:** ${app_data.get('income'):,.0f}")
                    st.write(f"**Credit Score:** {app_data.get('credit_score')}")
                
                with data_col2:
                    st.write(f"**Loan Amount:** ${app_data.get('loan_amount'):,.0f}")
                    st.write(f"**Term:** {app_data.get('tenure_months')} months")
                    st.write(f"**Liabilities:** ${app_data.get('existing_liabilities'):,.0f}")
                    st.write(f"**Location:** {app_data.get('location')}")
    else:
        st.info("👈 Submit an application to see the audit trail")


# ============================================================================
# SIDEBAR: CONFIGURATION
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configuration")

api_url = st.sidebar.text_input(
    "API URL",
    value="http://localhost:8000",
    help="Base URL for the API"
)

if st.sidebar.button("🧪 Test API Connection"):
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ API is healthy")
        else:
            st.sidebar.error(f"API returned: {response.status_code}")
    except:
        st.sidebar.error("❌ Cannot reach API")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
**Agentic AI Loan Approval System**

Powered by:
- 🤖 Claude Sonnet 4.6
- 🔗 LangGraph Orchestration
- 📡 Model Context Protocol
- ⚡ FastAPI + Streamlit

Version: 1.0.0
""")

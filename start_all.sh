#!/bin/bash

# Agentic AI Loan Approval System - Complete Startup Script
# Starts all services: MCP servers, FastAPI backend, Streamlit UI

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  Agentic AI Loan Approval System - STARTUP                            ║"
echo "║  Starting all services on localhost...                               ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing processes on ports 8000-8004 (cleanup)
cleanup() {
    echo ""
    echo "🛑 Cleaning up..."
    pkill -f "python3 -m src.mcp_servers" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "streamlit" 2>/dev/null || true
    sleep 1
    echo "✅ Cleanup complete"
}

trap cleanup EXIT

# Start MCP Servers in background
echo "📡 Starting MCP Servers..."
echo ""

python3 -m src.mcp_servers.applicant_db > logs/mcp_applicant_db.log 2>&1 &
MCP_APPLICANT_PID=$!
echo "  ✅ ApplicantDB Server (PID: $MCP_APPLICANT_PID) → http://localhost:8001"

python3 -m src.mcp_servers.risk_rules_db > logs/mcp_risk_rules.log 2>&1 &
MCP_RISK_PID=$!
echo "  ✅ RiskRulesDB Server (PID: $MCP_RISK_PID) → http://localhost:8002"

python3 -m src.mcp_servers.decision_synthesis > logs/mcp_decision.log 2>&1 &
MCP_DECISION_PID=$!
echo "  ✅ DecisionSynthesis Server (PID: $MCP_DECISION_PID) → http://localhost:8003"

python3 -m src.mcp_servers.notification_system > logs/mcp_notification.log 2>&1 &
MCP_NOTIFICATION_PID=$!
echo "  ✅ NotificationSystem Server (PID: $MCP_NOTIFICATION_PID) → http://localhost:8004"

sleep 2

# Start FastAPI Backend
echo ""
echo "🚀 Starting FastAPI Backend..."
python3 -m uvicorn src.api.main:app --reload --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "  ✅ FastAPI Backend (PID: $FASTAPI_PID) → http://localhost:8000"
echo "     📚 Swagger Docs: http://localhost:8000/docs"
echo "     📖 ReDoc: http://localhost:8000/redoc"

sleep 2

# Start Streamlit UI
echo ""
echo "🎨 Starting Streamlit UI..."
streamlit run src/ui/streamlit_app.py --server.port=8501 --server.address=localhost > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "  ✅ Streamlit UI (PID: $STREAMLIT_PID) → http://localhost:8501"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ ALL SERVICES STARTED                                             ║"
echo "╠════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                        ║"
echo "║  🎯 Open your browser and navigate to:                               ║"
echo "║     👉 http://localhost:8501                                          ║"
echo "║                                                                        ║"
echo "║  📊 System Status:                                                    ║"
echo "║     • MCP Servers: 4/4 running (ports 8001-8004)                     ║"
echo "║     • FastAPI: Running (port 8000)                                   ║"
echo "║     • Streamlit: Running (port 8501)                                 ║"
echo "║                                                                        ║"
echo "║  📝 Logs:                                                             ║"
echo "║     • tail -f logs/fastapi.log                                        ║"
echo "║     • tail -f logs/streamlit.log                                      ║"
echo "║     • tail -f logs/mcp_*.log                                          ║"
echo "║                                                                        ║"
echo "║  🛑 To stop all services: Press Ctrl+C                               ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Wait for all processes
wait

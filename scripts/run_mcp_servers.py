"""
Run all 4 MCP servers simultaneously.

Each server runs on a different port:
- ApplicantDB: 8001
- RiskRulesDB: 8002
- DecisionSynthesis: 8003
- NotificationSystem: 8004

Usage:
    python scripts/run_mcp_servers.py

Or run individually:
    python -m src.mcp_servers.applicant_db
    python -m src.mcp_servers.risk_rules_db
    python -m src.mcp_servers.decision_synthesis
    python -m src.mcp_servers.notification_system
"""

import subprocess
import sys
import time
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_server(server_name: str, port: int, module: str):
    """Run a single MCP server in a subprocess."""
    print(f"Starting {server_name} on port {port}...")
    
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        f"src.mcp_servers.{module}:mcp",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--reload",
    ]
    
    return subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main():
    """Run all MCP servers."""
    servers = [
        ("ApplicantDB", 8001, "applicant_db"),
        ("RiskRulesDB", 8002, "risk_rules_db"),
        ("DecisionSynthesis", 8003, "decision_synthesis"),
        ("NotificationSystem", 8004, "notification_system"),
    ]
    
    processes = []
    
    try:
        print("Initializing MCP servers...")
        print("=" * 60)
        
        for server_name, port, module in servers:
            proc = run_server(server_name, port, module)
            processes.append((server_name, proc, port))
            time.sleep(0.5)
        
        print("=" * 60)
        print("✓ All MCP servers started")
        print("\nServer Status:")
        for server_name, _, port in servers:
            print(f"  - {server_name}: http://127.0.0.1:{port}")
        
        print("\n💡 MCP Servers are running. Press Ctrl+C to stop.")
        print("=" * 60)
        
        # Keep alive
        while True:
            time.sleep(1)
            
            # Check if any process died
            for server_name, proc, port in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  {server_name} died with exit code {proc.returncode}")
    
    except KeyboardInterrupt:
        print("\n\nShutting down MCP servers...")
        for server_name, proc, _ in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"✓ Stopped {server_name}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"✓ Killed {server_name}")
        print("\nAll servers stopped.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Start all MCP servers for loan approval system.

This script starts 4 MCP servers:
1. ApplicantDB (port 8001) - Applicant profile and employment history
2. RiskRulesDB (port 8002) - Risk thresholds and decision rules
3. DecisionSynthesis (port 8003) - Decision synthesis policies
4. NotificationSystem (port 8004) - Audit logging and notifications

Usage:
    python scripts/start_mcp_servers.py

    # In background:
    python scripts/start_mcp_servers.py &
"""

import subprocess
import time
import socket
import sys
import signal
import os
from pathlib import Path

# MCP servers configuration
MCP_SERVERS = [
    {
        "name": "ApplicantDB",
        "port": 8001,
        "module": "src.mcp_servers.applicant_db",
        "command": "python -m uvicorn src.mcp_servers.applicant_db:mcp --host 0.0.0.0 --port 8001",
    },
    {
        "name": "RiskRulesDB",
        "port": 8002,
        "module": "src.mcp_servers.risk_rules_db",
        "command": "python -m uvicorn src.mcp_servers.risk_rules_db:mcp --host 0.0.0.0 --port 8002",
    },
    {
        "name": "DecisionSynthesis",
        "port": 8003,
        "module": "src.mcp_servers.decision_synthesis",
        "command": "python -m uvicorn src.mcp_servers.decision_synthesis:mcp --host 0.0.0.0 --port 8003",
    },
    {
        "name": "NotificationSystem",
        "port": 8004,
        "module": "src.mcp_servers.notification_system",
        "command": "python -m uvicorn src.mcp_servers.notification_system:mcp --host 0.0.0.0 --port 8004",
    },
]

processes = []


def is_port_in_use(port: int) -> bool:
    """Check if port is already in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result == 0


def wait_for_port(port: int, timeout: int = 10) -> bool:
    """Wait for port to be open (server started)."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def health_check_server(port: int, timeout: int = 5) -> bool:
    """Health check by connecting to port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"    ❌ Health check failed: {e}")
        return False


def start_mcp_server(server_config: dict) -> subprocess.Popen:
    """Start a single MCP server."""
    name = server_config["name"]
    port = server_config["port"]
    command = server_config["command"]

    print(f"\n▶️  Starting {name} on port {port}...")

    if is_port_in_use(port):
        print(f"    ⚠️  Port {port} already in use!")
        print(f"    📝 Assuming {name} is already running...")
        return None

    try:
        # Start server process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # Create new process group
        )

        # Wait for server to start
        print(f"    ⏳ Waiting for {name} to be ready...")
        if wait_for_port(port):
            print(f"    ✅ {name} started successfully!")
            # Do health check
            if health_check_server(port):
                print(f"    ✅ {name} health check passed!")
                return process
            else:
                print(f"    ⚠️  {name} health check failed (may still be initializing)")
                return process
        else:
            print(f"    ❌ Timeout waiting for {name} on port {port}")
            process.terminate()
            return None

    except Exception as e:
        print(f"    ❌ Failed to start {name}: {e}")
        return None


def stop_all_servers():
    """Stop all MCP servers gracefully."""
    print("\n\n" + "=" * 70)
    print("🛑 STOPPING MCP SERVERS")
    print("=" * 70)

    for process in processes:
        if process:
            try:
                print(f"   Terminating process {process.pid}...")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print(f"   ✅ Process stopped")
            except Exception as e:
                print(f"   ❌ Error stopping process: {e}")

    print("\n✅ All MCP servers stopped\n")


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("🚀 MCP SERVER STARTUP")
    print("=" * 70)
    print(f"\nStarting {len(MCP_SERVERS)} MCP servers...\n")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda sig, frame: (stop_all_servers(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda sig, frame: (stop_all_servers(), sys.exit(0)))

    # Start all servers
    for server_config in MCP_SERVERS:
        process = start_mcp_server(server_config)
        if process:
            processes.append(process)

    # Summary
    print("\n" + "=" * 70)
    print("📊 MCP SERVER STATUS")
    print("=" * 70)

    running_count = 0
    for server_config in MCP_SERVERS:
        port = server_config["port"]
        name = server_config["name"]
        if is_port_in_use(port):
            print(f"✅ {name:20} - Running on port {port}")
            running_count += 1
        else:
            print(f"❌ {name:20} - NOT running on port {port}")

    print("\n" + "=" * 70)
    if running_count == len(MCP_SERVERS):
        print(f"🎉 SUCCESS: All {len(MCP_SERVERS)} MCP servers are running!")
    else:
        print(
            f"⚠️  WARNING: Only {running_count}/{len(MCP_SERVERS)} MCP servers are running"
        )
    print("=" * 70)

    # Keep servers running
    print("\n📌 MCP servers are running. Press Ctrl+C to stop them.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all_servers()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Initialize SQLite database with schema."""

import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo/AI Loan Approval System')

from src.database.models import create_tables
from src.utils.config import settings

print("=" * 80)
print("Initializing database...")
print("=" * 80)

# Create all tables
create_tables(settings.database_url)
print(f"✅ Database initialized at: {settings.database_url}")

print("=" * 80)
print("Next steps:")
print("  1. Seed mock data: python scripts/seed_mock_data.py")
print("  2. Start MCP servers: python -m src.mcp_servers.*")
print("  3. Start API: python -m uvicorn src.api.main:app --reload")
print("=" * 80)

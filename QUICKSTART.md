# Quick Start Checklist

Get the project running in 10 minutes.

## ✓ Pre-Flight Checks

```bash
# 1. Verify Python version
python3.10 --version
# Expected: Python 3.10.x or higher

# 2. Navigate to project
cd "/home/ubuntu/Desktop/demo/AI Loan Approval System"

# 3. Verify scaffolding
ls -la src/ tests/ config/
# Should see: api/, orchestration/, agents/, mcp_servers/, ui/, utils/, database/
# Should see: unit/, integration/, fixtures/
```

## ✓ Setup Virtual Environment

```bash
# 1. Create venv
python3.10 -m venv venv

# 2. Activate (Linux/macOS)
source venv/bin/activate
# OR activate (Windows)
# .\venv\Scripts\activate

# 3. Verify activation (should show (venv) prefix)
which python
```

## ✓ Install Dependencies

```bash
# 1. Upgrade pip
pip install --upgrade pip setuptools wheel

# 2. Install from requirements.txt
pip install -r requirements.txt

# 3. Verify installation
python -c "import fastapi; import streamlit; import langgraph; print('✓ OK')"
```

## ✓ Configure Environment

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit and add your API key
nano .env
# Find: ANTHROPIC_API_KEY=sk-ant-xxx-your-api-key-here-xxx
# Replace with: ANTHROPIC_API_KEY=sk-ant-YOUR_REAL_KEY

# 3. Verify
echo $ANTHROPIC_API_KEY
```

## ✓ Test Configuration

```bash
# 1. Test config loading
python -c "from src.utils.config import settings; print(f'Config: {settings.app_env}')"

# 2. Test Pydantic models
python -c "from src.utils.schemas import ApplicationData; print('✓ Schemas OK')"

# 3. Test database path
python -c "from src.utils.config import settings; print(f'Database: {settings.db_path}')"
```

## ✓ Quick Tests

```bash
# 1. Test imports work
python << 'EOF'
try:
    from fastapi import FastAPI
    from streamlit import echo
    from langgraph import Graph
    from anthropic import Anthropic
    from pydantic import BaseModel
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
EOF

# 2. Test config loads
python << 'EOF'
try:
    from src.utils.config import settings
    assert settings.anthropic_api_key.startswith("sk-ant-")
    print(f"✓ Config loaded: environment={settings.app_env}, port={settings.api_port}")
except Exception as e:
    print(f"✗ Config error: {e}")
EOF

# 3. Test schemas validate
python << 'EOF'
try:
    from src.utils.schemas import ApplicationData
    from decimal import Decimal
    from datetime import datetime
    
    app = ApplicationData(
        applicant_id="APP-12345",
        age=35,
        income=Decimal("85000"),
        employment_type="Salaried",
        credit_score=745,
        loan_amount=Decimal("150000"),
        tenure_months=180,
        existing_liabilities=Decimal("12000"),
        location="US",
        timestamp=datetime.utcnow()
    )
    print(f"✓ Application data validated: {app.applicant_id}")
except Exception as e:
    print(f"✗ Schema error: {e}")
EOF
```

## ✓ Environment Verification

| Check | Command | Expected |
|-------|---------|----------|
| Python | `python --version` | 3.10+ |
| Venv Active | `which python` | Path includes `/venv/` |
| Config Loads | `python -c "from src.utils.config import settings"` | No error |
| Schemas OK | `python -c "from src.utils.schemas import ApplicationData"` | No error |
| API Key Set | `echo $ANTHROPIC_API_KEY` | Starts with `sk-ant-` |

## 🚀 You're Ready!

The project is now set up and ready for Phase 1 implementation.

### Next Steps

1. **Read Documentation** (in this order):
   - `SCAFFOLDING_SUMMARY.md` - What was scaffolded
   - `CLAUDE.md` - Coding conventions & development workflow
   - `SETUP.md` - Detailed setup reference

2. **Start Phase 1** (Week 1, Day 1):
   - Follow step-by-step plan in CLAUDE.md
   - Build → Test → Commit (every 30-60 minutes)

3. **First Task** (Day 1: Project Structure & Config):
   ```bash
   # Already complete! All structure and config created.
   # Next: Day 2 - Core Models & Schemas (src/utils/schemas.py already created!)
   ```

## 📋 Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'src'` | Run `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` or `pip install -e .` |
| `ANTHROPIC_API_KEY not set` | Edit `.env` and add your key, then restart terminal |
| `Port 8000 already in use` | Use `python -m uvicorn src.api.main:app --port 8001` |
| `Python 3.10 not found` | Install via `brew install python@3.10` (macOS) or `apt install python3.10` (Linux) |
| Module import errors | Try `pip install -e .` to install package in development mode |

## 📞 Key Commands

```bash
# Activate venv
source venv/bin/activate

# Run FastAPI (when implemented)
python -m uvicorn src.api.main:app --reload

# Run Streamlit (when implemented)
streamlit run src/ui/streamlit_app.py

# Run tests
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=src --cov-report=html

# Type checking (optional)
mypy src/ --ignore-missing-imports

# Code formatting (optional)
black src/ tests/
```

## ✅ Completion Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with ANTHROPIC_API_KEY
- [ ] Config loads without errors (`python -c "from src.utils.config import settings"`)
- [ ] Pydantic schemas work (`python -c "from src.utils.schemas import ApplicationData"`)
- [ ] All imports successful (run the import test above)
- [ ] Read CLAUDE.md for development workflow
- [ ] Ready to start Phase 1 implementation!

---

**Time to completion:** ~10 minutes  
**Documentation:** See CLAUDE.md, SETUP.md, SCAFFOLDING_SUMMARY.md  
**Status:** ✅ Ready for Phase 1 Implementation  

Good luck! 🚀

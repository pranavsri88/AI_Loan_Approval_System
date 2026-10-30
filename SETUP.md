# Virtual Environment Setup Guide

This guide walks through setting up the development environment for the Agentic AI Intelligent Loan Approval System.

## Quick Start (Recommended)

### 1. Create Virtual Environment

```bash
# Navigate to project root
cd /home/ubuntu/Desktop/demo/AI\ Loan\ Approval\ System

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

### 2. Verify Python Version

```bash
python --version
# Expected: Python 3.10.x or higher
```

### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install Dependencies

#### Option A: Using requirements.txt (Recommended for Development)

```bash
pip install -r requirements.txt
```

#### Option B: Using pyproject.toml with pip

```bash
pip install -e .
# With dev dependencies:
pip install -e ".[dev]"
```

#### Option C: Using pyproject.toml with pip-tools

```bash
pip install pip-tools
pip-compile pyproject.toml
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your API key
nano .env
# or
vim .env

# Verify ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY
```

### 6. Initialize Database

```bash
# Create database schema
python scripts/init_db.py

# Verify database created
ls -la data/
# Expected: loans.db file should exist
```

### 7. Verify Setup

```bash
# Test imports
python -c "from fastapi import FastAPI; from streamlit import echo; from langgraph import Graph; print('✓ All imports OK')"

# Test config loading
python -c "from src.utils.config import settings; print(f'✓ Config loaded: {settings.app_env}')"

# Test database connection
python -c "import sqlite3; conn = sqlite3.connect('data/loans.db'); print('✓ Database connected')"
```

## Detailed Installation Steps

### For macOS Users

```bash
# Ensure Homebrew is installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.10
brew install python@3.10

# Create virtual environment
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### For Linux Users (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install Python 3.10 and dev tools
sudo apt install python3.10 python3.10-venv python3.10-dev

# Create virtual environment
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### For Windows Users

```bash
# Using PowerShell (as Administrator)

# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

## Troubleshooting

### Issue: `python3.10: command not found`

**Solution:** Check available Python versions:
```bash
python3 --version
python --version
ls /usr/bin/python*
```

If Python 3.10 is not available, install it first (see OS-specific instructions above).

### Issue: `ModuleNotFoundError: No module named 'src'`

**Solution:** Ensure PYTHONPATH includes the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from src.utils.config import settings"
```

Or install the package in editable mode:
```bash
pip install -e .
```

### Issue: `ANTHROPIC_API_KEY not set`

**Solution:** Set the API key:
```bash
# Option 1: In .env file (recommended)
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Option 2: Environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 3: Temporary for one command
ANTHROPIC_API_KEY=sk-ant-... python your_script.py
```

### Issue: Database file not created

**Solution:** Manually initialize:
```bash
python scripts/init_db.py
# or
mkdir -p data/backups
sqlite3 data/loans.db < db/migrations/001_initial_schema.sql
```

### Issue: Port already in use (8000, 8501)

**Solution:** Use different ports:
```bash
# For FastAPI
python -m uvicorn src.api.main:app --port 8001

# For Streamlit
streamlit run src/ui/streamlit_app.py --server.port 8502
```

## Dependency Management

### Adding a New Dependency

```bash
# 1. Add to requirements.txt or pyproject.toml
# For requirements.txt:
echo "new-package==1.0.0" >> requirements.txt

# 2. Install it
pip install new-package==1.0.0

# 3. Freeze to lock file (optional)
pip freeze > requirements.lock
```

### Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade langchain

# Check for outdated packages
pip list --outdated
```

### Creating requirements.lock for Reproducible Builds

```bash
# Freeze exact versions
pip freeze > requirements.lock

# Install from lock file (ensures exact versions)
pip install -r requirements.lock
```

## Activating Virtual Environment

### On macOS/Linux

```bash
# Activate venv
source venv/bin/activate

# Check it's active (should show venv prompt)
which python
# Output: /path/to/venv/bin/python

# Deactivate when done
deactivate
```

### On Windows

```powershell
# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1

# Or with Command Prompt
venv\Scripts\activate.bat

# Check it's active (should show venv in prompt)
where python

# Deactivate when done
deactivate
```

## IDE Setup

### VS Code

1. **Install Python extension:** `ms-python.python`
2. **Select interpreter:**
   - Open Command Palette: `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Linux/Windows)
   - Type: `Python: Select Interpreter`
   - Choose: `./venv/bin/python`
3. **Verify:** Check status bar shows selected interpreter

### PyCharm

1. **Configure interpreter:**
   - Go to: `PyCharm → Preferences → Project → Python Interpreter`
   - Click gear icon → `Add`
   - Select: `Existing Environment → venv/bin/python`
   - Click: `OK`
2. **Verify:** Terminal shows `(venv)` prefix

### Jupyter Notebook (Optional)

```bash
# Install Jupyter in venv
pip install jupyter ipykernel

# Install kernel for this venv
python -m ipykernel install --user --name venv --display-name "Python (venv)"

# Start Jupyter
jupyter notebook

# Select kernel: `Kernel → Change Kernel → Python (venv)`
```

## Docker Setup (Alternative)

Instead of manual venv, use Docker:

```bash
# Build image
docker build -t ai-loan-approval:latest .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  ai-loan-approval:latest

# Or use Docker Compose
docker-compose up
```

## Next Steps

After setup completes:

1. **Read CLAUDE.md** for coding conventions and development workflow
2. **Start development:** Follow Phase 1 setup in CLAUDE.md
3. **Run tests:** `pytest tests/ -v`
4. **View documentation:** `cat docs/requirements.md`

---

## Verification Checklist

- [ ] Python 3.10+ installed (`python --version`)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list | grep fastapi`)
- [ ] ANTHROPIC_API_KEY set in .env
- [ ] Database initialized (`ls data/loans.db`)
- [ ] Imports work (`python -c "from src.utils.config import settings"`)
- [ ] Tests pass (`pytest tests/ -v` - once tests are written)
- [ ] FastAPI starts (`python -m uvicorn src.api.main:app --reload`)
- [ ] Streamlit starts (`streamlit run src/ui/streamlit_app.py`)

---

**Last Updated:** 2026-10-29  
**Python Version:** 3.10+  
**Status:** Ready for Development

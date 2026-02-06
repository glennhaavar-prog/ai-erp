#!/bin/bash
# Setup script for ERP deployment environment

echo "🔧 Setting up ERP environment..."

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not installed"
    echo "Install: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

# Check Python venv
if [ ! -d "venv" ]; then
    echo "❌ Python venv not found"
    echo "Creating venv..."
    python3 -m venv venv
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file missing"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  REMEMBER TO UPDATE .env WITH REAL CREDENTIALS!"
fi

echo "✅ Environment check complete"
echo ""
echo "Next steps:"
echo "1. Update .env with credentials"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Install deps: pip install -r requirements.txt"
echo "4. Run migrations: alembic upgrade head"
echo "5. Start agents!"

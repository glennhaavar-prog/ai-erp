#!/bin/bash

# Database Setup Script for Kontali ERP
# This script sets up PostgreSQL and runs Alembic migrations

set -e  # Exit on error

echo "=========================================="
echo "🚀 Kontali ERP Database Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DB_USER="${DB_USER:-erp_user}"
DB_PASSWORD="${DB_PASSWORD:-erp_password}"
DB_NAME="${DB_NAME:-ai_erp}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "📋 Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST:$DB_PORT"
echo ""

# Check if PostgreSQL is installed
echo "🔍 Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL client not found. Installing...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install postgresql
    else
        echo -e "${RED}❌ Unsupported OS. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ PostgreSQL client found${NC}"

# Check if PostgreSQL is running
echo ""
echo "🔍 Checking PostgreSQL service..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running. Starting...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
    fi
    sleep 2
fi

if pg_isready -h "$DB_HOST" -p "$DB_PORT" &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
    exit 1
fi

# Create database and user
echo ""
echo "🔧 Setting up database and user..."

# Check if running as postgres user or needs sudo
if [ "$USER" = "postgres" ]; then
    PSQL_CMD="psql"
else
    PSQL_CMD="sudo -u postgres psql"
fi

# Create user if not exists
$PSQL_CMD -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
$PSQL_CMD << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER USER $DB_USER CREATEDB;
EOF

echo -e "${GREEN}✅ User created/verified${NC}"

# Create database if not exists
$PSQL_CMD -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
$PSQL_CMD << EOF
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo -e "${GREEN}✅ Database created/verified${NC}"

# Grant schema permissions (for PostgreSQL 15+)
$PSQL_CMD -d "$DB_NAME" << EOF
GRANT ALL ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

echo -e "${GREEN}✅ Permissions granted${NC}"

# Check Python virtual environment
echo ""
echo "🐍 Checking Python environment..."
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi
echo -e "${GREEN}✅ Virtual environment ready${NC}"

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check if .env exists
echo ""
echo "⚙️  Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    
    # Update DATABASE_URL in .env
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=\"postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME\"|" .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please review .env and update API keys before running the app${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Run Alembic migrations
echo ""
echo "🔄 Running database migrations..."
echo ""

# Check current migration status
echo "Current migration status:"
alembic current

echo ""
echo "Applying migrations..."
alembic upgrade head

echo ""
echo -e "${GREEN}✅ Migrations applied successfully${NC}"

# Verify tables were created
echo ""
echo "🔍 Verifying database schema..."
TABLE_COUNT=$(psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -eq 17 ]; then
    echo -e "${GREEN}✅ All 17 tables created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Expected 17 tables, found $TABLE_COUNT${NC}"
fi

# Show created tables
echo ""
echo "📋 Created tables:"
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -c "\dt" | grep public

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo "=========================================="
echo ""
echo "Database connection info:"
echo "  URL: postgresql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next steps:"
echo "  1. Review and update .env file with API keys"
echo "  2. Load seed data: python scripts/seed_data.py"
echo "  3. Start the application: uvicorn app.main:app --reload"
echo ""
echo "To connect to the database:"
echo "  psql postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""

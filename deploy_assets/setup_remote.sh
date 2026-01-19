#!/bin/bash
set -e

# Store start directory (where deploy_assets resides)
START_DIR=$(pwd)

# Configuration
APP_DIR="/var/www/academicguard"
BACKEND_DIR="$APP_DIR/api"
DIST_DIR="$APP_DIR/dist"

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}>>> Starting Server Setup...${NC}"

# 1. Install System Dependencies
echo -e "${GREEN}>>> Installing System Dependencies...${NC}"
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    apt-get update
    apt-get install -y python3 python3-venv python3-pip python3-dev nginx redis-server supervisor build-essential
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    yum install -y python3 python3-devel nginx redis supervisor gcc
    systemctl enable nginx
    systemctl enable supervisord
    systemctl enable redis
else
    echo "Unsupported OS. Please install Python 3.10+, Nginx, Redis, Supervisor manually."
    exit 1
fi

# 2. Setup Directories
echo -e "${GREEN}>>> Setting up Directories...${NC}"
mkdir -p "$BACKEND_DIR"
mkdir -p "$DIST_DIR"

# Move files (Assumes files are in current dir from upload)
# We expect: dist/, src/, requirements.txt, alembic.ini, .env.example, deploy_assets/
if [ -d "dist" ]; then
    cp -r dist/* "$DIST_DIR/"
else
    echo "Warning: dist directory not found in upload."
fi

cp -r src "$BACKEND_DIR/"
cp -r data "$BACKEND_DIR/"
cp -r alembic "$BACKEND_DIR/"
cp requirements.txt "$BACKEND_DIR/"
cp alembic.ini "$BACKEND_DIR/"
cp .env.example "$BACKEND_DIR/.env"

# 3. Setup Python Environment
echo -e "${GREEN}>>> Setting up Python Environment...${NC}"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Install dependencies using Tsinghua Mirror
echo -e "${GREEN}>>> Installing Python Requirements (using Tsinghua Mirror)...${NC}"
./venv/bin/pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
./venv/bin/pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
./venv/bin/pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple uvicorn

# 4. Configure .env
echo -e "${GREEN}>>> Configuring .env...${NC}"
# Generate random secrets
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SERVICE_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Update .env
# Handle uppercase keys from .env.example
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${JWT_SECRET}/" .env
# Also handle lowercase just in case
sed -i "s/jwt_secret_key=.*/jwt_secret_key=${JWT_SECRET}/" .env

# Handle Service Secret (add if missing)
if grep -q "INTERNAL_SERVICE_SECRET" .env; then
    sed -i "s/INTERNAL_SERVICE_SECRET=.*/INTERNAL_SERVICE_SECRET=${SERVICE_SECRET}/" .env
elif grep -q "internal_service_secret" .env; then
    sed -i "s/internal_service_secret=.*/internal_service_secret=${SERVICE_SECRET}/" .env
else
    echo "INTERNAL_SERVICE_SECRET=${SERVICE_SECRET}" >> .env
fi

# Force Debug Mode
if grep -q "SYSTEM_MODE" .env; then
    sed -i "s/SYSTEM_MODE=.*/SYSTEM_MODE=debug/" .env
elif grep -q "system_mode" .env; then
    sed -i "s/system_mode=.*/system_mode=debug/" .env
else
    echo "SYSTEM_MODE=debug" >> .env
fi

# Set Database URL
if grep -q "DATABASE_URL" .env; then
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///$BACKEND_DIR/academicguard.db|" .env
elif grep -q "database_url" .env; then
    sed -i "s|database_url=.*|database_url=sqlite+aiosqlite:///$BACKEND_DIR/academicguard.db|" .env
else
    echo "DATABASE_URL=sqlite+aiosqlite:///$BACKEND_DIR/academicguard.db" >> .env
fi

# Debug .env content
# echo ">>> Debugging .env content:"
# cat .env

# Verify Settings loading
echo ">>> Verifying Settings..."
export PYTHONPATH=$BACKEND_DIR
./venv/bin/python3 -c "from src.config import get_settings; print(get_settings().model_dump_json(indent=2))" || exit 1

# 5. Database Migration
echo -e "${GREEN}>>> Running Database Migrations...${NC}"
./venv/bin/alembic upgrade head

# 6. Configure Nginx
echo -e "${GREEN}>>> Configuring Nginx...${NC}"
cp "$START_DIR/deploy_assets/nginx.conf.template" /etc/nginx/sites-available/academicguard
# Remove default if exists
rm -f /etc/nginx/sites-enabled/default
# Link new config
ln -sf /etc/nginx/sites-available/academicguard /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 7. Configure Supervisor
echo -e "${GREEN}>>> Configuring Supervisor...${NC}"
cp "$START_DIR/deploy_assets/supervisord.conf.template" /etc/supervisor/conf.d/academicguard.conf

# Restart supervisor to load new config
if systemctl list-units --full -all | grep -Fq "supervisor.service"; then
    systemctl restart supervisor
elif systemctl list-units --full -all | grep -Fq "supervisord.service"; then
    systemctl restart supervisord
fi

# Wait for supervisor to start
sleep 5

supervisorctl reread
supervisorctl update
supervisorctl restart academicguard-api

echo -e "${GREEN}>>> Deployment Complete!${NC}"
echo "Frontend: http://<YOUR_SERVER_IP>/"
echo "Backend: http://<YOUR_SERVER_IP>/api/docs"

#!/bin/bash
set -e

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
./venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
./venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
./venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uvicorn

# 4. Configure .env
echo -e "${GREEN}>>> Configuring .env...${NC}"
# Generate random secrets
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SERVICE_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Update .env (Simple sed replacement)
sed -i "s/jwt_secret_key=.*/jwt_secret_key=${JWT_SECRET}/" .env
sed -i "s/internal_service_secret=.*/internal_service_secret=${SERVICE_SECRET}/" .env
# Force Operational Mode for security
sed -i "s/system_mode=debug/system_mode=operational/" .env
# Set Database to SQLite for internal test simplicity (can be changed manually)
# sed -i "s|database_url=.*|database_url=sqlite+aiosqlite:///$BACKEND_DIR/academicguard.db|" .env

# 5. Database Migration
echo -e "${GREEN}>>> Running Database Migrations...${NC}"
./venv/bin/alembic upgrade head

# 6. Configure Nginx
echo -e "${GREEN}>>> Configuring Nginx...${NC}"
cp ../../deploy_assets/nginx.conf.template /etc/nginx/sites-available/academicguard
# Remove default if exists
rm -f /etc/nginx/sites-enabled/default
# Link new config
ln -sf /etc/nginx/sites-available/academicguard /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 7. Configure Supervisor
echo -e "${GREEN}>>> Configuring Supervisor...${NC}"
cp ../../deploy_assets/supervisord.conf.template /etc/supervisor/conf.d/academicguard.conf
supervisorctl reread
supervisorctl update
supervisorctl restart academicguard-api

echo -e "${GREEN}>>> Deployment Complete!${NC}"
echo "Frontend: http://<YOUR_SERVER_IP>/"
echo "Backend: http://<YOUR_SERVER_IP>/api/docs"

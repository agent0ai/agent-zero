#!/bin/sh

# Agent Zero Install Script v1
# Simplified Docker-based installation
# https://github.com/agent0ai/agent-zero

set -e

echo "=========================================="
echo "  Agent Zero - Installation Script v1"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_ok()    { printf "  ${GREEN}✔${NC} %s\n" "$1"; }
print_info()  { printf "${GREEN}[INFO]${NC} %s\n" "$1"; }
print_warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
print_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }

# -----------------------------------------------------------
# 1. Ensure Docker is installed
# -----------------------------------------------------------
if command -v docker > /dev/null 2>&1; then
    print_ok "Docker already installed"
else
    print_warn "Docker not found. Installing via https://get.docker.com ..."
    curl -fsSL https://get.docker.com | sh

    if [ "$(uname -s 2>/dev/null)" = "Linux" ] && [ "$(id -u 2>/dev/null)" -ne 0 ]; then
        print_info "Adding current user to the docker group..."
        sudo usermod -aG docker "$USER"
        print_warn "You may need to log out and back in for group changes to take effect."
    fi
fi

if docker compose version > /dev/null 2>&1; then
    print_ok "Docker Compose available"
else
    print_error "Docker Compose plugin not found. Please install Docker Compose."
    exit 1
fi

echo ""

# -----------------------------------------------------------
# 2. Gather configuration from user
# -----------------------------------------------------------
INSTALL_DIR="$HOME/.agentzero"
DEFAULT_DATA_DIR="$INSTALL_DIR/usr"
DEFAULT_PORT="5080"

# Data directory
printf "Where to store Agent Zero user data? [%s]: " "$DEFAULT_DATA_DIR"
IFS= read -r DATA_DIR
DATA_DIR="${DATA_DIR:-$DEFAULT_DATA_DIR}"
case "$DATA_DIR" in
    ~/*) DATA_DIR="$HOME/${DATA_DIR#~/}" ;;
    ~) DATA_DIR="$HOME" ;;
esac
mkdir -p "$DATA_DIR"
print_info "Data directory: $DATA_DIR"

# Port
printf "Web UI port? [%s]: " "$DEFAULT_PORT"
IFS= read -r PORT
PORT="${PORT:-$DEFAULT_PORT}"
case "$PORT" in
    ''|*[!0-9]*)
    print_error "Invalid port. Falling back to ${DEFAULT_PORT}."
    PORT="$DEFAULT_PORT"
    ;;
esac
print_info "Web UI port: $PORT"

# Authentication
printf "Web UI login username (leave empty for no auth): "
IFS= read -r AUTH_LOGIN
AUTH_PASSWORD=""
if [ -n "$AUTH_LOGIN" ]; then
    printf "Web UI password [12345678]: "
    IFS= read -r AUTH_PASSWORD
    AUTH_PASSWORD="${AUTH_PASSWORD:-12345678}"
    print_info "Auth configured for user: $AUTH_LOGIN"
else
    print_warn "No authentication will be configured."
fi

echo ""
print_info "Configuration complete. Setting up Agent Zero..."
echo ""

# -----------------------------------------------------------
# 3. Generate docker-compose.yml
# -----------------------------------------------------------
mkdir -p "$INSTALL_DIR"

COMPOSE_FILE="$INSTALL_DIR/docker-compose.yml"

{
    echo "services:"
    echo "  agent-zero:"
    echo "    image: agent0ai/agent-zero"
    echo "    container_name: agent-zero"
    echo "    restart: unless-stopped"
    echo "    ports:"
    echo "      - \"${PORT}:80\""
    echo "    volumes:"
    echo "      - ${DATA_DIR}:/a0/usr"
    if [ -n "$AUTH_LOGIN" ]; then
        echo "    environment:"
        echo "      - AUTH_LOGIN=${AUTH_LOGIN}"
        echo "      - AUTH_PASSWORD=${AUTH_PASSWORD}"
    fi
} > "$COMPOSE_FILE"

print_info "Created $COMPOSE_FILE"

# -----------------------------------------------------------
# 4. Pull image & start container
# -----------------------------------------------------------
cd "$INSTALL_DIR"
print_info "Pulling Agent Zero image (this may take a moment)..."
docker compose pull

print_info "Starting Agent Zero..."
docker compose up -d

# -----------------------------------------------------------
# 5. Done!
# -----------------------------------------------------------
echo ""
echo "=========================================="
printf "  ${GREEN}${BOLD}Installation Complete!${NC}\n"
echo "=========================================="
echo ""
echo "  📁 Data directory : $DATA_DIR"
echo "  🌐 Web UI         : http://localhost:$PORT"
if [ -n "$AUTH_LOGIN" ]; then
    echo "  👤 Login          : $AUTH_LOGIN"
    echo "  🔑 Password       : $AUTH_PASSWORD"
else
    echo "  🔓 Authentication : none"
fi
echo ""
echo "  Useful commands:"
echo "    cd $INSTALL_DIR && docker compose logs -f   # View logs"
echo "    cd $INSTALL_DIR && docker compose down      # Stop"
echo "    cd $INSTALL_DIR && docker compose up -d     # Start"
echo "    cd $INSTALL_DIR && docker compose pull      # Update image"
echo ""
print_info "Happy automating with Agent Zero! 🤖"

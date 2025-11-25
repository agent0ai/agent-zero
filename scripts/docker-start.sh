#!/bin/bash
# =============================================================================
# Docker Services Start Script
# =============================================================================
# Starts all Agent Zero services with proper dependency ordering
#
# Usage:
#   ./scripts/docker-start.sh         # Start all services
#   ./scripts/docker-start.sh --build # Rebuild and start
#   ./scripts/docker-start.sh --logs  # Start and follow logs
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Change to project root
cd "$(dirname "$0")/.."

# Parse arguments
BUILD=""
FOLLOW_LOGS=""

for arg in "$@"; do
    case $arg in
        --build)
            BUILD="--build"
            ;;
        --logs)
            FOLLOW_LOGS="true"
            ;;
    esac
done

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Agent Zero Docker Services${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo -e "${YELLOW}Make sure you're in the project root directory${NC}"
    exit 1
fi

# Check for required directories
echo -e "${YELLOW}Checking required directories...${NC}"
mkdir -p data knowledge usr/projects

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Copy from claudedocs/config_templates/.env.* to .env${NC}"
    echo ""
fi

# Start services
echo -e "${YELLOW}Starting Docker services...${NC}"
echo ""

if [ -n "$BUILD" ]; then
    echo -e "${BLUE}Building images...${NC}"
    docker compose build
    echo ""
fi

# Start services in dependency order
echo -e "${BLUE}Starting services...${NC}"
docker compose up -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

services=("redis-cache" "qdrant-unity" "qdrant-mcp-server" "unity-mcp-server" "agent-zero-unity")

for service in "${services[@]}"; do
    echo -n "  $service: "
    timeout=60
    elapsed=0

    while [ $elapsed -lt $timeout ]; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")

        if [ "$status" == "healthy" ]; then
            echo -e "${GREEN}healthy${NC}"
            break
        elif [ "$status" == "unhealthy" ]; then
            echo -e "${RED}unhealthy${NC}"
            break
        fi

        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done

    if [ $elapsed -ge $timeout ]; then
        echo -e "${YELLOW}timeout (may still be starting)${NC}"
    fi
done

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  Services Started!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Service URLs:"
echo -e "  Agent Zero UI:   ${GREEN}http://localhost:50001${NC}"
echo -e "  Qdrant Dashboard: ${GREEN}http://localhost:6333/dashboard${NC}"
echo -e "  Qdrant MCP:      ${GREEN}http://localhost:9060${NC}"
echo -e "  Unity MCP:       ${GREEN}http://localhost:9050${NC}"
echo -e "  Redis:           ${GREEN}localhost:6379${NC}"
echo ""
echo -e "Commands:"
echo -e "  Logs:    docker compose logs -f"
echo -e "  Stop:    docker compose down"
echo -e "  Status:  docker compose ps"
echo ""

if [ "$FOLLOW_LOGS" == "true" ]; then
    echo -e "${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
    echo ""
    docker compose logs -f
fi

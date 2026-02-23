#!/bin/sh

# Agent Zero Install Script v1
# Simplified Docker-based installation
# https://github.com/agent0ai/agent-zero

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

printf "%b" "${BLUE}"
cat <<'EOF'
                   0000000000000000                   
              0000000000000000000000000              
           000000000000000  00000000000000           
         0000000000000000    0000000000000000         
        000000000000000        000000000000000        
       000000000000000          000000000000000      
      00000000000000              00000000000000     
     00000000000000       00       00000000000000     
     0000000000000      000000      0000000000000     
     00000000000       00000000       00000000000     
     0000000000       0000000000       0000000000     
     000000000      00000000000000      000000000     
      000000       000          000       0000000     
       0000       000            000       00000      
        00      0000              0000      00        
         000000000000000000000000000000000000         
           00000000000000000000000000000000           
              00000000000000000000000000              
                  000000000000000000                  
EOF
printf "%b\n" "${NC}"

print_ok()    { printf "  ${GREEN}✔${NC} %s\n" "$1"; }
print_info()  { printf "${GREEN}[INFO]${NC} %s\n" "$1"; }
print_warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
print_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }

check_docker_daemon_running() {
    if docker info >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

start_docker_daemon() {
    OS_NAME="$(uname -s 2>/dev/null || true)"

    case "$OS_NAME" in
        Darwin)
            print_info "Starting Docker Desktop..."
            if command -v open >/dev/null 2>&1; then
                open -a Docker
                return 0
            else
                print_error "Cannot start Docker Desktop automatically."
                return 1
            fi
            ;;
        Linux)
            print_info "Starting Docker daemon..."
            # Try systemctl first
            if command -v systemctl >/dev/null 2>&1; then
                if sudo systemctl start docker >/dev/null 2>&1; then
                    return 0
                fi
            fi
            # Fallback to service command
            if command -v service >/dev/null 2>&1; then
                if sudo service docker start >/dev/null 2>&1; then
                    return 0
                fi
            fi
            print_error "Could not start Docker daemon."
            return 1
            ;;
        *)
            print_error "Automatic Docker daemon start not supported on this OS."
            return 1
            ;;
    esac
}

wait_for_docker_daemon() {
    MAX_WAIT=30
    WAITED=0

    print_info "Waiting for Docker daemon to be ready..."
    while [ $WAITED -lt $MAX_WAIT ]; do
        if docker info >/dev/null 2>&1; then
            print_ok "Docker daemon is ready"
            return 0
        fi
        sleep 1
        WAITED=$((WAITED + 1))
        printf "."
    done
    echo ""
    print_error "Docker daemon did not become ready within ${MAX_WAIT} seconds."
    return 1
}

check_docker() {
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

    # -----------------------------------------------------------
    # 2. Ensure Docker daemon is running
    # -----------------------------------------------------------
    if ! check_docker_daemon_running; then
        print_warn "Docker daemon is not running"
        if start_docker_daemon; then
            if ! wait_for_docker_daemon; then
                print_error "Failed to start Docker daemon. Please start Docker manually and try again."
                exit 1
            fi
        else
            print_error "Please start Docker manually and try again."
            exit 1
        fi
    else
        print_ok "Docker daemon is running"
    fi
}

count_running_agent_zero_containers() {
    docker ps --filter "ancestor=agent0ai/agent-zero" --format '{{.Names}}' 2>/dev/null | awk 'NF {count++} END {print count+0}'
}

instance_name_taken() {
    NAME_TO_CHECK="$1"

    if docker ps -a --format '{{.Names}}' 2>/dev/null | awk -v target="$NAME_TO_CHECK" '$0 == target {found=1} END {exit found ? 0 : 1}'; then
        return 0
    fi

    if [ -e "$HOME/.agentzero/$NAME_TO_CHECK" ]; then
        return 0
    fi

    return 1
}

suggest_next_instance_name() {
    BASE_NAME="${1:-agent-zero}"
    CANDIDATE_NAME="$BASE_NAME"
    INDEX=2

    while instance_name_taken "$CANDIDATE_NAME"; do
        CANDIDATE_NAME="${BASE_NAME}-${INDEX}"
        INDEX=$((INDEX + 1))
    done

    printf "%s\n" "$CANDIDATE_NAME"
}

open_browser() {
    URL="$1"
    OS_NAME="$(uname -s 2>/dev/null || true)"

    case "$OS_NAME" in
        Darwin)
            if command -v open >/dev/null 2>&1; then
                if open "$URL" >/dev/null 2>&1; then
                    print_ok "Opened browser: $URL"
                else
                    print_warn "Could not open browser automatically. Open this URL manually: $URL"
                fi
            else
                print_warn "open command not found. Open this URL manually: $URL"
            fi
            ;;
        Linux)
            if command -v xdg-open >/dev/null 2>&1; then
                if xdg-open "$URL" >/dev/null 2>&1; then
                    print_ok "Opened browser: $URL"
                else
                    print_warn "Could not open browser automatically. Open this URL manually: $URL"
                fi
            else
                print_warn "xdg-open not found. Open this URL manually: $URL"
            fi
            ;;
        *)
            print_warn "Automatic browser open is not supported on this OS. Open this URL manually: $URL"
            ;;
    esac
}

fetch_available_tags() {
    TAGS_URL="https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=15&ordering=last_updated"
    RAW_TAGS_JSON="$(curl -fsSL "$TAGS_URL" 2>/dev/null || true)"
    PARSED_TAGS=""

    if [ -z "$RAW_TAGS_JSON" ]; then
        return 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        PARSED_TAGS="$(printf "%s" "$RAW_TAGS_JSON" | python3 -c 'import json,sys
try:
    payload=json.load(sys.stdin)
except Exception:
    sys.exit(1)
seen=set()
for item in payload.get("results", []):
    name=item.get("name")
    if not name or name in seen:
        continue
    seen.add(name)
    print(name)
' 2>/dev/null || true)"
    fi

    if [ -z "$PARSED_TAGS" ]; then
        PARSED_TAGS="$(printf "%s\n" "$RAW_TAGS_JSON" | tr ',' '\n' | sed -n 's/^[[:space:]]*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
    fi

    PARSED_TAGS="$(printf "%s\n" "$PARSED_TAGS" | awk 'NF && !seen[$0]++')"

    if [ -z "$PARSED_TAGS" ]; then
        return 1
    fi

    printf "%s\n" "$PARSED_TAGS"
}

select_image_tag() {
    SELECTED_TAG="latest"
    AVAILABLE_TAGS="$(fetch_available_tags || true)"

    echo "Step A - Select image tag:"
    if [ -z "$AVAILABLE_TAGS" ]; then
        print_warn "Could not fetch tags from Docker Hub. Falling back to latest."
        print_info "Image tag: $SELECTED_TAG"
        return 0
    fi

    printf "%s\n" "$AVAILABLE_TAGS" | awk '{printf "  %d) %s\n", NR, $0}'
    printf "Select image tag number [latest]: "
    IFS= read -r TAG_SELECTION

    if [ -z "$TAG_SELECTION" ]; then
        print_info "No tag selected. Using latest."
        print_info "Image tag: $SELECTED_TAG"
        return 0
    fi

    case "$TAG_SELECTION" in
        *[!0-9]*)
            if printf "%s\n" "$AVAILABLE_TAGS" | awk -v selected="$TAG_SELECTION" '$0 == selected {found=1} END {exit found ? 0 : 1}'; then
                SELECTED_TAG="$TAG_SELECTION"
            else
                print_warn "Invalid selection '$TAG_SELECTION'. Falling back to latest."
                SELECTED_TAG="latest"
            fi
            ;;
        *)
            RESOLVED_TAG="$(printf "%s\n" "$AVAILABLE_TAGS" | awk -v n="$TAG_SELECTION" 'NR == n {print; exit}')"
            if [ -z "$RESOLVED_TAG" ]; then
                print_warn "Invalid selection '$TAG_SELECTION'. Falling back to latest."
                SELECTED_TAG="latest"
            else
                SELECTED_TAG="$RESOLVED_TAG"
            fi
            ;;
    esac

    print_info "Image tag: $SELECTED_TAG"
}

create_instance() {
    # -----------------------------------------------------------
    # 2. Gather configuration from user
    # -----------------------------------------------------------
    INSTALL_ROOT="$HOME/.agentzero"
    DEFAULT_PORT="5080"
    DEFAULT_NAME="$(suggest_next_instance_name "agent-zero")"

    # Tag selection
    select_image_tag
    echo ""

    # Container / instance name
    echo "Step B - Container name:"
    printf "Name [%s]: " "$DEFAULT_NAME"
    IFS= read -r CONTAINER_NAME
    CONTAINER_NAME="${CONTAINER_NAME:-$DEFAULT_NAME}"

    if instance_name_taken "$CONTAINER_NAME"; then
        SUGGESTED_NAME="$(suggest_next_instance_name "$CONTAINER_NAME")"
        print_warn "Instance name '$CONTAINER_NAME' is already taken. Using '$SUGGESTED_NAME'."
        CONTAINER_NAME="$SUGGESTED_NAME"
    fi
    print_info "Instance name: $CONTAINER_NAME"

    INSTANCE_DIR="$INSTALL_ROOT/$CONTAINER_NAME"
    DEFAULT_DATA_DIR="$INSTANCE_DIR/usr"

    # Data directory
    echo "Step C - Data directory:"
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
    echo "Step D - Web UI port:"
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
    echo "Step E - Authentication:"
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
    mkdir -p "$INSTANCE_DIR"

    COMPOSE_FILE="$INSTANCE_DIR/docker-compose.yml"

    {
        echo "services:"
        echo "  agent-zero:"
        echo "    image: agent0ai/agent-zero:$SELECTED_TAG"
        echo "    container_name: $CONTAINER_NAME"
        echo "    restart: unless-stopped"
        echo "    ports:"
        echo "      - \"${PORT}:80\""
        echo "    volumes:"
        echo "      - \"${DATA_DIR}:/a0/usr\""
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
    print_info "Pulling Agent Zero image (this may take a moment)..."
    docker compose -f "$COMPOSE_FILE" pull

    print_info "Starting Agent Zero..."
    docker compose -f "$COMPOSE_FILE" up -d

    # -----------------------------------------------------------
    # 5. Done!
    # -----------------------------------------------------------
    echo ""
    echo "=========================================="
    printf "  ${GREEN}${BOLD}Installation Complete!${NC}\n"
    echo "=========================================="
    echo ""
    echo "  🏷️ Image tag      : $SELECTED_TAG"
    echo "  📦 Instance name  : $CONTAINER_NAME"
    echo "  🧩 Compose file   : $COMPOSE_FILE"
    echo "  📁 Data directory : $DATA_DIR"
    echo "  🌐 Web UI         : http://localhost:$PORT"
    if [ -n "$AUTH_LOGIN" ]; then
        echo "  🔐 Authentication : enabled"
        echo "  👤 Login          : $AUTH_LOGIN"
        echo "  🔑 Password       : $AUTH_PASSWORD"
    else
        echo "  🔓 Authentication : none"
    fi
    echo ""
    echo "  Useful commands:"
    echo "    docker compose -f $COMPOSE_FILE logs -f   # View logs"
    echo "    docker compose -f $COMPOSE_FILE down      # Stop"
    echo "    docker compose -f $COMPOSE_FILE up -d     # Start"
    echo "    docker compose -f $COMPOSE_FILE pull      # Update image"
    echo ""
    print_info "Happy automating with Agent Zero! 🤖"
}

manage_instances() {
    CONTAINER_ROWS="$(docker ps -a --filter "ancestor=agent0ai/agent-zero" --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>/dev/null || true)"

    if [ -z "$CONTAINER_ROWS" ]; then
        print_warn "No Agent Zero containers found to manage."
        return 0
    fi

    while :; do
        echo "Step M - Select existing instance:"
        printf "%s\n" "$CONTAINER_ROWS" | awk -F'|' '
            {
                tag=$2
                if (index($2, ":") > 0) {
                    sub(/^.*:/, "", tag)
                } else {
                    tag="latest"
                }
                printf "  %d) %s  [tag: %s]  [status: %s]\n", NR, $1, tag, $3
            }
        '
        printf "Select container number [1]: "
        IFS= read -r CONTAINER_SELECTION
        CONTAINER_SELECTION="${CONTAINER_SELECTION:-1}"

        case "$CONTAINER_SELECTION" in
            ''|*[!0-9]*)
                print_warn "Invalid selection '$CONTAINER_SELECTION'. Please enter a number."
                continue
                ;;
        esac

        SELECTED_ROW="$(printf "%s\n" "$CONTAINER_ROWS" | awk -F'|' -v n="$CONTAINER_SELECTION" 'NR == n {print; exit}')"
        if [ -z "$SELECTED_ROW" ]; then
            print_warn "Selection '$CONTAINER_SELECTION' is out of range."
            continue
        fi

        SELECTED_NAME="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f1)"
        SELECTED_IMAGE="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f2)"
        SELECTED_STATUS="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f3-)"
        print_info "Selected instance: $SELECTED_NAME ($SELECTED_IMAGE, $SELECTED_STATUS)"

        while :; do
            echo "1) Open in browser"
            echo "2) Start"
            echo "3) Stop"
            echo "4) Back/Exit manage menu"
            printf "Choose an option [4]: "
            IFS= read -r ACTION_OPTION
            ACTION_OPTION="${ACTION_OPTION:-4}"

            case "$ACTION_OPTION" in
                1)
                    PORT_OUTPUT="$(docker port "$SELECTED_NAME" 80/tcp 2>/dev/null || true)"
                    HOST_PORT="$(printf "%s\n" "$PORT_OUTPUT" | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p' | head -n 1)"

                    if [ -z "$HOST_PORT" ]; then
                        print_warn "Could not resolve a host port for '$SELECTED_NAME' on 80/tcp. Ensure it is running with a published port."
                    else
                        TARGET_URL="http://localhost:$HOST_PORT"
                        print_info "Opening $TARGET_URL"
                        open_browser "$TARGET_URL"
                    fi
                    ;;
                2)
                    print_info "Starting '$SELECTED_NAME'..."
                    if docker start "$SELECTED_NAME" >/dev/null 2>&1; then
                        print_ok "Started '$SELECTED_NAME'."
                    else
                        print_error "Failed to start '$SELECTED_NAME'."
                    fi
                    ;;
                3)
                    print_info "Stopping '$SELECTED_NAME'..."
                    if docker stop "$SELECTED_NAME" >/dev/null 2>&1; then
                        print_ok "Stopped '$SELECTED_NAME'."
                    else
                        print_error "Failed to stop '$SELECTED_NAME'."
                    fi
                    ;;
                4)
                    return 0
                    ;;
                *)
                    print_warn "Invalid action '$ACTION_OPTION'. Choose 1, 2, 3, or 4."
                    ;;
            esac
        done
    done
}

main_menu_for_existing() {
    RUNNING_COUNT="$1"
    print_info "Detected ${RUNNING_COUNT} running Agent Zero container(s)."
    echo "1) Install new instance"
    echo "2) Manage existing instances"
    printf "Choose an option [1]: "
    IFS= read -r MENU_OPTION
    MENU_OPTION="${MENU_OPTION:-1}"

    case "$MENU_OPTION" in
        2) manage_instances ;;
        *) create_instance ;;
    esac
}

main() {
    check_docker
    echo ""

    RUNNING_COUNT="$(count_running_agent_zero_containers)"
    case "$RUNNING_COUNT" in
        ''|*[!0-9]*) RUNNING_COUNT="0" ;;
    esac

    if [ "$RUNNING_COUNT" -gt 0 ]; then
        main_menu_for_existing "$RUNNING_COUNT"
    else
        create_instance
    fi
}

main "$@"

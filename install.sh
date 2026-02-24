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

select_from_menu() {
    # Check for header parameter (starts with --header=)
    MENU_HEADER=""
    if [ $# -gt 0 ] && [ "${1#--header=}" != "$1" ]; then
        MENU_HEADER="${1#--header=}"
        shift
    fi

    # Validate at least one option provided
    if [ $# -eq 0 ]; then
        print_error "select_from_menu requires at least one menu option"
        exit 1
    fi

    ITEM_COUNT=$#
    SELECTED_INDEX=0

    while :; do
        # Clear screen
        clear >/dev/tty 2>&1

        # Display header if provided
        if [ -n "$MENU_HEADER" ]; then
            echo "$MENU_HEADER" >/dev/tty
            echo "" >/dev/tty
        fi

        # Render menu items
        CURRENT_INDEX=0
        for item in "$@"; do
            if [ "$CURRENT_INDEX" -eq "$SELECTED_INDEX" ]; then
                printf "  ${GREEN}> %s${NC}\n" "$item" >/dev/tty
            else
                printf "    %s\n" "$item" >/dev/tty
            fi
            CURRENT_INDEX=$((CURRENT_INDEX + 1))
        done

        # Show help text
        echo "" >/dev/tty
        printf "Use ↑/↓ arrows to navigate, Enter to select\n" >/dev/tty

        # Read single character from terminal
        IFS= read -rsn1 key </dev/tty

        # Handle Enter key (empty read or newline)
        if [ -z "$key" ] || [ "$key" = $'\n' ]; then
            printf "%d\n" "$SELECTED_INDEX"
            return 0
        fi

        # Handle escape sequences (arrow keys)
        if [ "$key" = $'\x1b' ]; then
            # Read next character
            IFS= read -rsn1 key2 </dev/tty
            if [ "$key2" = "[" ]; then
                # Read arrow key identifier
                IFS= read -rsn1 key3 </dev/tty
                case "$key3" in
                    A) # Up arrow
                        SELECTED_INDEX=$((SELECTED_INDEX - 1))
                        if [ "$SELECTED_INDEX" -lt 0 ]; then
                            SELECTED_INDEX=$((ITEM_COUNT - 1))
                        fi
                        ;;
                    B) # Down arrow
                        SELECTED_INDEX=$((SELECTED_INDEX + 1))
                        if [ "$SELECTED_INDEX" -ge "$ITEM_COUNT" ]; then
                            SELECTED_INDEX=0
                        fi
                        ;;
                esac
            fi
        fi
    done
}

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

count_existing_agent_zero_containers() {
    docker ps -a --filter "ancestor=agent0ai/agent-zero" --format '{{.Names}}' 2>/dev/null | awk 'NF {count++} END {print count+0}'
}

instance_name_taken() {
    NAME_TO_CHECK="$1"

    if docker ps -a --format '{{.Names}}' 2>/dev/null | awk -v target="$NAME_TO_CHECK" '$0 == target {found=1} END {exit found ? 0 : 1}'; then
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
    TAGS_URL="https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=5&ordering=last_updated"
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
    AVAILABLE_TAGS="$(printf "%s\n" "$AVAILABLE_TAGS" | awk 'tolower($0) != "latest"')"

    if [ -z "$AVAILABLE_TAGS" ]; then
        echo "Select image tag:"
        print_warn "No additional tags found. Using latest."
        print_info "Image tag: $SELECTED_TAG"
        echo ""
        return 0
    fi

    # Build menu with "latest" as first option
    SELECTED_INDEX=$(select_from_menu "--header=Select image tag:" "latest" $AVAILABLE_TAGS)

    # Extract the selected tag
    if [ "$SELECTED_INDEX" -eq 0 ]; then
        SELECTED_TAG="latest"
    else
        SELECTED_TAG=$(printf "%s\n" "$AVAILABLE_TAGS" | awk -v n="$SELECTED_INDEX" 'NR == n {print; exit}')
    fi

    print_info "Image tag: $SELECTED_TAG"
    echo ""
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
    echo "Container name:"
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
    echo "Data directory:"
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
    echo "Web UI port:"
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
    echo "Authentication:"
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
    while :; do
        CONTAINER_ROWS="$(docker ps -a --filter "ancestor=agent0ai/agent-zero" --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>/dev/null || true)"

        if [ -z "$CONTAINER_ROWS" ]; then
            print_warn "No Agent Zero containers found to manage."
            return 0
        fi

        # Build menu by manually rendering and handling arrow keys inline
        ITEM_COUNT=$(printf "%s\n" "$CONTAINER_ROWS" | awk 'END {print NR}')
        SELECTED_INDEX=0

        while :; do
            # Clear screen
            clear

            # Display header
            echo "Select existing instance:" >/dev/tty
            echo "" >/dev/tty

            # Render menu items
            printf "%s\n" "$CONTAINER_ROWS" | awk -F'|' -v sel="$SELECTED_INDEX" '
            {
                tag=$2
                if (index($2, ":") > 0) {
                    sub(/^.*:/, "", tag)
                } else {
                    tag="latest"
                }
                option = sprintf("%s [tag: %s] [status: %s]", $1, tag, $3)
                if (NR - 1 == sel) {
                    printf "  \033[0;32m> %s\033[0m\n", option
                } else {
                    printf "    %s\n", option
                }
            }' >/dev/tty

            # Show help text
            echo "" >/dev/tty
            printf "Use ↑/↓ arrows to navigate, Enter to select\n" >/dev/tty

            # Read single character from terminal
            IFS= read -rsn1 key </dev/tty

            # Handle Enter key
            if [ -z "$key" ] || [ "$key" = $'\n' ]; then
                break
            fi

            # Handle escape sequences (arrow keys)
            if [ "$key" = $'\x1b' ]; then
                IFS= read -rsn1 key2 </dev/tty
                if [ "$key2" = "[" ]; then
                    IFS= read -rsn1 key3 </dev/tty
                    case "$key3" in
                        A) # Up arrow
                            SELECTED_INDEX=$((SELECTED_INDEX - 1))
                            if [ "$SELECTED_INDEX" -lt 0 ]; then
                                SELECTED_INDEX=$((ITEM_COUNT - 1))
                            fi
                            ;;
                        B) # Down arrow
                            SELECTED_INDEX=$((SELECTED_INDEX + 1))
                            if [ "$SELECTED_INDEX" -ge "$ITEM_COUNT" ]; then
                                SELECTED_INDEX=0
                            fi
                            ;;
                    esac
                fi
            fi
        done

        # Extract container details using selected index
        SELECTED_ROW="$(printf "%s\n" "$CONTAINER_ROWS" | awk -v n="$((SELECTED_INDEX + 1))" 'NR == n {print; exit}')"
        SELECTED_NAME="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f1)"
        SELECTED_IMAGE="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f2)"
        SELECTED_STATUS="$(printf "%s\n" "$SELECTED_ROW" | cut -d'|' -f3-)"

        while :; do
            SELECTED_STATUS="$(docker ps -a --filter "name=^/${SELECTED_NAME}$" --format '{{.Status}}' 2>/dev/null | head -n 1)"
            case "$SELECTED_STATUS" in
                Up*) IS_RUNNING=1 ;;
                *) IS_RUNNING=0 ;;
            esac

            INSTANCE_HEADER="Selected: $SELECTED_NAME ($SELECTED_IMAGE, $SELECTED_STATUS)"

            if [ "$IS_RUNNING" -eq 1 ]; then
                ACTION_INDEX=$(select_from_menu "--header=$INSTANCE_HEADER" "Open in browser" "Stop" "Back/Exit manage menu")
                case "$ACTION_INDEX" in
                    0) ACTION_KEY="open" ;;
                    1) ACTION_KEY="stop" ;;
                    2) ACTION_KEY="back" ;;
                    *) ACTION_KEY="invalid" ;;
                esac
            else
                ACTION_INDEX=$(select_from_menu "--header=$INSTANCE_HEADER" "Start" "Back/Exit manage menu")
                case "$ACTION_INDEX" in
                    0) ACTION_KEY="start" ;;
                    1) ACTION_KEY="back" ;;
                    *) ACTION_KEY="invalid" ;;
                esac
            fi

            case "$ACTION_KEY" in
                open)
                    PORT_OUTPUT="$(docker port "$SELECTED_NAME" 80/tcp 2>/dev/null || true)"
                    HOST_PORT="$(printf "%s\n" "$PORT_OUTPUT" | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p' | head -n 1)"

                    if [ -z "$HOST_PORT" ]; then
                        print_warn "Could not resolve a host port for '$SELECTED_NAME' on 80/tcp. Ensure it is running with a published port."
                    else
                        TARGET_URL="http://localhost:$HOST_PORT"
                        print_info "Opening $TARGET_URL"
                        open_browser "$TARGET_URL"
                    fi
                    echo ""
                    ;;
                start)
                    print_info "Starting '$SELECTED_NAME'..."
                    if docker start "$SELECTED_NAME" >/dev/null 2>&1; then
                        print_ok "Started '$SELECTED_NAME'."
                    else
                        print_error "Failed to start '$SELECTED_NAME'."
                    fi
                    echo ""
                    ;;
                stop)
                    print_info "Stopping '$SELECTED_NAME'..."
                    if docker stop "$SELECTED_NAME" >/dev/null 2>&1; then
                        print_ok "Stopped '$SELECTED_NAME'."
                    else
                        print_error "Failed to stop '$SELECTED_NAME'."
                    fi
                    echo ""
                    ;;
                back)
                    return 0
                    ;;
                *)
                    print_warn "Invalid action. Please try again."
                    echo ""
                    ;;
            esac
        done
    done
}

main_menu_for_existing() {
    EXISTING_COUNT="$1"
    HEADER="Detected ${EXISTING_COUNT} Agent Zero container(s). What would you like to do?"

    SELECTED_INDEX=$(select_from_menu "--header=$HEADER" "Install new instance" "Manage existing instances")

    case "$SELECTED_INDEX" in
        0) create_instance ;;
        1) manage_instances ;;
        *) create_instance ;;
    esac
}

main() {
    check_docker
    echo ""

    EXISTING_COUNT="$(count_existing_agent_zero_containers)"
    case "$EXISTING_COUNT" in
        ''|*[!0-9]*) EXISTING_COUNT="0" ;;
    esac

    if [ "$EXISTING_COUNT" -gt 0 ]; then
        main_menu_for_existing "$EXISTING_COUNT"
    else
        create_instance
    fi
}

main "$@"

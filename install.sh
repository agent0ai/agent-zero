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

print_banner() {
    printf "%b" "${BLUE}"
    cat <<'EOF'
 █████╗   ██████╗ ███████╗███╗   ██╗████████╗   ███████╗███████╗██████╗  ██████╗ 
██╔══██╗ ██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝   ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗
███████║ ██║  ███╗█████╗  ██╔██╗ ██║   ██║        ███╔╝ █████╗  ██████╔╝██║   ██║
██╔══██║ ██║   ██║██╔══╝  ██║╚██╗██║   ██║       ███╔╝  ██╔══╝  ██╔══██╗██║   ██║
██║  ██║ ╚██████╔╝███████╗██║ ╚████║   ██║      ███████╗███████╗██║  ██║╚██████╔╝
╚═╝  ╚═╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
EOF
    printf "%b\n" "${NC}"
}

print_banner

print_ok()    { printf "  ${GREEN}✔${NC} %s\n" "$1"; }
print_info()  { printf "${GREEN}[INFO]${NC} %s\n" "$1"; }
print_warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
print_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }

wait_for_keypress() {
    printf "\nPress any key to continue..."
    IFS= read -rsn1 _key </dev/tty
}

# Check whether a TCP port is in use on localhost.
# Uses a fallback chain: lsof → nc → /dev/tcp (for broad OS compatibility).
# Also checks Docker container port mappings directly.
# Returns 0 if in use, 1 if free.
is_port_in_use() {
    CHECK_PORT="$1"

    # Check Docker-published ports (covers stopped containers with port reservations too)
    DOCKER_PORTS="$(docker ps -a --format '{{.Ports}}' 2>/dev/null || true)"
    if [ -n "$DOCKER_PORTS" ]; then
        if printf "%s\n" "$DOCKER_PORTS" | grep -qE "(^|[ ,])0\.0\.0\.0:${CHECK_PORT}->" 2>/dev/null; then
            return 0
        fi
        if printf "%s\n" "$DOCKER_PORTS" | grep -qE "(^|[ ,]):::${CHECK_PORT}->" 2>/dev/null; then
            return 0
        fi
    fi

    # System-level check via lsof (macOS + Linux)
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i ":${CHECK_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
            return 0
        fi
        return 1
    fi

    # Fallback: nc (netcat)
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$CHECK_PORT" >/dev/null 2>&1; then
            return 0
        fi
        return 1
    fi

    # Last resort: assume free
    return 1
}

# Find the first free port starting from a given base.
find_free_port() {
    BASE_PORT="${1:-5080}"
    CANDIDATE_PORT="$BASE_PORT"
    MAX_ATTEMPTS=100

    ATTEMPT=0
    while [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; do
        if ! is_port_in_use "$CANDIDATE_PORT"; then
            printf "%d\n" "$CANDIDATE_PORT"
            return 0
        fi
        CANDIDATE_PORT=$((CANDIDATE_PORT + 1))
        ATTEMPT=$((ATTEMPT + 1))
    done

    # If we exhausted attempts, return the base port and let Docker report the conflict
    printf "%d\n" "$BASE_PORT"
}

# Escape-aware text input. Reads one line with support for:
#   - Normal character input and Backspace for editing
#   - Escape key to abort (prints nothing, returns 1)
#   - Enter to submit (prints the entered text, returns 0)
# Usage: VALUE=$(read_input) || return 1
read_input() {
    INPUT_BUF=""

    while :; do
        # Read a single character (raw, no echo)
        IFS= read -rsn1 INPUT_CHAR </dev/tty

        # Handle Enter key (empty read)
        if [ -z "$INPUT_CHAR" ]; then
            printf "\n" >/dev/tty
            printf "%s\n" "$INPUT_BUF"
            return 0
        fi

        # Handle Escape key
        if [ "$INPUT_CHAR" = $'\x1b' ]; then
            # Consume any trailing escape sequence chars (arrow keys etc.)
            # Note: -t only supports integer seconds in /bin/sh, so we use -t 1.
            IFS= read -rsn1 -t 1 _discard </dev/tty 2>/dev/null || true
            if [ "$_discard" = "[" ]; then
                IFS= read -rsn1 -t 1 _discard2 </dev/tty 2>/dev/null || true
            fi
            printf "\n" >/dev/tty
            return 1
        fi

        # Handle Backspace (0x7f or 0x08)
        if [ "$INPUT_CHAR" = $'\x7f' ] || [ "$INPUT_CHAR" = $'\x08' ]; then
            if [ -n "$INPUT_BUF" ]; then
                INPUT_BUF="${INPUT_BUF%?}"
                # Move cursor back, overwrite with space, move back again
                printf "\b \b" >/dev/tty
            fi
            continue
        fi

        # Regular printable character — append to buffer and echo
        INPUT_BUF="${INPUT_BUF}${INPUT_CHAR}"
        printf "%s" "$INPUT_CHAR" >/dev/tty
    done
}

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
        print_banner >/dev/tty

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
        printf "Use ↑/↓ to navigate, Enter to select, Esc to go back\n" >/dev/tty

        # Read single character from terminal
        IFS= read -rsn1 key </dev/tty

        # Handle Enter key (empty read or newline)
        if [ -z "$key" ] || [ "$key" = $'\n' ]; then
            printf "%d\n" "$SELECTED_INDEX"
            return 0
        fi

        # Handle Backspace key (go back)
        if [ "$key" = $'\x7f' ] || [ "$key" = $'\x08' ]; then
            printf "%s\n" "-1"
            return 1
        fi

        # Handle escape sequences (arrow keys) and bare Escape (go back)
        if [ "$key" = $'\x1b' ]; then
            # Read next character with timeout to distinguish bare Escape from arrow keys.
            # Arrow key sequences (\x1b[A) arrive instantly; bare Escape has no follow-up.
            # Note: -t only supports integer seconds in /bin/sh, so we use -t 1.
            IFS= read -rsn1 -t 1 key2 </dev/tty 2>/dev/null || true
            if [ -z "$key2" ]; then
                # Bare Escape pressed (no follow-up char within timeout) — go back
                printf "%s\n" "-1"
                return 1
            elif [ "$key2" = "[" ]; then
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
    TAGS_URL="https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=20&ordering=last_updated"
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
    ALL_TAGS="$(fetch_available_tags || true)"

    if [ -z "$ALL_TAGS" ]; then
        echo "Select version:"
        print_warn "No additional tags found. Using latest."
        print_info "Selected version: $SELECTED_TAG"
        echo ""
        return 0
    fi

    # Build ordered tag list:
    #   1. Pinned tags (latest, testing, development) — only if they exist
    #   2. Up to 5 additional tags from newest, excluding pinned ones
    PINNED_TAGS=""
    for PIN_TAG in latest testing development; do
        if printf "%s\n" "$ALL_TAGS" | awk -v tag="$PIN_TAG" '$0 == tag {found=1; exit} END {exit found ? 0 : 1}'; then
            PINNED_TAGS="${PINNED_TAGS:+${PINNED_TAGS}
}${PIN_TAG}"
        fi
    done

    # Get remaining tags (exclude pinned), take first 5 (already sorted newest-first from API)
    OTHER_TAGS="$(printf "%s\n" "$ALL_TAGS" | awk '
        $0 == "latest" || $0 == "testing" || $0 == "development" { next }
        count < 5 { print; count++ }
    ')"

    # Combine pinned + other into final menu list
    MENU_TAGS=""
    if [ -n "$PINNED_TAGS" ]; then
        MENU_TAGS="$PINNED_TAGS"
    fi
    if [ -n "$OTHER_TAGS" ]; then
        MENU_TAGS="${MENU_TAGS:+${MENU_TAGS}
}${OTHER_TAGS}"
    fi

    if [ -z "$MENU_TAGS" ]; then
        echo "Select version:"
        print_warn "No tags found. Using latest."
        print_info "Selected version: $SELECTED_TAG"
        echo ""
        return 0
    fi

    # Build menu from the tag list
    # shellcheck disable=SC2086
    SELECTED_INDEX=$(select_from_menu "--header=Select version:" $MENU_TAGS) || true

    # Handle go-back
    if [ "$SELECTED_INDEX" = "-1" ]; then
        return 1
    fi

    # Extract the selected tag (0-indexed)
    SELECTED_TAG="$(printf "%s\n" "$MENU_TAGS" | awk -v n="$((SELECTED_INDEX + 1))" 'NR == n {print; exit}')"

    if [ -z "$SELECTED_TAG" ]; then
        SELECTED_TAG="latest"
    fi

    print_info "Selected version: $SELECTED_TAG"
    echo ""
}

create_instance() {
    # -----------------------------------------------------------
    # 2. Gather configuration from user
    # -----------------------------------------------------------
    INSTALL_ROOT="$HOME/.agentzero"
    DEFAULT_PORT="$(find_free_port 5080)"
    DEFAULT_NAME="$(suggest_next_instance_name "agent-zero")"

    # Tag selection (Escape aborts create_instance)
    if ! select_image_tag; then
        return 1
    fi

    # Container / instance name
    echo ""
    printf "${BOLD}What should this instance be called?${NC} (Esc to go back)\n"
    printf "Leave empty to use default [%s]: " "$DEFAULT_NAME"
    CONTAINER_NAME=$(read_input) || return 1
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
    echo ""
    printf "${BOLD}Where should Agent Zero store user data?${NC} (Esc to go back)\n"
    printf "Leave empty to use default [%s]: " "$DEFAULT_DATA_DIR"
    DATA_DIR=$(read_input) || return 1
    DATA_DIR="${DATA_DIR:-$DEFAULT_DATA_DIR}"
    case "$DATA_DIR" in
        ~/*) DATA_DIR="$HOME/${DATA_DIR#~/}" ;;
        ~) DATA_DIR="$HOME" ;;
    esac
    mkdir -p "$DATA_DIR"
    print_info "Data directory: $DATA_DIR"

    # Port
    echo ""
    printf "${BOLD}What port should Agent Zero Web UI run on?${NC} (Esc to go back)\n"
    printf "Leave empty to use default [%s]: " "$DEFAULT_PORT"
    PORT=$(read_input) || return 1
    PORT="${PORT:-$DEFAULT_PORT}"
    case "$PORT" in
        ''|*[!0-9]*)
        print_error "Invalid port. Falling back to ${DEFAULT_PORT}."
        PORT="$DEFAULT_PORT"
        ;;
    esac
    print_info "Web UI port: $PORT"

    # Authentication
    echo ""
    printf "${BOLD}What login username should be used for the Web UI?${NC} (Esc to go back)\n"
    printf "Leave empty for no authentication: "
    AUTH_LOGIN=$(read_input) || return 1
    AUTH_PASSWORD=""
    if [ -n "$AUTH_LOGIN" ]; then
        echo ""
        printf "${BOLD}What password should be used?${NC} (Esc to go back)\n"
        printf "Leave empty to use default [12345678]: "
        AUTH_PASSWORD=$(read_input) || return 1
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
            print_banner >/dev/tty

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
            printf "Use ↑/↓ to navigate, Enter to select, Esc to go back\n" >/dev/tty

            # Read single character from terminal
            IFS= read -rsn1 key </dev/tty

            # Handle Enter key
            if [ -z "$key" ] || [ "$key" = $'\n' ]; then
                break
            fi

            # Handle Backspace key (go back)
            if [ "$key" = $'\x7f' ] || [ "$key" = $'\x08' ]; then
                return 0
            fi

            # Handle escape sequences (arrow keys) and bare Escape (go back)
            if [ "$key" = $'\x1b' ]; then
                IFS= read -rsn1 -t 1 key2 </dev/tty 2>/dev/null || true
                if [ -z "$key2" ]; then
                    # Bare Escape pressed — go back to main menu
                    return 0
                elif [ "$key2" = "[" ]; then
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

            # If container no longer exists (e.g. after delete), go back to instance list
            if [ -z "$SELECTED_STATUS" ]; then
                break
            fi

            case "$SELECTED_STATUS" in
                Up*) IS_RUNNING=1 ;;
                *) IS_RUNNING=0 ;;
            esac

            INSTANCE_HEADER="Selected: $SELECTED_NAME ($SELECTED_IMAGE, $SELECTED_STATUS)"

            if [ "$IS_RUNNING" -eq 1 ]; then
                ACTION_INDEX=$(select_from_menu "--header=$INSTANCE_HEADER" "Open in browser" "Restart" "Stop" "Delete" "Back") || true
                case "$ACTION_INDEX" in
                    -1) ACTION_KEY="back" ;;  # Escape/Backspace — go back to instance list
                    0) ACTION_KEY="open" ;;
                    1) ACTION_KEY="restart" ;;
                    2) ACTION_KEY="stop" ;;
                    3) ACTION_KEY="delete" ;;
                    4) ACTION_KEY="back" ;;
                    *) ACTION_KEY="invalid" ;;
                esac
            else
                ACTION_INDEX=$(select_from_menu "--header=$INSTANCE_HEADER" "Start" "Delete" "Back") || true
                case "$ACTION_INDEX" in
                    -1) ACTION_KEY="back" ;;  # Escape/Backspace — go back to instance list
                    0) ACTION_KEY="start" ;;
                    1) ACTION_KEY="delete" ;;
                    2) ACTION_KEY="back" ;;
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
                    wait_for_keypress
                    ;;
                start)
                    print_info "Starting '$SELECTED_NAME'..."
                    START_OUTPUT="$(docker start "$SELECTED_NAME" 2>&1)" || true
                    if docker ps --filter "name=^/${SELECTED_NAME}$" --filter "status=running" --format '{{.Names}}' 2>/dev/null | grep -q "^${SELECTED_NAME}$"; then
                        print_ok "Started '$SELECTED_NAME'."
                    else
                        print_error "Failed to start '$SELECTED_NAME'."
                        if [ -n "$START_OUTPUT" ]; then
                            printf "  %s\n" "$START_OUTPUT"
                        fi
                    fi
                    wait_for_keypress
                    ;;
                stop)
                    print_info "Stopping '$SELECTED_NAME'..."
                    if docker stop "$SELECTED_NAME" >/dev/null 2>&1; then
                        print_ok "Stopped '$SELECTED_NAME'."
                    else
                        print_error "Failed to stop '$SELECTED_NAME'."
                    fi
                    wait_for_keypress
                    ;;
                restart)
                    print_info "Restarting '$SELECTED_NAME'..."
                    RESTART_OUTPUT="$(docker restart "$SELECTED_NAME" 2>&1)" || true
                    if docker ps --filter "name=^/${SELECTED_NAME}$" --filter "status=running" --format '{{.Names}}' 2>/dev/null | grep -q "^${SELECTED_NAME}$"; then
                        print_ok "Restarted '$SELECTED_NAME'."
                    else
                        print_error "Failed to restart '$SELECTED_NAME'."
                        if [ -n "$RESTART_OUTPUT" ]; then
                            printf "  %s\n" "$RESTART_OUTPUT"
                        fi
                    fi
                    wait_for_keypress
                    ;;
                delete)
                    printf "Are you sure you want to delete '%s'? [y/N]: " "$SELECTED_NAME"
                    IFS= read -rsn1 CONFIRM </dev/tty
                    printf "\n"
                    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
                        # Stop first if running
                        docker stop "$SELECTED_NAME" >/dev/null 2>&1 || true
                        if docker rm "$SELECTED_NAME" >/dev/null 2>&1; then
                            print_ok "Deleted '$SELECTED_NAME'."
                        else
                            print_error "Failed to delete '$SELECTED_NAME'."
                        fi
                        wait_for_keypress
                        break  # Back to instance list (container no longer exists)
                    else
                        print_info "Delete cancelled."
                        wait_for_keypress
                    fi
                    ;;
                back)
                    break  # Break inner loop, go back to instance selection
                    ;;
                *)
                    print_warn "Invalid action. Please try again."
                    wait_for_keypress
                    ;;
            esac
        done
    done
}

main_menu_for_existing() {
    while :; do
        # Re-count containers each iteration (may change after delete/create)
        MENU_COUNT="$(count_existing_agent_zero_containers)"
        case "$MENU_COUNT" in
            ''|*[!0-9]*) MENU_COUNT="0" ;;
        esac

        if [ "$MENU_COUNT" -gt 0 ]; then
            HEADER="Detected ${MENU_COUNT} Agent Zero container(s). What would you like to do?"
            SELECTED_INDEX=$(select_from_menu "--header=$HEADER" "Install new instance" "Manage existing instances" "Exit") || true

            case "$SELECTED_INDEX" in
                -1) exit 0 ;;    # Escape/Backspace — exit
                0)
                    if create_instance; then
                        return 0  # Install completed successfully
                    fi
                    # Escape pressed during create — loop back to menu
                    ;;
                1) manage_instances ;;  # loops back to this menu after returning
                2) exit 0 ;;     # Exit option
                *) exit 0 ;;
            esac
        else
            # All containers were deleted — go straight to install
            if ! create_instance; then
                exit 0
            fi
            return 0
        fi
    done
}

main() {
    check_docker
    echo ""

    EXISTING_COUNT="$(count_existing_agent_zero_containers)"
    case "$EXISTING_COUNT" in
        ''|*[!0-9]*) EXISTING_COUNT="0" ;;
    esac

    if [ "$EXISTING_COUNT" -gt 0 ]; then
        main_menu_for_existing
    else
        # No existing containers — go straight to install.
        # If Escape pressed during create, exit gracefully.
        if ! create_instance; then
            exit 0
        fi
    fi
}

main "$@"

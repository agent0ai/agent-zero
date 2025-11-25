#!/bin/bash
# =============================================================================
# Qdrant Knowledge Base Setup Script
# =============================================================================
# This script initializes the Qdrant knowledge base for Unity projects
# Run this inside the agent-zero-unity container
#
# Usage:
#   docker exec -it agent-zero-unity /a0/scripts/setup-qdrant-kb.sh
#
# Or from host:
#   ./scripts/setup-qdrant-kb.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QDRANT_URL="${QDRANT_URL:-http://qdrant-unity:6333}"
COLLECTION_NAME="${COLLECTION_NAME:-unity_project_kb}"
VECTOR_SIZE="${VECTOR_SIZE:-384}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Qdrant Knowledge Base Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to check Qdrant connectivity
check_qdrant() {
    echo -e "${YELLOW}Checking Qdrant connectivity...${NC}"

    # Try curl first
    if command -v curl &> /dev/null; then
        if curl -sf "${QDRANT_URL}/" > /dev/null 2>&1; then
            echo -e "${GREEN}  Qdrant is accessible at ${QDRANT_URL}${NC}"
            return 0
        fi
    fi

    # Try Python requests
    if python3 -c "import requests; r = requests.get('${QDRANT_URL}/'); assert r.status_code == 200" 2>/dev/null; then
        echo -e "${GREEN}  Qdrant is accessible at ${QDRANT_URL}${NC}"
        return 0
    fi

    echo -e "${RED}  Cannot connect to Qdrant at ${QDRANT_URL}${NC}"
    echo -e "${RED}  Make sure Qdrant is running and accessible${NC}"
    return 1
}

# Function to check if collection exists
check_collection() {
    echo -e "${YELLOW}Checking if collection '${COLLECTION_NAME}' exists...${NC}"

    response=$(curl -sf "${QDRANT_URL}/collections/${COLLECTION_NAME}" 2>/dev/null || echo '{"status":"not_found"}')

    if echo "$response" | grep -q '"status":"green"'; then
        echo -e "${GREEN}  Collection exists and is healthy${NC}"

        # Get point count
        point_count=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
        echo -e "${BLUE}  Current points: ${point_count}${NC}"
        return 0
    else
        echo -e "${YELLOW}  Collection does not exist${NC}"
        return 1
    fi
}

# Function to create collection
create_collection() {
    echo -e "${YELLOW}Creating collection '${COLLECTION_NAME}'...${NC}"

    # Collection configuration
    config='{
        "vectors": {
            "text-dense": {
                "size": '"${VECTOR_SIZE}"',
                "distance": "Cosine"
            }
        },
        "sparse_vectors": {
            "text-sparse": {
                "index": {
                    "on_disk": false
                }
            }
        },
        "optimizers_config": {
            "indexing_threshold": 20000
        },
        "hnsw_config": {
            "m": 32,
            "ef_construct": 256
        }
    }'

    response=$(curl -sf -X PUT "${QDRANT_URL}/collections/${COLLECTION_NAME}" \
        -H "Content-Type: application/json" \
        -d "$config" 2>/dev/null)

    if echo "$response" | grep -q '"status":"ok"'; then
        echo -e "${GREEN}  Collection created successfully${NC}"
    else
        echo -e "${RED}  Failed to create collection${NC}"
        echo -e "${RED}  Response: ${response}${NC}"
        return 1
    fi
}

# Function to create payload indexes
create_indexes() {
    echo -e "${YELLOW}Creating payload indexes...${NC}"

    indexes=("asset_guid:keyword" "assembly_name:keyword" "code_type:keyword" "class_name:keyword" "file_path:text")

    for index_def in "${indexes[@]}"; do
        field_name="${index_def%%:*}"
        field_type="${index_def##*:}"

        payload='{
            "field_name": "'"${field_name}"'",
            "field_schema": "'"${field_type}"'"
        }'

        response=$(curl -sf -X PUT "${QDRANT_URL}/collections/${COLLECTION_NAME}/index" \
            -H "Content-Type: application/json" \
            -d "$payload" 2>/dev/null)

        if echo "$response" | grep -q '"status":"ok"'; then
            echo -e "${GREEN}    Index created: ${field_name} (${field_type})${NC}"
        else
            echo -e "${YELLOW}    Index ${field_name} may already exist${NC}"
        fi
    done
}

# Function to verify setup
verify_setup() {
    echo -e "${YELLOW}Verifying setup...${NC}"

    response=$(curl -sf "${QDRANT_URL}/collections/${COLLECTION_NAME}" 2>/dev/null)

    echo ""
    echo -e "${BLUE}Collection Info:${NC}"
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin).get('result', {})
print(f\"  Name: ${COLLECTION_NAME}\")
print(f\"  Status: {data.get('status', 'unknown')}\")
print(f\"  Points: {data.get('points_count', 0)}\")
print(f\"  Segments: {data.get('segments_count', 0)}\")
vectors = data.get('config', {}).get('params', {}).get('vectors', {})
for name, cfg in vectors.items() if isinstance(vectors, dict) else []:
    print(f\"  Vector '{name}': {cfg.get('size', 'N/A')}d, {cfg.get('distance', 'N/A')}\")
" 2>/dev/null || echo "  (Unable to parse collection info)"
}

# Function to install Python dependencies
install_deps() {
    echo -e "${YELLOW}Checking Python dependencies...${NC}"

    deps=("requests" "sentence-transformers" "qdrant-client")
    missing_deps=()

    for dep in "${deps[@]}"; do
        if ! python3 -c "import ${dep//-/_}" 2>/dev/null; then
            missing_deps+=("$dep")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${YELLOW}Installing missing dependencies: ${missing_deps[*]}${NC}"
        pip install --quiet "${missing_deps[@]}" 2>/dev/null || {
            echo -e "${RED}Failed to install some dependencies${NC}"
            echo -e "${YELLOW}Try: pip install ${missing_deps[*]}${NC}"
        }
    else
        echo -e "${GREEN}  All dependencies installed${NC}"
    fi
}

# Main execution
main() {
    echo ""

    # Step 1: Check Qdrant connectivity
    if ! check_qdrant; then
        exit 1
    fi
    echo ""

    # Step 2: Check/Create collection
    if ! check_collection; then
        create_collection
        echo ""
        create_indexes
    fi
    echo ""

    # Step 3: Install dependencies
    install_deps
    echo ""

    # Step 4: Verify setup
    verify_setup

    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}  Setup Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. Run ingestion: python3 /a0/ingest_to_qdrant.py"
    echo -e "  2. Verify via dashboard: http://localhost:6333/dashboard"
    echo -e "  3. Test MCP: Use qdrant_admin.qdrant_get_collection_info"
    echo ""
}

main "$@"

#!/bin/bash

#
# TDD Swarm Worktree Setup
# Creates isolated git worktrees for parallel testing contexts
# Usage: ./scripts/setup_tdd_worktrees.sh [create|clean|list]
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREES_DIR="$PROJECT_ROOT/.worktrees"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_usage() {
    echo -e "${BLUE}TDD Swarm Worktree Manager${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  create   - Create TDD test worktrees"
    echo "  clean    - Clean up worktrees"
    echo "  list     - List active worktrees"
    echo ""
}

create_worktrees() {
    echo -e "${BLUE}🌳 Creating TDD Swarm worktrees...${NC}"

    cd "$PROJECT_ROOT"

    # Create worktrees directory
    mkdir -p "$WORKTREES_DIR"

    # Worktree contexts
    WORKTREES=(
        "unit-tests:unit testing contexts"
        "integration-tests:integration testing contexts"
        "adapter-tests:provider adapter testing"
        "sync-tests:data sync testing"
    )

    for worktree_spec in "${WORKTREES[@]}"; do
        IFS=":" read -r worktree_name description <<< "$worktree_spec"
        worktree_path="$WORKTREES_DIR/$worktree_name"

        if [ -d "$worktree_path" ]; then
            echo -e "${YELLOW}ℹ️  Worktree already exists: $worktree_name${NC}"
        else
            echo -e "${BLUE}📝 Creating worktree: $worktree_name ($description)${NC}"
            git worktree add "$worktree_path" main 2>/dev/null || true
        fi
    done

    echo -e "${GREEN}✅ Worktrees created at $WORKTREES_DIR${NC}"
    echo ""
    echo "Usage examples:"
    echo "  cd $WORKTREES_DIR/unit-tests && pytest tests/test_pms_canonical_models.py -v"
    echo "  cd $WORKTREES_DIR/adapter-tests && pytest tests/test_pms_providers.py -v"
    echo ""
}

clean_worktrees() {
    echo -e "${BLUE}🗑️  Cleaning up worktrees...${NC}"

    cd "$PROJECT_ROOT"

    if [ -d "$WORKTREES_DIR" ]; then
        # Remove all worktrees
        for worktree in $(git worktree list --porcelain | grep "^worktree" | awk '{print $2}'); do
            if [[ "$worktree" == "$WORKTREES_DIR"* ]]; then
                echo "Removing worktree: $worktree"
                git worktree remove "$worktree" 2>/dev/null || git worktree prune
            fi
        done

        rm -rf "$WORKTREES_DIR"
    fi

    echo -e "${GREEN}✅ Worktrees cleaned${NC}"
}

list_worktrees() {
    echo -e "${BLUE}📋 Active worktrees:${NC}"
    cd "$PROJECT_ROOT"
    git worktree list
}

# Main
case "${1:-help}" in
    create)
        create_worktrees
        ;;
    clean)
        clean_worktrees
        ;;
    list)
        list_worktrees
        ;;
    help|-h|--help)
        print_usage
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

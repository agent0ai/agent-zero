#!/bin/bash

################################################################################
# PMS Hub Feature Teams TDD Swarm Setup Script
# Sets up parallel git worktrees for two feature teams
# Usage: ./scripts/setup_feature_teams.sh [create|list|clean]
################################################################################

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_DIR="$REPO_DIR/.worktrees"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

create_feature_teams() {
    print_header "Creating Feature Teams Worktrees"

    cd "$REPO_DIR"

    # Ensure we're on main branch
    if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
        print_error "Not on main branch. Please switch to main first."
        exit 1
    fi

    # Pull latest changes
    print_info "Pulling latest changes from main..."
    git pull origin main 2>/dev/null || print_info "Could not pull from remote"

    # Create worktree directory if it doesn't exist
    mkdir -p "$WORKTREE_DIR"
    print_success "Worktree directory ready: $WORKTREE_DIR"

    # Team A: Calendar Hub Integration
    print_header "Team A: Calendar Hub Integration"

    TEAM_A_BRANCH="feature/pms-calendar-sync"
    TEAM_A_WORKTREE="$WORKTREE_DIR/pms-calendar"

    # Create feature branch
    if git rev-parse --verify "$TEAM_A_BRANCH" >/dev/null 2>&1; then
        print_info "Branch $TEAM_A_BRANCH already exists, checking it out..."
        git checkout "$TEAM_A_BRANCH"
    else
        print_info "Creating branch $TEAM_A_BRANCH..."
        git checkout -b "$TEAM_A_BRANCH"
        git push -u origin "$TEAM_A_BRANCH" 2>/dev/null || print_info "Could not push to remote"
    fi

    # Create worktree
    if [ -d "$TEAM_A_WORKTREE" ]; then
        print_info "Removing existing worktree: $TEAM_A_WORKTREE"
        git worktree remove "$TEAM_A_WORKTREE" --force 2>/dev/null || true
    fi

    print_info "Creating worktree: $TEAM_A_WORKTREE"
    git worktree add "$TEAM_A_WORKTREE" "$TEAM_A_BRANCH"
    print_success "Worktree created for Team A at $TEAM_A_WORKTREE"

    # Team B: Guest Communication Automation
    print_header "Team B: Guest Communication Automation"

    TEAM_B_BRANCH="feature/pms-messaging-automation"
    TEAM_B_WORKTREE="$WORKTREE_DIR/pms-messaging"

    # Switch back to main to create second branch
    git checkout main

    # Create feature branch
    if git rev-parse --verify "$TEAM_B_BRANCH" >/dev/null 2>&1; then
        print_info "Branch $TEAM_B_BRANCH already exists, checking it out..."
        git checkout "$TEAM_B_BRANCH"
    else
        print_info "Creating branch $TEAM_B_BRANCH..."
        git checkout -b "$TEAM_B_BRANCH"
        git push -u origin "$TEAM_B_BRANCH" 2>/dev/null || print_info "Could not push to remote"
    fi

    # Create worktree
    if [ -d "$TEAM_B_WORKTREE" ]; then
        print_info "Removing existing worktree: $TEAM_B_WORKTREE"
        git worktree remove "$TEAM_B_WORKTREE" --force 2>/dev/null || true
    fi

    print_info "Creating worktree: $TEAM_B_WORKTREE"
    git worktree add "$TEAM_B_WORKTREE" "$TEAM_B_BRANCH"
    print_success "Worktree created for Team B at $TEAM_B_WORKTREE"

    # Switch back to main
    git checkout main

    # Display next steps
    print_header "Setup Complete!"
    echo ""
    echo -e "${YELLOW}Team A: Calendar Hub Integration${NC}"
    echo -e "  Branch: $TEAM_A_BRANCH"
    echo -e "  Worktree: $TEAM_A_WORKTREE"
    echo -e "  Start: cd $TEAM_A_WORKTREE && pytest tests/test_pms_calendar_sync.py -v"
    echo ""
    echo -e "${YELLOW}Team B: Guest Communication Automation${NC}"
    echo -e "  Branch: $TEAM_B_BRANCH"
    echo -e "  Worktree: $TEAM_B_WORKTREE"
    echo -e "  Start: cd $TEAM_B_WORKTREE && pytest tests/test_pms_communication_workflows.py -v"
    echo ""
    echo -e "${BLUE}Documentation:${NC} TDD_SWARM_FEATURE_TEAMS.md"
    echo ""
}

list_worktrees() {
    print_header "Active Worktrees"
    cd "$REPO_DIR"
    git worktree list --porcelain
    echo ""
}

clean_worktrees() {
    print_header "Cleaning Up Worktrees"

    cd "$REPO_DIR"

    # List all worktrees
    worktrees=$(git worktree list --porcelain | grep -v "^$(git rev-parse --git-dir)$" | awk '{print $1}' || true)

    if [ -z "$worktrees" ]; then
        print_info "No worktrees to clean up"
        return
    fi

    # Remove each worktree
    while IFS= read -r worktree; do
        if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --git-dir)" ]; then
            print_info "Removing worktree: $worktree"
            git worktree remove "$worktree" --force 2>/dev/null || true
        fi
    done <<< "$worktrees"

    print_success "Worktree cleanup complete"
}

# Main script logic
case "${1:-create}" in
    create)
        create_feature_teams
        ;;
    list)
        list_worktrees
        ;;
    clean)
        clean_worktrees
        ;;
    *)
        echo "Usage: $0 {create|list|clean}"
        echo ""
        echo "Commands:"
        echo "  create - Create feature team worktrees (default)"
        echo "  list   - List all active worktrees"
        echo "  clean  - Remove all feature team worktrees"
        exit 1
        ;;
esac

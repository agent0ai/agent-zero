# Dev Container Build Fix - March 13, 2026

## Problem

The dev container failed to build with the error:

```
ERROR: failed to build: failed to solve: error from sender: open /mnt/wdblack/dev/projects/agent-zero/docker/run/agent-zero/tmp/codex-home/tmp/arg0: permission denied
```

## Root Cause

The `docker/run/` directory contained runtime artifacts (specifically root-owned files in `codex-home/`) that:

1. Prevented Docker from scanning the build context
2. Could not be deleted without elevated privileges on WSL2
3. Should never be committed to the repository

## Solutions Applied

### 1. Updated `.dockerignore` (Lines 1-3)

Moved `docker/run/` exclusion to the top for early processing:

```
docker/run/
docker/run/**
```

### 2. Fixed `DockerfileLocal` (Line 12)

Removed the problematic `COPY ./docker/run/fs/ /` command since:

- This directory never existed in the repository
- It was trying to copy from a non-existent location
- It triggered Docker's context scanning which hit permission errors

Changed from:

```dockerfile
COPY ./docker/run/fs/ /
```

To:

```dockerfile
# Copy filesystem files to root (if they exist)
# Skipping docker/run/fs as it's a runtime-only directory
```

### 3. Added to `.gitignore`

Added `docker/run/` to prevent accidental commits of runtime artifacts.

## How to Apply These Fixes Locally

### Option 1: Automated Cleanup (Recommended)

```bash
bash scripts/cleanup-docker-run.sh
```

This script will:

- Detect and remove the `docker/run/` directory safely
- Handle permission issues gracefully
- Provide helpful error messages if manual intervention is needed

### Option 2: Manual Cleanup

If the script doesn't work, use:

```bash
# For WSL2 users who can use sudo without password:
sudo rm -rf docker/run/

# Or create a placeholder to prevent recreation:
mkdir -p docker/run
touch docker/run/.gitkeep
```

### Option 3: Docker Container Solution

If manual deletion fails on WSL2:

```bash
# This will work if your Docker daemon has proper permissions
docker run --rm -v $(pwd):/workspace -w /workspace \
  alpine:latest rm -rf /workspace/docker/run

# Or use the dev container after other fixes
docker build --build-arg BRANCH=local -f DockerfileLocal .
```

## Verification

After applying fixes, verify with:

```bash
# docker/run should not exist
test -d docker/run && echo "FAILED: docker/run still exists" || echo "✓ docker/run successfully removed"

# Dockerfile should not reference docker/run/fs
grep "docker/run" Dockerfile* || echo "✓ No docker/run references in Dockerfile"
```

## Dev Container Build

After cleanup, the dev container should build successfully:

**VS Code:**

- **Remote-Containers: Reopen in Container** (Command Palette: `F1`)
- Or: Click "Reopen in Container" in the bottom-right corner

## Prevention

- `docker/run/` is now in `.gitignore` and `.dockerignore`
- No runtime artifacts will be accidentally committed
- The Dockerfile no longer references non-existent paths
- Future runs will not recreate this problematic directory

## Files Modified

- `.dockerignore` - Added docker/run/ at top for early exclusion
- `DockerfileLocal` - Removed non-existent COPY command
- `.gitignore` - Added docker/run/ exclusion
- `scripts/cleanup-docker-run.sh` - New cleanup helper script

## Notes

- This fix resolves the permission denied error on WSL2
- Docker/Buildx context scanning will no longer encounter the problematic files
- The changes are backward compatible and don't affect functionality

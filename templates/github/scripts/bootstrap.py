#!/usr/bin/env python3
"""
Agent Zero GitHub Bootstrap Script
==================================
Initializes a project with GitHub best practices templates.

Usage:
    python bootstrap.py [OPTIONS] [TARGET_DIR]

Options:
    --tier TIER     Template tier: minimal, standard, full (default: standard)
    --no-git        Skip git initialization
    --no-hooks      Skip pre-commit hook installation
    --dry-run       Show what would be done without making changes
    --force         Overwrite existing files
    -h, --help      Show this help message
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_BASE = Path(__file__).parent.parent / "tiers"
TIERS = ["minimal", "standard", "full"]

def log(msg, level="info"):
    colors = {"info": "\033[94m", "success": "\033[92m", "warning": "\033[93m", "error": "\033[91m", "reset": "\033[0m"}
    prefix = {"info": "i", "success": "✓", "warning": "!", "error": "✗"}
    print(f"{colors.get(level, '')}{prefix.get(level, '')} {msg}{colors['reset']}")

def copy_templates(tier, target, force=False, dry_run=False):
    tier_path = TEMPLATE_BASE / tier
    if not tier_path.exists():
        log(f"Template tier '{tier}' not found at {tier_path}", "error")
        return None
    
    files_copied = 0
    files_skipped = 0
    
    for src_file in tier_path.rglob("*"):
        if src_file.is_dir():
            continue
        rel_path = src_file.relative_to(tier_path)
        dest_file = target / rel_path
        
        if dest_file.exists() and not force:
            log(f"Skipping {rel_path} (exists, use --force to overwrite)", "warning")
            files_skipped += 1
            continue
        
        if dry_run:
            log(f"Would copy: {rel_path}", "info")
        else:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            log(f"Copied: {rel_path}", "success")
        files_copied += 1
    
    return files_copied, files_skipped

def init_git(target, dry_run=False):
    git_dir = target / ".git"
    if git_dir.exists():
        log("Git repository already initialized", "info")
        return True
    if dry_run:
        log("Would initialize git repository", "info")
        return True
    try:
        subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True)
        log("Initialized git repository", "success")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Failed to initialize git: {e}", "error")
        return False

def install_precommit(target, dry_run=False):
    precommit_config = target / ".pre-commit-config.yaml"
    if not precommit_config.exists():
        log("No .pre-commit-config.yaml found, skipping hook installation", "warning")
        return True
    if dry_run:
        log("Would install pre-commit hooks", "info")
        return True
    try:
        subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("pre-commit not installed. Install with: pip install pre-commit", "warning")
        return False
    try:
        subprocess.run(["pre-commit", "install"], cwd=target, check=True, capture_output=True)
        log("Installed pre-commit hooks", "success")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Failed to install pre-commit hooks: {e}", "error")
        return False

def main():
    parser = argparse.ArgumentParser(description="Bootstrap a project with Agent Zero GitHub templates")
    parser.add_argument("target", nargs="?", default=".", help="Target directory (default: current)")
    parser.add_argument("--tier", choices=TIERS, default="standard", help="Template tier")
    parser.add_argument("--no-git", action="store_true", help="Skip git initialization")
    parser.add_argument("--no-hooks", action="store_true", help="Skip pre-commit installation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    target = Path(args.target).resolve()
    
    print(f"\n🚀 Agent Zero GitHub Bootstrap")
    print(f"   Tier: {args.tier}")
    print(f"   Target: {target}")
    if args.dry_run:
        print(f"   Mode: DRY RUN\n")
    else:
        print()
    
    if not target.exists():
        log(f"Target directory does not exist: {target}", "error")
        sys.exit(1)
    
    log(f"Copying {args.tier} tier templates...", "info")
    result = copy_templates(args.tier, target, args.force, args.dry_run)
    if result:
        copied, skipped = result
        log(f"Copied {copied} files, skipped {skipped}", "success")
    
    if not args.no_git:
        init_git(target, args.dry_run)
    
    if not args.no_hooks:
        install_precommit(target, args.dry_run)
    
    print(f"\n✨ Bootstrap complete!")
    if not args.dry_run:
        print(f"\nNext steps:")
        print(f"  1. Review the generated files")
        print(f"  2. Customize configs as needed")
        print(f"  3. Run: git add . && git commit -m 'Initial setup'")

if __name__ == "__main__":
    main()

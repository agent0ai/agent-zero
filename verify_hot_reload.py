#!/usr/bin/env python3
"""
Hot-Reload Verification Script

Verifies that the hot-reload system is properly installed and functional.
"""

import sys
import os


def check_files():
    """Check that all required files exist"""
    print("Checking required files...")

    required_files = [
        "python/helpers/hot_reload.py",
        "python/helpers/module_cache.py",
        "python/helpers/hot_reload_integration.py",
        "python/api/hot_reload_status.py",
        "webui/js/hot_reload_panel.js",
        "docs/HOT_RELOAD.md",
    ]

    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            missing.append(file)

    if missing:
        print(f"\n❌ Missing {len(missing)} file(s)")
        return False

    print("\n✓ All required files present")
    return True


def check_dependencies():
    """Check that watchdog is installed"""
    print("\nChecking dependencies...")

    try:
        import watchdog
        try:
            version = watchdog.__version__
        except AttributeError:
            version = "installed"
        print(f"  ✓ watchdog {version}")
        return True
    except ImportError:
        print("  ✗ watchdog - NOT INSTALLED")
        print("\nInstall with: pip install watchdog")
        return False


def check_imports():
    """Check that modules can be imported"""
    print("\nChecking module imports...")

    modules = [
        "python.helpers.hot_reload",
        "python.helpers.module_cache",
        "python.helpers.hot_reload_integration",
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - {e}")
            failed.append(module)

    if failed:
        print(f"\n❌ Failed to import {len(failed)} module(s)")
        return False

    print("\n✓ All modules imported successfully")
    return True


def check_integration():
    """Check that hot-reload is integrated into initialize.py"""
    print("\nChecking integration...")

    with open("initialize.py", "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("initialize_hot_reload function", "def initialize_hot_reload()"),
        ("hot_reload_integration import", "from python.helpers.hot_reload_integration"),
    ]

    all_ok = True
    for name, search_str in checks:
        if search_str in content:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} - NOT FOUND")
            all_ok = False

    # Check run_ui.py
    with open("run_ui.py", "r", encoding="utf-8") as f:
        content = f.read()

    if "initialize.initialize_hot_reload()" in content:
        print(f"  ✓ Hot-reload initialization in run_ui.py")
    else:
        print(f"  ✗ Hot-reload initialization in run_ui.py - NOT FOUND")
        all_ok = False

    if all_ok:
        print("\n✓ Integration complete")
    else:
        print("\n❌ Integration incomplete")

    return all_ok


def check_api_endpoint():
    """Check that API endpoint is registered"""
    print("\nChecking API endpoint registration...")

    # The endpoint is auto-registered by run_ui.py
    # We can only verify the file exists
    if os.path.exists("python/api/hot_reload_status.py"):
        print("  ✓ API endpoint file exists")
        print("  ℹ Endpoint will be available at /hot_reload_status when server runs")
        return True
    else:
        print("  ✗ API endpoint file missing")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Hot-Reload System Verification")
    print("=" * 60)
    print()

    checks = [
        ("Files", check_files),
        ("Dependencies", check_dependencies),
        ("Imports", check_imports),
        ("Integration", check_integration),
        ("API Endpoint", check_api_endpoint),
    ]

    results = {}
    for name, check_func in checks:
        results[name] = check_func()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = all(results.values())

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")

    print()

    if all_passed:
        print("✅ All checks passed!")
        print("\nNext steps:")
        print("1. Install watchdog if not already: pip install -r requirements.txt")
        print("2. Start Agent Zero: python run_ui.py")
        print("3. Edit a tool file and save to test hot-reload")
        print("4. Check the DevTools panel in the web UI (bottom-right)")
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

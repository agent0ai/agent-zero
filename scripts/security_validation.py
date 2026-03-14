import sqlite3
from pathlib import Path


def validate_security():
    print("=== Agent Jumbo White-Hat Security Validation ===")

    db_path = Path("instruments/custom/workflow_engine/data/workflow.db")
    if not db_path.exists():
        print("[!] Database not found. Run the UI first to initialize.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check for registered passkeys
    cursor.execute("SELECT count(*) FROM user_passkeys")
    passkeys = cursor.fetchone()[0]
    print(f"[*] Registered Passkeys: {passkeys}")

    # 2. Check for synced profiles
    cursor.execute("SELECT count(*) FROM user_profiles")
    profiles = cursor.fetchone()[0]
    print(f"[*] Synced User Profiles: {profiles}")

    # 3. Analyze Security Audit Log
    print("\n--- Recent Security Events ---")
    cursor.execute(
        "SELECT event_type, status, timestamp, details FROM security_audit_log ORDER BY timestamp DESC LIMIT 10"
    )
    events = cursor.fetchall()

    if events:
        for e in events:
            print(f"[{e[2]}] {e[0].upper():<20} | Status: {e[1]:<10} | Details: {e[3]}")
    else:
        print("[ ] No security events recorded yet.")

    # 4. Check for Rate Limit hits
    cursor.execute("SELECT count(*) FROM security_audit_log WHERE event_type = 'rate_limit_exceeded'")
    rate_limits = cursor.fetchone()[0]
    if rate_limits > 0:
        print(f"\n[!] WARNING: {rate_limits} rate limit violations detected!")
    else:
        print("\n[V] No rate limit violations.")

    conn.close()
    print("\n=== Validation Complete ===")


if __name__ == "__main__":
    validate_security()

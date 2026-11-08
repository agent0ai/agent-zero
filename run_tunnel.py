"""Legacy image compatibility until startup retires its Supervisor entry."""
if __name__ == "__main__":
    import os
    # Keep old Supervisor retries from stopping WebUI before migration runs.
    os.execv("/bin/sleep", ["sleep", "infinity"])

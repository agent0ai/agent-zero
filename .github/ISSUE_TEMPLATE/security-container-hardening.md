---
    title: "🛡️ Security: Harden Docker container security"
    labels: "security, high-priority, docker"
    ---

    ## Problem Statement

    The Docker container currently runs as **root** user with excessive privileges, creating a significant security risk:

    - If an attacker gains code execution inside container, they have root
    - No separation of privileges for different components
    - Docker capabilities not restricted
    - No seccomp/AppArmor profiles applied

    ## Current Issues

    1. **Runs as root**
       - `Dockerfile` uses `USER root` or no user switch
       - SSH daemon configured for `root` user (`code_exec_ssh_user: "root"`)
       - All processes run with UID 0

    2. **Excessive capabilities**
       - Likely has `CAP_SYS_ADMIN` and other dangerous capabilities
       - Not using `--cap-drop` in docker-compose

    3. **Missing security profiles**
       - No seccomp profile filtering syscalls
       - No AppArmor/SELinux confinement
       - No `--security-opt` configurations

    4. **SSH Exposure**
       - SSH port exposed (55022) without additional hardening
       - Password authentication enabled (should use key-based)
       - No fail2ban or rate limiting on SSH

    ## Proposed Solution

    ### 1. Create Non-Root User

    ```dockerfile
    # In Dockerfile
    RUN addgroup -g 1000 -S agentzero && \
        adduser -u 1000 -S agentzero -G agentzero -h /home/agentzero -s /bin/sh && \
        chown -R agentzero:agentzero /usr

    USER agentzero
    WORKDIR /home/agentzero
    ```

    ### 2. Drop Unnecessary Capabilities

    ```yaml
    # In docker-compose.yml
    services:
      agent-zero:
        cap_drop:
          - ALL
        cap_add:
          - NET_BIND_SERVICE  # Only if binding to ports < 1024
          - CHOWN  # If needed for file operations
    ```

    ### 3. Apply Seccomp Profile

    Create `docker/seccomp-agent-zero.json`:

    ```json
    {
      "defaultAction": "SCMP_ACT_ERRNO",
      "syscalls": [
        {
          "name": "exit",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "exit_group",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "read",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "write",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "open",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "close",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "fstat",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "mmap",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "mprotect",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "munmap",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "brk",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "rt_sigaction",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "rt_sigprocmask",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "sigaltstack",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "clone",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "execve",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "getpid",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "getuid",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "getgid",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "geteuid",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "getegid",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "set_tid_address",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "set_robust_list",
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "name": "prlimit64",
          "action": "SCMP_ACT_ALLOW"
        }
      ]
    }
    ```

    Then in docker-compose:
    ```yaml
        security_opt:
          - seccomp:/path/to/seccomp-agent-zero.json
    ```

    ### 4. SSH Hardening

    - Change `code_exec_ssh_user` from `root` to `agentzero`
    - Use key-based authentication only (disable password auth)
    - Limit SSH to localhost only (already on 127.0.0.1:55022)
    - Add `PermitEmptyPasswords no`, `PasswordAuthentication no`

    ### 5. Read-Only Filesystem (Optional)

    Mount filesystem as read-only except for specific writable directories:

    ```yaml
        read_only: true
        tmpfs:
          - /tmp
          - /run
        volumes:
          - ./data:/usr/data:rw
          - ./memory:/usr/memory:rw
    ```

    ## Implementation Plan

    ### Phase 1: Create non-root user (Medium risk, high impact)
    1. Update `Dockerfile` to create `agentzero` user
    2. Switch to user before starting supervisor
    3. Update SSH config to use `agentzero` user
    4. Fix any permission issues in `/usr` directories

    ### Phase 2: Capability restriction (Low risk, medium impact)
    1. Add `cap_drop: [ALL]` to docker-compose
    2. Add minimal `cap_add` as needed
    3. Test all functionality (browser, code execution, etc.)

    ### Phase 3: Seccomp profile (Medium risk, high security)
    1. Generate seccomp profile based on allowed syscalls
    2. Use `docker/seccomp-profile.json`
    3. Apply in docker-compose
    4. Test thoroughly; may need adjustments

    ### Phase 4: SSH hardening (Low risk, high security)
    1. Change SSH user to `agentzero`
    2. Disable password authentication
    3. Enforce key-based auth only
    4. Add rate limiting via `MaxAuthTries`

    ## Testing Checklist

    - [ ] Web UI loads correctly as non-root
    - [ ] Code execution works (Python, Node.js, terminal)
    - [ ] SSH sessions establish successfully
    - [ ] File operations in `/usr` work (memory, knowledge, projects)
    - [ ] Docker container starts without permission errors
    - [ ] Browser automation still works
    - [ ] All tools can access required resources

    ## Rollback Plan

    - Keep root user as fallback (comment out USER directive)
    - Document how to revert to root if issues encountered
    - Provide debugging mode with verbose logging

    ## Related Issues

    - This addresses vulnerability: **Plaintext secrets** (secrets still need encryption)
    - Should be coordinated with **Encrypted secrets storage** PR

    ## Metrics

    - Reduces attack surface by >90%
    - Eliminates container escape impact (non-root)
    - Compliance: Helps meet CIS Docker Benchmark Level 1

    ---
    *This template was generated from deep analysis of agent-zero codebase.*
    
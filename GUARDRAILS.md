# AI Agent Guardrails

**⚠️ CRITICAL: ALL AI AGENTS MUST COMPLY WITH THESE RULES ⚠️**

This file defines safety restrictions that AI agents MUST follow when working in this workspace.
Agents should read and acknowledge these guardrails at the start of every session.

---

## 🚫 ABSOLUTE RESTRICTIONS (NEVER VIOLATE)

### 1. Prompt Compliance
- **Follow prompt instructions EXACTLY as written**
- Do NOT interpret, improvise, or "improve" upon explicit instructions
- Do NOT skip steps or take shortcuts unless explicitly permitted
- If instructions are unclear, **ASK for clarification** before proceeding
- If you cannot complete a task as specified, **STOP and explain why**

### 2. Forbidden Operations
**NEVER execute these operations under ANY circumstances:**

```
# Destructive commands
rm -rf /
rm -rf ~
rm -rf /*
dd if=/dev/zero of=/dev/sda

# Silent discard (hides errors/output)
command > /dev/null
command 2> /dev/null
command &> /dev/null

# System modification without explicit approval
chmod -R 777 /
chown -R user /

# Fork bombs or resource exhaustion
:(){ :|:& };:
```

### 3. Secret Protection
**NEVER read, display, echo, log, or expose:**

- `.env` files or any `*.env*` files
- Files containing: `secret`, `password`, `token`, `key`, `credential`, `auth`
- SSH keys: `~/.ssh/*`, `id_rsa`, `id_ed25519`, `*.pem`
- Cloud credentials: `~/.aws/*`, `~/.gcloud/*`, `~/.azure/*`
- API keys in any format
- Database connection strings with passwords
- Any file the user explicitly marks as secret

**If you accidentally see a secret:**
1. Do NOT repeat it in your response
2. Immediately inform the user
3. Recommend rotating the exposed credential

### 4. Command Autonomy
**All terminal commands MUST be non-interactive:**

- Use `-y`, `--yes`, `--non-interactive` flags
- Use `DEBIAN_FRONTEND=noninteractive` for apt
- Use `--no-input` for pip
- Use `-f` for commands that prompt for confirmation (only when safe)
- **NEVER** run commands that wait for user input
- If interaction is required, break into multiple steps with user confirmation

### 5. Protected Paths
**NEVER modify these locations:**

```
.github/prompts/*     # Prompt templates
.github/agents/*      # Agent definitions  
.github/instructions/*# Instruction files
GUARDRAILS.md         # This file
.copilotignore        # Ignore patterns
```

**For any config file modification:**
1. Show the proposed change first
2. Wait for explicit user approval
3. Create a backup before modifying

---

## ⚠️ CAUTION ZONES (REQUIRE EXPLICIT APPROVAL)

### Database Operations
- Schema modifications (CREATE, ALTER, DROP)
- Bulk data changes (UPDATE/DELETE without WHERE)
- Production database connections

### Git Operations
- Force push (`git push -f`, `git push --force`)
- Branch deletion (`git branch -D`)
- History rewriting (`git rebase`, `git filter-branch`)
- Pushing to main/master directly

### System Configuration
- Package installation (npm install, pip install, apt install)
- Environment variable changes
- Service restarts
- Port binding

### File Operations
- Deleting multiple files
- Moving/renaming critical files
- Changing file permissions
- Operations outside workspace directory

---

## ✅ SAFE OPERATIONS (NO APPROVAL NEEDED)

- Reading files in the workspace
- Creating new files in the workspace
- Running tests
- Building/compiling code
- Git status, diff, log (read-only)
- Linting and formatting
- Starting dev servers (on safe ports)

---

## 📋 SESSION PROTOCOL

### At Session Start
1. Check if GUARDRAILS.md exists
2. Read and acknowledge these rules
3. State: "Guardrails acknowledged. Operating within defined restrictions."

### Before Any Command
1. Check command against ABSOLUTE RESTRICTIONS
2. If in CAUTION ZONE, request explicit approval
3. Prefer SAFE OPERATIONS when possible

### When Uncertain
1. **STOP** - Do not proceed
2. **ASK** - Request clarification from user
3. **EXPLAIN** - State what you need to know and why

---

## 🔧 USER-DEFINED RULES

Add your project-specific restrictions below. Agents MUST respect these rules.

<!-- 
Example user rules:

### Project-Specific Restrictions
- Never modify the `src/core/` directory without approval
- Always run tests before committing
- Use TypeScript strict mode for all new files
- Require documentation for public functions
- No console.log in production code
- Database migrations require team review

### Deployment Rules  
- Never deploy to production directly
- Staging deployment requires all tests passing
- Hotfixes require incident ticket reference

### Code Standards
- Maximum function length: 50 lines
- Maximum file length: 300 lines
- Required test coverage: 80%
-->

### Custom Restrictions
<!-- Add your rules here -->



---

## 📝 Guardrails Version

- **Version:** 1.0.0
- **Last Updated:** 2025-12-04
- **Maintainer:** User (editable)

---

*These guardrails exist to protect your codebase, secrets, and system integrity.*
*AI agents should treat these rules as inviolable constraints, not suggestions.*

"""
Workflow Engine Database - SQLite storage for workflows, executions, and training progress
Manages workflow definitions, execution state, and skill tracking
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class WorkflowEngineDatabase:
    """Database operations for workflow engine"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Workflow definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                description TEXT,
                workflow_type TEXT DEFAULT 'custom',
                definition TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_template BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                metadata TEXT DEFAULT '{}',
                UNIQUE(name, version)
            )
        """)

        # Audit log for workflow changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER,
                action TEXT NOT NULL,
                changed_by TEXT,
                change_notes TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                previous_definition TEXT,
                new_definition TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
            )
        """)

        # Workflow executions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'pending',
                current_stage_id TEXT,
                current_task_id TEXT,
                started_at TEXT,
                completed_at TEXT,
                context TEXT DEFAULT '{}',
                result TEXT,
                error TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
            )
        """)

        # Stage progress tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stage_progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER NOT NULL,
                stage_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                entry_criteria_met TEXT DEFAULT '[]',
                exit_criteria_met TEXT DEFAULT '[]',
                deliverables_completed TEXT DEFAULT '[]',
                approval_status TEXT,
                approved_by TEXT,
                notes TEXT,
                FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id),
                UNIQUE(execution_id, stage_id)
            )
        """)

        # Task execution tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_executions (
                task_exec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER NOT NULL,
                stage_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                attempt_count INTEGER DEFAULT 0,
                input_data TEXT,
                output_data TEXT,
                error TEXT,
                assigned_to TEXT,
                FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id),
                UNIQUE(execution_id, stage_id, task_id)
            )
        """)

        # Skills and proficiency tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                proficiency_levels TEXT DEFAULT '[]',
                prerequisites TEXT DEFAULT '[]',
                related_tools TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Agent skill progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                current_level INTEGER DEFAULT 1,
                completions INTEGER DEFAULT 0,
                last_practiced TEXT,
                assessment_scores TEXT DEFAULT '[]',
                notes TEXT,
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
                UNIQUE(agent_id, skill_id)
            )
        """)

        # Training modules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_modules (
                module_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                skills_taught TEXT DEFAULT '[]',
                skill_level_target INTEGER DEFAULT 1,
                lessons TEXT DEFAULT '[]',
                module_assessment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Learning paths
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_paths (
                path_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_role TEXT,
                description TEXT,
                estimated_hours REAL,
                modules TEXT DEFAULT '[]',
                certification TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Agent learning progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                path_id TEXT NOT NULL,
                current_module_id TEXT,
                current_lesson_id TEXT,
                modules_completed TEXT DEFAULT '[]',
                overall_score REAL DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT,
                certified_at TEXT,
                FOREIGN KEY (path_id) REFERENCES learning_paths(path_id),
                UNIQUE(agent_id, path_id)
            )
        """)

        # Workflow events/audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                event_type TEXT NOT NULL,
                stage_id TEXT,
                task_id TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                data TEXT DEFAULT '{}',
                FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
            )
        """)

        # Passkeys for WebAuthn
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_passkeys (
                passkey_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                public_key BLOB NOT NULL,
                sign_count INTEGER DEFAULT 0,
                transports TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT
            )
        """)

        # User Profile linked to phone/passkeys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                full_name TEXT,
                email TEXT,
                phone_number TEXT,
                avatar_url TEXT,
                device_info TEXT, -- JSON string of device capabilities
                timezone TEXT,
                locale TEXT,
                last_synced TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Security Audit Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_log (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL, -- 'auth_attempt', 'profile_sync', 'passkey_reg', 'vault_access'
                status TEXT NOT NULL, -- 'success', 'failure', 'warning'
                user_id TEXT,
                ip_address TEXT,
                device_info TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ========== Workflow Definition Operations ==========

    def save_workflow(self, name: str, definition: dict, version: str = "1.0.0",
                     description: str = None, workflow_type: str = "custom",
                     is_template: bool = False, metadata: dict = None,
                     changed_by: str = "system", change_notes: str = None) -> int:
        """Save or update a workflow definition with audit logging"""
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Check for existing version
            cursor.execute("SELECT * FROM workflows WHERE name = ? AND version = ?", (name, version))
            existing = cursor.fetchone()

            if existing:
                existing_def = existing['definition']
                workflow_id = existing['workflow_id']
                
                # Update existing
                cursor.execute("""
                    UPDATE workflows SET
                        description = ?,
                        workflow_type = ?,
                        definition = ?,
                        is_template = ?,
                        metadata = ?,
                        updated_at = ?
                    WHERE workflow_id = ?
                """, (description, workflow_type, json.dumps(definition), 
                      is_template, json.dumps(metadata or {}), 
                      datetime.now().isoformat(), workflow_id))
                
                action = "update"
            else:
                # Deactivate other versions if this is a new version and we want it to be active
                # (Assuming new saves are intended to be the active one)
                cursor.execute("UPDATE workflows SET is_active = 0 WHERE name = ?", (name,))
                
                # Insert new version
                cursor.execute("""
                    INSERT INTO workflows (name, version, description, workflow_type,
                                           definition, is_template, is_active, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, version, description, workflow_type,
                      json.dumps(definition), is_template, 1,
                      json.dumps(metadata or {}), datetime.now().isoformat()))
                
                workflow_id = cursor.lastrowid
                existing_def = None
                action = "create"

            # Audit logging
            cursor.execute("""
                INSERT INTO workflow_audit_log (workflow_id, action, changed_by, 
                                               change_notes, previous_definition, new_definition)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workflow_id, action, changed_by, change_notes, 
                  existing_def, json.dumps(definition)))

            conn.commit()
            return workflow_id
        finally:
            conn.close()

    def get_workflow(self, workflow_id: int = None, name: str = None, version: str = None) -> Optional[dict]:
        """Get workflow by ID, or active version by name, or specific version by name"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if workflow_id:
            cursor.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
        elif name and version:
            cursor.execute("SELECT * FROM workflows WHERE name = ? AND version = ?", (name, version))
        elif name:
            cursor.execute("SELECT * FROM workflows WHERE name = ? AND is_active = 1", (name,))
        else:
            return None

        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['definition'] = json.loads(result['definition'])
            result['metadata'] = json.loads(result['metadata'])
            return result
        return None

    def get_workflow_history(self, name: str) -> list:
        """Get version history for a named workflow"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM workflows
            WHERE name = ?
            ORDER BY version DESC
        """, (name,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('definition'):
                r['definition'] = json.loads(r['definition'])
            results.append(r)
        return results

    def rollback_workflow(self, name: str, version: str, changed_by: str = "system") -> bool:
        """Set a specific version as the active one (deactivating others)"""
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # First deactivate all versions of this workflow
            cursor.execute("UPDATE workflows SET is_active = FALSE WHERE name = ?", (name,))
            
            # Then activate the target version
            cursor.execute("""
                UPDATE workflows SET is_active = TRUE 
                WHERE name = ? AND version = ?
            """, (name, version))
            
            if cursor.rowcount == 0:
                conn.rollback()
                return False

            # Add to audit log
            cursor.execute("""
                INSERT INTO workflow_audit_log (workflow_id, action, changed_by, change_notes)
                SELECT workflow_id, 'rollback', ?, ? FROM workflows 
                WHERE name = ? AND version = ?
            """, (changed_by, f"Rolled back to version {version}", name, version))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Rollback error: {e}")
            return False
        finally:
            conn.close()

    # ========== Execution Operations ==========

    def start_execution(self, workflow_id: int, name: str = None, context: dict = None) -> int:
        """Start a new workflow execution"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO workflow_executions (workflow_id, name, status, started_at, context)
            VALUES (?, ?, 'running', ?, ?)
        """, (workflow_id, name, datetime.now().isoformat(), json.dumps(context or {})))

        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self._log_event(execution_id, "execution_started", data={"context": context})
        return execution_id

    def get_execution(self, execution_id: int) -> Optional[dict]:
        """Get execution details"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM workflow_executions WHERE execution_id = ?", (execution_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['context'] = json.loads(result['context']) if result['context'] else {}
            return result
        return None

    def update_execution(self, execution_id: int, status: str = None,
                        current_stage_id: str = None, current_task_id: str = None,
                        context: dict = None, result: str = None, error: str = None):
        """Update execution state"""
        conn = self._get_conn()
        cursor = conn.cursor()

        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == 'completed':
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        if current_stage_id:
            updates.append("current_stage_id = ?")
            params.append(current_stage_id)
        if current_task_id:
            updates.append("current_task_id = ?")
            params.append(current_task_id)
        if context:
            updates.append("context = ?")
            params.append(json.dumps(context))
        if result:
            updates.append("result = ?")
            params.append(result)
        if error:
            updates.append("error = ?")
            params.append(error)

        if updates:
            params.append(execution_id)
            cursor.execute(f"UPDATE workflow_executions SET {', '.join(updates)} WHERE execution_id = ?", params)
            conn.commit()

        conn.close()

    def list_executions(self, workflow_id: int = None, status: str = None, limit: int = 50) -> list:
        """List workflow executions"""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT e.*, w.name as workflow_name
            FROM workflow_executions e
            JOIN workflows w ON e.workflow_id = w.workflow_id
            WHERE 1=1
        """
        params = []

        if workflow_id:
            query += " AND e.workflow_id = ?"
            params.append(workflow_id)
        if status:
            query += " AND e.status = ?"
            params.append(status)

        query += " ORDER BY e.started_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['context'] = json.loads(r['context']) if r['context'] else {}
            results.append(r)
        return results

    # ========== Stage Progress Operations ==========

    def update_stage_progress(self, execution_id: int, stage_id: str, status: str = None,
                             entry_criteria_met: list = None, exit_criteria_met: list = None,
                             deliverables_completed: list = None, approval_status: str = None,
                             approved_by: str = None, notes: str = None):
        """Update stage progress"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Insert or update
        cursor.execute("""
            INSERT INTO stage_progress (execution_id, stage_id)
            VALUES (?, ?)
            ON CONFLICT(execution_id, stage_id) DO NOTHING
        """, (execution_id, stage_id))

        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == 'in_progress' and not cursor.execute(
                "SELECT started_at FROM stage_progress WHERE execution_id = ? AND stage_id = ? AND started_at IS NOT NULL",
                (execution_id, stage_id)).fetchone():
                updates.append("started_at = ?")
                params.append(datetime.now().isoformat())
            if status in ('completed', 'skipped'):
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())

        if entry_criteria_met is not None:
            updates.append("entry_criteria_met = ?")
            params.append(json.dumps(entry_criteria_met))
        if exit_criteria_met is not None:
            updates.append("exit_criteria_met = ?")
            params.append(json.dumps(exit_criteria_met))
        if deliverables_completed is not None:
            updates.append("deliverables_completed = ?")
            params.append(json.dumps(deliverables_completed))
        if approval_status:
            updates.append("approval_status = ?")
            params.append(approval_status)
        if approved_by:
            updates.append("approved_by = ?")
            params.append(approved_by)
        if notes:
            updates.append("notes = ?")
            params.append(notes)

        if updates:
            params.extend([execution_id, stage_id])
            cursor.execute(f"UPDATE stage_progress SET {', '.join(updates)} WHERE execution_id = ? AND stage_id = ?", params)

        conn.commit()
        conn.close()

        self._log_event(execution_id, "stage_updated", stage_id=stage_id, data={"status": status})

    def get_stage_progress(self, execution_id: int, stage_id: str = None) -> list:
        """Get stage progress for execution"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if stage_id:
            cursor.execute("SELECT * FROM stage_progress WHERE execution_id = ? AND stage_id = ?",
                          (execution_id, stage_id))
        else:
            cursor.execute("SELECT * FROM stage_progress WHERE execution_id = ? ORDER BY progress_id",
                          (execution_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['entry_criteria_met'] = json.loads(r['entry_criteria_met'])
            r['exit_criteria_met'] = json.loads(r['exit_criteria_met'])
            r['deliverables_completed'] = json.loads(r['deliverables_completed'])
            results.append(r)
        return results if not stage_id else (results[0] if results else None)

    # ========== Task Execution Operations ==========

    def update_task_execution(self, execution_id: int, stage_id: str, task_id: str,
                             status: str = None, input_data: dict = None,
                             output_data: dict = None, error: str = None,
                             assigned_to: str = None):
        """Update task execution state"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Insert or update
        cursor.execute("""
            INSERT INTO task_executions (execution_id, stage_id, task_id)
            VALUES (?, ?, ?)
            ON CONFLICT(execution_id, stage_id, task_id) DO NOTHING
        """, (execution_id, stage_id, task_id))

        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == 'running':
                updates.append("started_at = ?")
                params.append(datetime.now().isoformat())
                updates.append("attempt_count = attempt_count + 1")
            if status in ('completed', 'failed', 'skipped'):
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())

        if input_data:
            updates.append("input_data = ?")
            params.append(json.dumps(input_data))
        if output_data:
            updates.append("output_data = ?")
            params.append(json.dumps(output_data))
        if error:
            updates.append("error = ?")
            params.append(error)
        if assigned_to:
            updates.append("assigned_to = ?")
            params.append(assigned_to)

        if updates:
            params.extend([execution_id, stage_id, task_id])
            cursor.execute(f"UPDATE task_executions SET {', '.join(updates)} WHERE execution_id = ? AND stage_id = ? AND task_id = ?", params)

        conn.commit()
        conn.close()

        self._log_event(execution_id, "task_updated", stage_id=stage_id, task_id=task_id, data={"status": status})

    def get_task_executions(self, execution_id: int, stage_id: str = None) -> list:
        """Get task executions"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if stage_id:
            cursor.execute("SELECT * FROM task_executions WHERE execution_id = ? AND stage_id = ?",
                          (execution_id, stage_id))
        else:
            cursor.execute("SELECT * FROM task_executions WHERE execution_id = ?", (execution_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['input_data'] = json.loads(r['input_data']) if r['input_data'] else None
            r['output_data'] = json.loads(r['output_data']) if r['output_data'] else None
            results.append(r)
        return results

    # ========== Skill Operations ==========

    def save_skill(self, skill_id: str, name: str, category: str, description: str = None,
                  proficiency_levels: list = None, prerequisites: list = None,
                  related_tools: list = None):
        """Save or update a skill"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO skills (skill_id, name, category, description,
                               proficiency_levels, prerequisites, related_tools)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(skill_id) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                description = excluded.description,
                proficiency_levels = excluded.proficiency_levels,
                prerequisites = excluded.prerequisites,
                related_tools = excluded.related_tools
        """, (skill_id, name, category, description,
              json.dumps(proficiency_levels or []),
              json.dumps(prerequisites or []),
              json.dumps(related_tools or [])))

        conn.commit()
        conn.close()

    def get_skill(self, skill_id: str) -> Optional[dict]:
        """Get skill details"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            r = dict(row)
            r['proficiency_levels'] = json.loads(r['proficiency_levels'])
            r['prerequisites'] = json.loads(r['prerequisites'])
            r['related_tools'] = json.loads(r['related_tools'])
            return r
        return None

    def list_skills(self, category: str = None) -> list:
        """List all skills"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if category:
            cursor.execute("SELECT * FROM skills WHERE category = ? ORDER BY name", (category,))
        else:
            cursor.execute("SELECT * FROM skills ORDER BY category, name")

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['proficiency_levels'] = json.loads(r['proficiency_levels'])
            r['prerequisites'] = json.loads(r['prerequisites'])
            r['related_tools'] = json.loads(r['related_tools'])
            results.append(r)
        return results

    def update_skill_progress(self, agent_id: str, skill_id: str, current_level: int = None,
                             completions: int = None, assessment_score: float = None):
        """Update agent's skill progress"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Insert or update
        cursor.execute("""
            INSERT INTO skill_progress (agent_id, skill_id)
            VALUES (?, ?)
            ON CONFLICT(agent_id, skill_id) DO NOTHING
        """, (agent_id, skill_id))

        updates = ["last_practiced = ?"]
        params = [datetime.now().isoformat()]

        if current_level is not None:
            updates.append("current_level = ?")
            params.append(current_level)
        if completions is not None:
            updates.append("completions = completions + ?")
            params.append(completions)
        if assessment_score is not None:
            # Append to scores array
            cursor.execute(
                "SELECT assessment_scores FROM skill_progress WHERE agent_id = ? AND skill_id = ?",
                (agent_id, skill_id))
            row = cursor.fetchone()
            scores = json.loads(row['assessment_scores']) if row else []
            scores.append({"score": assessment_score, "timestamp": datetime.now().isoformat()})
            updates.append("assessment_scores = ?")
            params.append(json.dumps(scores))

        params.extend([agent_id, skill_id])
        cursor.execute(f"UPDATE skill_progress SET {', '.join(updates)} WHERE agent_id = ? AND skill_id = ?", params)

        conn.commit()
        conn.close()

    def get_skill_progress(self, agent_id: str, skill_id: str = None) -> list:
        """Get agent's skill progress"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if skill_id:
            cursor.execute("""
                SELECT sp.*, s.name, s.category
                FROM skill_progress sp
                JOIN skills s ON sp.skill_id = s.skill_id
                WHERE sp.agent_id = ? AND sp.skill_id = ?
            """, (agent_id, skill_id))
        else:
            cursor.execute("""
                SELECT sp.*, s.name, s.category
                FROM skill_progress sp
                JOIN skills s ON sp.skill_id = s.skill_id
                WHERE sp.agent_id = ?
                ORDER BY s.category, s.name
            """, (agent_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['assessment_scores'] = json.loads(r['assessment_scores'])
            results.append(r)
        return results

    # ========== Learning Path Operations ==========

    def save_learning_path(self, path_id: str, name: str, target_role: str,
                          description: str = None, estimated_hours: float = None,
                          modules: list = None, certification: dict = None):
        """Save or update a learning path"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO learning_paths (path_id, name, target_role, description,
                                       estimated_hours, modules, certification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path_id) DO UPDATE SET
                name = excluded.name,
                target_role = excluded.target_role,
                description = excluded.description,
                estimated_hours = excluded.estimated_hours,
                modules = excluded.modules,
                certification = excluded.certification
        """, (path_id, name, target_role, description, estimated_hours,
              json.dumps(modules or []), json.dumps(certification)))

        conn.commit()
        conn.close()

    def get_learning_path(self, path_id: str) -> Optional[dict]:
        """Get learning path details"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learning_paths WHERE path_id = ?", (path_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            r = dict(row)
            r['modules'] = json.loads(r['modules'])
            r['certification'] = json.loads(r['certification']) if r['certification'] else None
            return r
        return None

    def list_learning_paths(self, target_role: str = None) -> list:
        """List learning paths"""
        conn = self._get_conn()
        cursor = conn.cursor()

        if target_role:
            cursor.execute("SELECT * FROM learning_paths WHERE target_role = ? ORDER BY name", (target_role,))
        else:
            cursor.execute("SELECT * FROM learning_paths ORDER BY target_role, name")

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['modules'] = json.loads(r['modules'])
            r['certification'] = json.loads(r['certification']) if r['certification'] else None
            results.append(r)
        return results

    # ========== Event Logging ==========

    def _log_event(self, execution_id: int, event_type: str, stage_id: str = None,
                  task_id: str = None, data: dict = None):
        """Log workflow event"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO workflow_events (execution_id, event_type, stage_id, task_id, data)
            VALUES (?, ?, ?, ?, ?)
        """, (execution_id, event_type, stage_id, task_id, json.dumps(data or {})))

        conn.commit()
        conn.close()

    def get_execution_events(self, execution_id: int, limit: int = 100) -> list:
        """Get execution event history"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM workflow_events
            WHERE execution_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (execution_id, limit))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['data'] = json.loads(r['data'])
            results.append(r)
        return results

    def get_events_by_type(self, event_type: str, limit: int = 100) -> list:
        """Get events of a specific type across all executions"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.*, we.name as execution_name 
            FROM workflow_events e
            LEFT JOIN workflow_executions we ON e.execution_id = we.execution_id
            WHERE e.event_type = ?
            ORDER BY e.timestamp DESC LIMIT ?
        """, (event_type, limit))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('data'):
                try:
                    r['data'] = json.loads(r['data'])
                except:
                    pass
            results.append(r)
        return results

    # ========== Statistics ==========

    def get_stats(self) -> dict:
        """Get workflow engine statistics"""
        conn = self._get_conn()
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) as count FROM workflows")
        stats['total_workflows'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM workflows WHERE is_template = TRUE")
        stats['workflow_templates'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM workflow_executions")
        stats['total_executions'] = cursor.fetchone()['count']

        cursor.execute("SELECT status, COUNT(*) as count FROM workflow_executions GROUP BY status")
        stats['executions_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) as count FROM skills")
        stats['total_skills'] = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM learning_paths")
        stats['total_learning_paths'] = cursor.fetchone()['count']

        conn.close()
        return stats

    def get_recent_executions(self, limit: int = 5) -> list:
        """Get recent workflow executions"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT we.*, w.name as workflow_name
            FROM workflow_executions we
            LEFT JOIN workflows w ON we.workflow_id = w.workflow_id
            ORDER BY we.started_at DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('context'):
                r['context'] = json.loads(r['context'])
            results.append(r)
        return results

    def get_top_skills(self, limit: int = 5) -> list:
        """Get top skills by level"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, sp.current_level, sp.completions
            FROM skills s
            LEFT JOIN skill_progress sp ON s.skill_id = sp.skill_id
            ORDER BY COALESCE(sp.current_level, 1) DESC, COALESCE(sp.completions, 0) DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('prerequisites'):
                r['prerequisites'] = json.loads(r['prerequisites'])
            if r.get('proficiency_levels'):
                r['proficiency_levels'] = json.loads(r['proficiency_levels'])
            if r.get('related_tools'):
                r['related_tools'] = json.loads(r['related_tools'])
            results.append(r)
        return results

    def get_learning_progress(self, path_id: str, agent_id: str = "agent_0") -> dict:
        """Get learning progress for a path and agent"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM learning_progress
            WHERE path_id = ? AND agent_id = ?
        """, (path_id, agent_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "path_id": path_id,
                "agent_id": agent_id,
                "modules_completed": [],
                "current_module": None,
                "overall_score": 0,
                "enrolled_at": None,
                "certified": False
            }

        result = dict(row)
        if result.get('modules_completed'):
            result['modules_completed'] = json.loads(result['modules_completed'])
        return result

    def get_training_module(self, module_id: str) -> Optional[dict]:
        """Get training module by ID"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM training_modules WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        result = dict(row)
        if result.get('skills_taught'):
            result['skills_taught'] = json.loads(result['skills_taught'])
        if result.get('lessons'):
            result['lessons'] = json.loads(result['lessons'])
        return result

    def get_agent_proficiency(self, agent_id: str = "agent_0") -> list:
        """Get all skill proficiencies for an agent"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, sp.current_level, sp.completions, sp.last_practiced
            FROM skills s
            LEFT JOIN skill_progress sp ON s.skill_id = sp.skill_id AND sp.agent_id = ?
            ORDER BY COALESCE(sp.current_level, 1) DESC, s.name ASC
        """, (agent_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('prerequisites'):
                r['prerequisites'] = json.loads(r['prerequisites'])
            if r.get('proficiency_levels'):
                r['proficiency_levels'] = json.loads(r['proficiency_levels'])
            if r.get('related_tools'):
                r['related_tools'] = json.loads(r['related_tools'])
            # Ensure defaults
            r['current_level'] = r.get('current_level') or 1
            r['completions'] = r.get('completions') or 0
            results.append(r)
        return results

    def list_workflows(self, workflow_type: str = None, templates_only: bool = False) -> list:
        """List all workflows from the database"""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM workflows"
        params = []
        conditions = []

        if workflow_type:
            conditions.append("workflow_type = ?")
            params.append(workflow_type)
        
        if templates_only:
            conditions.append("is_template = TRUE")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY name ASC, version DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            if r.get('definition'):
                r['definition'] = json.loads(r['definition'])
            results.append(r)
        return results

    def save_event(self, execution_id: int, event_type: str, stage_id: str = None,
                  task_id: str = None, data: dict = None):
        """Save a workflow event to the database"""
        self._log_event(execution_id, event_type, stage_id, task_id, data)

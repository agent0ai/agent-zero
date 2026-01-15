import unittest
import time
import os
import json
import sqlite3
from unittest.mock import MagicMock, patch
from python.helpers.security import SecurityManager
from python.helpers import files

class TestPerformanceSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure we have a clean test environment."""
        cls.db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
        # Ensure directory exists
        os.makedirs(os.path.dirname(cls.db_path), exist_ok=True)

    def test_async_logging_speed(self):
        """Validates that log_event returns nearly instantaneously (asynchronous)."""
        start_time = time.perf_counter()
        
        # Log 10 events rapidly
        for i in range(10):
            SecurityManager.log_event("perf_test", "success", details={"index": i})
            
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000 # convert to ms
        
        print(f"\n[PERF] 10 Async Logs took: {duration:.2f}ms")
        
        # 10 synchronous SQLite commits would take at least 50-200ms
        # Async should take < 5ms total for queuing
        self.assertLess(duration, 20.0, "Async logging is slower than expected (overhead should be negligible)")

    def test_database_persistence(self):
        """Verifies that async logs actually make it to the database."""
        test_id = f"test_{int(time.time())}"
        SecurityManager.log_event("persistence_check", "success", user_id=test_id)
        
        # Wait a brief moment for the background thread to flush
        time.sleep(0.5)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT event_type FROM security_audit_log WHERE user_id = ?", (test_id,))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row, "Log event was not persisted to the database")
        self.assertEqual(row[0], "persistence_check")

    def test_wal_mode_enabled(self):
        """Checks if the database is running in WAL mode for concurrency."""
        from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
        db = WorkflowEngineDatabase(self.db_path)
        conn = db._get_conn()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(mode.lower(), "wal", "Database should be in WAL mode for performance")

if __name__ == "__main__":
    unittest.main()

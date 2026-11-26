from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

from helpers import team_store


class TeamStoreTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "team" / "access.sqlite3"
        self.store = team_store.TeamStore(self.path)
        self.first = self.store.create_account("Alice", "first-pass-1234", actor_id="admin")

    def test_reset_and_disable_invalidate_existing_sessions(self):
        first = self.store.sign_in("ALICE", "first-pass-1234")
        second = self.store.sign_in("alice", "first-pass-1234")
        self.assertEqual(self.store.account_for_session(first), self.first)
        self.assertNotEqual(first, second)

        self.store.reset_password(self.first.id, "reset-pass-1234", actor_id="admin")
        self.assertIsNone(self.store.account_for_session(first))
        self.assertIsNone(self.store.account_for_session(second))
        self.assertIsNone(self.store.sign_in("alice", "first-pass-1234"))

        updated = self.store.sign_in("alice", "reset-pass-1234")
        self.assertIsNotNone(updated)
        self.store.set_account_enabled(self.first.id, False, actor_id="admin")
        self.assertIsNone(self.store.sign_in("alice", "reset-pass-1234"))
        self.store.set_account_enabled(self.first.id, True, actor_id="admin")
        self.assertIsNone(self.store.account_for_session(updated))

    def test_password_checked_before_reset_cannot_issue_session_afterward(self):
        checking = Event()
        resume = Event()
        verify = team_store.check_password_hash

        def wait_during_verification(password_hash, password):
            checking.set()
            if not resume.wait(timeout=5):
                raise RuntimeError("The password reset test did not release verification.")
            return verify(password_hash, password)

        with patch.object(team_store, "check_password_hash", side_effect=wait_during_verification):
            with ThreadPoolExecutor(max_workers=1) as executor:
                result = executor.submit(self.store.sign_in, "alice", "first-pass-1234")
                try:
                    self.assertTrue(checking.wait(timeout=5))
                    self.store.reset_password(self.first.id, "reset-pass-1234", actor_id="admin")
                finally:
                    resume.set()
                self.assertIsNone(result.result(timeout=5))

    def test_memberships_are_many_to_many_and_bound_to_project_identity(self):
        second = self.store.create_account("bob", "second-pass-1234", actor_id="admin")
        self.store.bind_project("project-1", "id-1")
        self.store.bind_project("project-2", "id-2")
        self.store.set_membership(self.first.id, "id-1", True, actor_id="admin")
        self.store.set_membership(self.first.id, "id-2", True, actor_id="admin")
        self.store.set_membership(second.id, "id-1", True, actor_id="admin")
        self.assertEqual(self.store.memberships(self.first.id), {"project-1": "id-1", "project-2": "id-2"})
        self.assertEqual(self.store.memberships(second.id), {"project-1": "id-1"})

        self.store.set_membership(second.id, "id-1", False, actor_id="admin")
        self.assertEqual(self.store.memberships(second.id), {})
        self.store.bind_project("project-1", "replacement")
        self.assertEqual(self.store.memberships(self.first.id), {"project-2": "id-2"})
        with self.assertRaises(ValueError):
            self.store.set_membership(second.id, "id-1", True, actor_id="admin")

    def test_session_and_password_persist_as_digests_and_audit_has_no_credentials(self):
        token = self.store.sign_in("alice", "first-pass-1234")
        with closing(sqlite3.connect(self.path)) as db:
            password_hash = db.execute("SELECT password_hash FROM accounts").fetchone()[0]
            token_hash = db.execute("SELECT token_hash FROM sessions").fetchone()[0]
            events = db.execute("SELECT action, actor_id, account_id FROM audit_events").fetchall()
        self.assertNotEqual(password_hash, "first-pass-1234")
        self.assertEqual(token_hash, team_store._session_hash(token))
        self.assertEqual(events, [("account.create", "admin", self.first.id)])
        self.assertEqual(team_store.TeamStore(self.path).account_for_session(token), self.first)
        self.store.revoke_session(token)
        self.assertIsNone(self.store.account_for_session(token))

    def test_normalized_username_is_unique(self):
        with self.assertRaises(ValueError):
            self.store.create_account(" alice ", "second-pass-1234", actor_id="admin")
        self.assertEqual(self.store.list_accounts(), [self.first])


if __name__ == "__main__":
    unittest.main()

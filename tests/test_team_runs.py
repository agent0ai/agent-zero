import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from helpers import team_access, team_runs
from helpers.team_store import ADMIN_ACTOR_ID, ActiveRunConflict, TeamStore


class TeamRunTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = TeamStore(Path(directory.name) / "team" / "access.sqlite3")
        self.a = self.store.create_account("alice", "first-pass-1234", actor_id="admin")
        self.b = self.store.create_account("bob", "second-pass-1234", actor_id="admin")
        self.store.bind_project("p1", "project-1")
        self.store.set_membership(self.a.id, "project-1", True, actor_id="admin")
        self.store.set_membership(self.b.id, "project-1", True, actor_id="admin")

    def reserve(self, account, chat="x", request="request-1", runtime="current", digest="text"):
        return self.store.reserve_run(context_id=chat, project_id="project-1", account_id=account.id,
                                      runtime_id=runtime, request_id=request, request_digest=digest)

    def test_shared_chat_has_one_atomic_holder_and_another_chat_can_run(self):
        ready = Barrier(2)

        def compete(account):
            ready.wait(timeout=5)
            try:
                return self.reserve(account)[0], True
            except ActiveRunConflict as error:
                return error.run, False

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(compete, self.a)
            b = pool.submit(compete, self.b)
            first, second = a.result(timeout=8), b.result(timeout=8)
        self.assertEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])
        y, created = self.reserve(self.b, chat="y")
        self.assertTrue(created)
        self.assertEqual(set(self.store.active_runs()), {"x", "y"})
        self.assertEqual(self.store.active_run("y"), y)

    def test_replay_returns_prior_result_and_late_completion_leaves_new_run(self):
        first, created = self.reserve(self.a)
        self.assertTrue(created)
        self.assertEqual(self.reserve(self.a), (first, False))
        with self.assertRaises(ValueError):
            self.reserve(self.a, digest="changed text")
        self.assertTrue(self.store.finish_run(first, "completed"))
        replay, created = self.reserve(self.a)
        self.assertFalse(created)
        self.assertEqual((replay.id, replay.state), (first.id, "completed"))
        later, created = self.reserve(self.b, request="request-2")
        self.assertTrue(created)
        self.assertFalse(self.store.finish_run(first, "failed"))
        self.assertEqual(later, self.store.active_run("x"))

    def test_platform_administrator_uses_the_same_chat_lock(self):
        admin = SimpleNamespace(id=ADMIN_ACTOR_ID)
        active, _ = self.reserve(admin)
        self.assertEqual(active.username, "Platform administrator")
        with self.assertRaises(ActiveRunConflict):
            self.reserve(self.a)
        self.assertEqual(self.store.add_queued_message(active, "one", "Continue"), 1)
        self.assertEqual(self.store.memberships(ADMIN_ACTOR_ID), {})
        self.assertNotIn(ADMIN_ACTOR_ID, {account.id for account in self.store.list_accounts()})
        with self.assertRaises(ValueError):
            self.store.set_account_enabled(ADMIN_ACTOR_ID, True, actor_id=ADMIN_ACTOR_ID)

    def test_compaction_reservation_rejects_messages_and_queueing(self):
        run, _ = self.store.reserve_run(
            context_id="x", project_id="project-1", account_id=self.a.id, runtime_id="current",
            request_id="compact", request_digest="compact", kind="compact",
        )
        with self.assertRaises(ActiveRunConflict):
            self.reserve(self.b)
        with self.assertRaises(ValueError):
            self.store.add_queued_message(run, "one", "Continue")

    def test_a_native_welcome_message_does_not_make_an_empty_project_chat_visible(self):
        context = SimpleNamespace(get_data=lambda _: None, log=SimpleNamespace(logs=[
            SimpleNamespace(type="response", heading="", content="Welcome", kvps={}),
        ]))
        self.assertFalse(team_access.has_chat_history(context))
        context.log.logs.append(SimpleNamespace(type="user", heading="", content="", kvps={
            "attachments": ["actual.txt"],
        }))
        self.assertTrue(team_access.has_chat_history(context))

    def test_recovery_retains_current_runs_and_revoked_account_cannot_reserve(self):
        old, _ = self.reserve(self.a, runtime="previous")
        current, _ = self.reserve(self.b, chat="y")
        self.assertEqual(self.store.recover_runs("current"), 1)
        self.assertEqual(self.store.active_runs(), {"y": current})
        replay, created = self.reserve(self.a)
        self.assertEqual((replay.id, replay.state, created), (old.id, "interrupted", False))
        self.store.set_membership(self.a.id, "project-1", False, actor_id="admin")
        with self.assertRaises(PermissionError):
            self.reserve(self.a, chat="z")

    def test_queue_replays_promotes_in_order_and_closes_after_last_item(self):
        run, _ = self.reserve(self.a)
        self.assertTrue(self.store.start_run(run))
        self.assertEqual(self.store.add_queued_message(run, "one", "First"), 1)
        self.assertEqual(self.store.add_queued_message(run, "one", "First"), 1)
        self.assertEqual(self.store.add_queued_message(run, "two", "Second"), 2)
        with self.assertRaises(ValueError):
            self.store.add_queued_message(run, "one", "Changed")
        self.assertIsNone(self.store.take_queued_message(run, interject=True))
        self.assertEqual(self.store.edit_queue(run, item_id=None, remove=False, first_only=True), (1, 2))
        self.assertEqual(self.store.take_queued_message(run, interject=True), ("one", "First"))
        self.assertEqual(self.store.take_queued_message(run, interject=False), ("two", "Second"))
        self.assertIsNone(self.store.take_queued_message(run, interject=False))
        with self.assertRaises(ValueError):
            self.store.add_queued_message(run, "three", "Too late")

    def test_stop_and_recovery_discard_pending_messages(self):
        run, _ = self.reserve(self.a)
        self.store.add_queued_message(run, "one", "Queued before the stop")
        self.assertTrue(self.store.request_stop(run, self.a.id))
        self.assertIsNone(self.store.take_queued_message(run, interject=False))
        self.store.finish_run(run, "stopped")
        later, _ = self.reserve(self.b, request="new", runtime="previous")
        self.store.add_queued_message(later, "two", "Queued before the restart")
        self.assertEqual(self.store.recover_runs("current"), 1)
        self.assertEqual(self.store.pending_queues(), {})

    def coordinator(self):
        patches = (
            patch.object(team_runs, "get_store", return_value=self.store),
            patch.object(team_runs, "mark_dirty_all"),
            patch.object(team_runs.persist_chat, "save_tmp_chat"),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        return SimpleNamespace(id="x", paused=False, log=Mock())

    async def test_stop_before_worker_start_never_dispatches_model(self):
        context = self.coordinator()
        run, _ = self.reserve(self.a)
        model = AsyncMock()
        with team_runs.authorized_dispatch(run):
            wrapped = team_runs.manage_turn(context, model)
        self.assertTrue(team_runs.request_stop(run, self.a.id))
        self.assertEqual(self.store.active_run("x").state, "stopping")
        self.assertIsNone(await wrapped())
        model.assert_not_called()
        self.assertIsNone(self.store.active_run("x"))
        self.assertEqual(self.reserve(self.a)[0].state, "stopped")

    async def test_stop_cannot_release_chat_before_cancelled_coroutine_exits(self):
        context = self.coordinator()
        run, _ = self.reserve(self.a)
        began = asyncio.Event()
        cleaning = asyncio.Event()
        cleanup_allowed = asyncio.Event()

        async def controlled_model():
            began.set()
            try:
                await asyncio.Future()
            finally:
                cleaning.set()
                await cleanup_allowed.wait()

        with team_runs.authorized_dispatch(run):
            wrapped = team_runs.manage_turn(context, controlled_model)
        worker = asyncio.create_task(wrapped())
        await asyncio.wait_for(began.wait(), timeout=5)
        self.assertTrue(team_runs.request_stop(run, self.a.id))
        try:
            await asyncio.wait_for(cleaning.wait(), timeout=5)
            self.assertEqual(self.store.active_run("x").state, "stopping")
            with self.assertRaises(ActiveRunConflict):
                self.reserve(self.b)
        finally:
            cleanup_allowed.set()
        with self.assertRaises(asyncio.CancelledError):
            await worker
        self.assertIsNone(self.store.active_run("x"))
        self.assertTrue(self.reserve(self.b)[1])


if __name__ == "__main__":
    unittest.main()

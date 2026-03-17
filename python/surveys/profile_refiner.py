from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from typing import Any

from agent import Agent
from python.helpers.defer import DeferredTask

from .db import SurveyDB
from .schemas import UserProfile


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            dst[k] = _deep_merge(dst[k], v)  # type: ignore[arg-type]
        else:
            dst[k] = v
    return dst


class ProfileRefinerService:
    """Background worker that turns survey answers into structured profile updates."""

    DATA_KEY = "_survey_profile_refiner"

    def __init__(self, agent: Agent):
        self.agent = agent
        self.task: DeferredTask | None = None

    def start(self) -> None:
        if self.task and self.task.is_alive():
            return
        self.task = DeferredTask(thread_name=f"ProfileRefiner-{self.agent.context.id}")
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task, terminate_thread=True)
        self.task.start_task(self._run_loop)

    def stop(self) -> None:
        if self.task:
            self.task.kill(terminate_thread=True)
            self.task = None

    async def _run_loop(self) -> None:
        db = SurveyDB.for_agent(self.agent)
        try:
            while True:
                await asyncio.sleep(10)

                # Do not interfere with active survey filling.
                if self.agent.get_data("_survey_active"):
                    continue

                events = db.fetch_unprocessed_answer_events(limit=200)
                if not events:
                    continue

                # Group by profile_id (fallback to "default").
                grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for e in events:
                    pid = e.get("profile_id") or "default"
                    grouped[pid].append(e)

                processed_ids: list[str] = []
                for profile_id, evs in grouped.items():
                    profile = db.get_profile(profile_id) or UserProfile(
                        id=profile_id, persona_id=None, data={}
                    )

                    # Prepare a compact evidence block.
                    lines = []
                    for e in evs[:60]:
                        q = (e.get("question_text") or "").strip()
                        a = (e.get("answer_text") or "").strip()
                        if not q:
                            q = e.get("selector") or e.get("field_kind") or "question"
                        if q and a:
                            lines.append(f"- Q: {q}\n  A: {a}")

                    system = (
                        "You refine a user profile from survey answers.\n"
                        "Output ONLY valid JSON.\n"
                        "Return an object with keys:\n"
                        "- profile_patch: object (deep-merge patch)\n"
                        "- extracted_facts: array of short strings\n"
                        "Rules:\n"
                        "- Prefer stable fields: demographics, contact, preferences, traits.\n"
                        "- If unsure, add to notes instead of guessing.\n"
                    )
                    message = (
                        f"current_profile_json: {json.dumps(profile.data or {}, ensure_ascii=False)}\n\n"
                        f"survey_answers:\n{chr(10).join(lines)}\n"
                    )

                    try:
                        out = await self.agent.call_utility_model(
                            system=system, message=message, background=True
                        )
                        data = json.loads(out)
                        patch = data.get("profile_patch") if isinstance(data, dict) else None
                        if isinstance(patch, dict):
                            profile.data = _deep_merge(profile.data or {}, patch)
                            db.upsert_profile(profile)
                        processed_ids.extend([e["id"] for e in evs])
                    except Exception:
                        # If parsing fails, do not mark processed.
                        continue

                if processed_ids:
                    db.mark_answers_processed(processed_ids)
        finally:
            db.close()


def ensure_profile_refiner_running(agent: Agent) -> ProfileRefinerService:
    svc = agent.get_data(ProfileRefinerService.DATA_KEY)
    if isinstance(svc, ProfileRefinerService):
        svc.start()
        return svc
    svc = ProfileRefinerService(agent)
    agent.set_data(ProfileRefinerService.DATA_KEY, svc)
    svc.start()
    return svc


import json

from python.helpers.tool import Tool, Response
from python.surveys.db import SurveyDB
from python.surveys.schemas import UserProfile
from python.surveys.profile_refiner import _deep_merge


class ProfileUpdate(Tool):
    async def execute(
        self,
        profile_id: str = "default",
        patch_json: str = "",
        persona_id: str = "",
        **kwargs,
    ):
        """
        Update (deep-merge) the structured survey profile stored in SQLite.

        - profile_id: profile key (default "default")
        - patch_json: JSON object to deep-merge into profile.data
        - persona_id: optional persona association
        """
        if not patch_json:
            return Response(
                message="patch_json is required and must be a JSON object.",
                break_loop=False,
            )

        try:
            patch = json.loads(patch_json)
        except Exception as e:
            return Response(message=f"Invalid patch_json: {e}", break_loop=False)

        if not isinstance(patch, dict):
            return Response(message="patch_json must be a JSON object.", break_loop=False)

        db = SurveyDB.for_agent(self.agent)
        try:
            profile = db.get_profile(profile_id) or UserProfile(
                id=profile_id, persona_id=(persona_id or None), data={}
            )
            if persona_id:
                profile.persona_id = persona_id
            profile.data = _deep_merge(profile.data or {}, patch)
            db.upsert_profile(profile)
            return Response(
                message=json.dumps(
                    {"profile_id": profile.id, "updated_keys": sorted(patch.keys())},
                    ensure_ascii=False,
                    indent=2,
                ),
                break_loop=False,
            )
        finally:
            db.close()


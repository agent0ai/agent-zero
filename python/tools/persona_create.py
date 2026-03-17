import json
import uuid

from python.helpers.tool import Tool, Response
from python.surveys.db import SurveyDB
from python.surveys.schemas import Persona


class PersonaCreate(Tool):
    async def execute(
        self,
        name: str = "",
        description: str = "",
        constraints_json: str = "",
        generate: bool = False,
        seed: str = "",
        **kwargs,
    ):
        """
        Create (and store) a persona used for survey answering.

        If generate=true, the utility model will draft name/description/constraints using 'seed'.
        """
        db = SurveyDB.for_agent(self.agent)
        try:
            constraints = {}
            if constraints_json:
                constraints = json.loads(constraints_json)

            if generate:
                system = (
                    "You design a survey-answering persona for testing.\n"
                    "Output ONLY valid JSON with keys: name, description, constraints.\n"
                    "Constraints must be a JSON object with stable fields (demographics, preferences, traits).\n"
                )
                msg = f"seed: {seed}\nexisting_name: {name}\nexisting_description: {description}\n"
                out = await self.agent.call_utility_model(system=system, message=msg, background=False)
                data = json.loads(out)
                if isinstance(data, dict):
                    name = str(data.get("name") or name or "Persona")
                    description = str(data.get("description") or description or "")
                    if isinstance(data.get("constraints"), dict):
                        constraints = data["constraints"]

            if not name:
                name = "Persona"

            persona = Persona(
                id=str(uuid.uuid4()),
                name=name,
                description=description or "",
                constraints=constraints or {},
            )
            db.upsert_persona(persona)
            return Response(
                message=json.dumps(
                    {"persona_id": persona.id, "name": persona.name},
                    ensure_ascii=False,
                    indent=2,
                ),
                break_loop=False,
            )
        finally:
            db.close()


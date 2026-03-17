import asyncio
import os
from pathlib import Path

from agent import AgentContext
from initialize import initialize
from python.tools.survey_fill import SurveyFill


async def main():
    config = initialize()
    ctx = AgentContext(config)

    demo_path = Path(__file__).parent / "docs" / "res" / "survey_demo.html"
    url = demo_path.resolve().as_uri()  # file://...

    tool = SurveyFill(agent=ctx.agent0, name="survey_fill", args={}, message="")
    res = await tool.execute(url=url, profile_id="default", max_pages=3, use_llm=False)
    print(res.message)


if __name__ == "__main__":
    asyncio.run(main())


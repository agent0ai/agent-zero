import cProfile
import io
import pstats
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent, AgentContext
from helpers.extension import extensible
from initialize import initialize_agent


class PerfAgent(Agent):
    @extensible
    def perf_hook(self, value: int):
        return value + 1


@pytest.mark.parametrize("iterations", [10000])
def test_extensible_method_performance_trace(iterations: int):
    agent = PerfAgent(number=0, config=initialize_agent())
    context = agent.context

    try:
        profiler = cProfile.Profile()
        profiler.enable()

        result = 0
        for i in range(iterations):
            result = agent.perf_hook(i)

        profiler.disable()

        output = io.StringIO()
        stats = pstats.Stats(profiler, stream=output)
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        print(f"\n[extensible perf] iterations={iterations} result={result}")
        print(output.getvalue())

        assert result == iterations
    finally:
        if context:
            AgentContext.remove(context.id)

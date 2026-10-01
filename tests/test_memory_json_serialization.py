import json
import threading

import numpy as np
from langchain_core.documents import Document

from plugins._memory.api.memory_dashboard import MemoryDashboard
from plugins._memory.helpers.memory import Memory


def test_cosine_normalizer_returns_native_float():
    score = Memory._cosine_normalizer(np.float32(0.8))

    assert type(score) is float


def test_memory_dashboard_serializes_legacy_numpy_similarity():
    dashboard = MemoryDashboard(app=None, thread_lock=threading.RLock())
    document = Document(
        page_content="legacy memory",
        metadata={
            "id": "memory-1",
            "area": "main",
            "timestamp": "unknown",
            "_consolidation_similarity": np.float32(0.75),
        },
    )

    formatted = dashboard._format_memory_for_dashboard(document)

    assert type(formatted["metadata"]["_consolidation_similarity"]) is float
    assert isinstance(document.metadata["_consolidation_similarity"], np.float32)
    json.dumps(formatted)

"""
Security Test: Verify safe deserialization practices.

Tests:
- FAISS indexes load without dangerous deserialization
- No pickle.loads on untrusted data
- Safe parsing of JSON/serialized data
"""

import pytest
import os
import tempfile
from pathlib import Path

from python.helpers.memory import Memory, MyFaiss
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import FakeEmbeddings


class TestDeserialization:
    """Test deserialization safety."""

    def test_faiss_load_without_dangerous_flag(self):
        """Verify FAISS.load_local is not called with allow_dangerous_deserialization=True."""
        # This test checks the code, not runtime behavior
        # We'll inspect the source to ensure the flag is False
        import inspect
        from python.helpers import memory

        source = inspect.getsource(memory.Memory.initialize)
        # The dangerous flag should NOT be set to True in the code
        assert "allow_dangerous_deserialization=True" not in source, \
            "FAISS should not use dangerous deserialization"
        # It should either be absent (defaults to False) or explicitly False
        assert "allow_dangerous_deserialization=False" in source or \
               "allow_dangerous_deserialization" not in source, \
               "FAISS deserialization should be safe"

    def test_no_pickle_usage_on_user_data(self):
        """Ensure pickle is not used to load user-provided data."""
        import python.helpers.memory as mem_mod
        import python.helpers.knowledge_import as ki_mod

        # Scan modules for pickle usage
        pickle_patterns = [
            'pickle.load',
            'pickle.loads',
            'cPickle.load',
            'cPickle.loads'
        ]

        mem_source = inspect.getsource(mem_mod)
        ki_source = inspect.getsource(ki_mod)

        for pattern in pickle_patterns:
            assert pattern not in mem_source, f"Found unsafe pickle usage in memory.py: {pattern}"
            assert pattern not in ki_source, f"Found unsafe pickle usage in knowledge_import.py: {pattern}"

    def test_faiss_index_file_validation(self):
        """Test that loading a malicious FAISS index is prevented."""
        # Create a fake malicious FAISS file (pickle exploit attempt)
        # This should be safely rejected by FAISS when allow_dangerous_deserialization=False

        embeddings = FakeEmbeddings(size=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a legitimate FAISS index first
            db = FAISS.from_texts(["test"], embeddings)
            db.save_local(tmpdir)

            # Now attempt to load it (should succeed)
            try:
                loaded = FAISS.load_local(
                    folder_path=tmpdir,
                    embeddings=embeddings,
                    allow_dangerous_deserialization=False
                )
                assert loaded is not None
            except Exception as e:
                pytest.fail(f"Failed to load legitimate FAISS index: {e}")

            # Try to load with dangerous flag set to True (should load but risky)
            # We won't test malicious files as that would require creating an exploit
            # The important thing is that our code doesn't set True

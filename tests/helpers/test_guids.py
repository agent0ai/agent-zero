"""Tests for python/helpers/guids.py — generate_id."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import guids


class TestGenerateId:
    def test_default_length(self):
        id_ = guids.generate_id()
        assert len(id_) == 8
        assert id_.isalnum()

    def test_custom_length(self):
        id_ = guids.generate_id(12)
        assert len(id_) == 12
        assert id_.isalnum()

    def test_alphanumeric_only(self):
        for _ in range(20):
            id_ = guids.generate_id(10)
            assert all(c.isalnum() for c in id_)

    def test_different_ids_each_call(self):
        ids = {guids.generate_id() for _ in range(50)}
        assert len(ids) == 50

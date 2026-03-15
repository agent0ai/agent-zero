"""Tests for python/helpers/login.py — get_credentials_hash, is_login_required."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import login
from python.helpers import dotenv


class TestGetCredentialsHash:
    def test_returns_none_when_no_user(self):
        with patch.object(dotenv, "get_dotenv_value") as m:
            m.side_effect = lambda k, d=None: None if k == dotenv.KEY_AUTH_LOGIN else "pass"
            assert login.get_credentials_hash() is None

    def test_returns_hash_when_user_and_password(self):
        with patch.object(dotenv, "get_dotenv_value") as m:
            m.side_effect = lambda k, d=None: "user" if k == dotenv.KEY_AUTH_LOGIN else "secret"
            h = login.get_credentials_hash()
            assert h is not None
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    def test_same_credentials_same_hash(self):
        with patch.object(dotenv, "get_dotenv_value") as m:
            m.side_effect = lambda k, d=None: "alice" if k == dotenv.KEY_AUTH_LOGIN else "pwd123"
            h1 = login.get_credentials_hash()
            h2 = login.get_credentials_hash()
            assert h1 == h2

    def test_different_credentials_different_hash(self):
        with patch.object(dotenv, "get_dotenv_value") as m1:
            m1.side_effect = lambda k, d=None: "alice" if k == dotenv.KEY_AUTH_LOGIN else "pwd1"
            h1 = login.get_credentials_hash()
        with patch.object(dotenv, "get_dotenv_value") as m2:
            m2.side_effect = lambda k, d=None: "alice" if k == dotenv.KEY_AUTH_LOGIN else "pwd2"
            h2 = login.get_credentials_hash()
        assert h1 != h2


class TestIsLoginRequired:
    def test_false_when_no_user(self):
        with patch.object(dotenv, "get_dotenv_value", return_value=None):
            assert login.is_login_required() is False

    def test_true_when_user_set(self):
        with patch.object(dotenv, "get_dotenv_value") as m:
            m.side_effect = lambda k, d=None: "admin" if k == dotenv.KEY_AUTH_LOGIN else ""
            assert login.is_login_required() is True

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._whatsapp_integration.helpers.number_utils import (
    normalize_allowed_numbers,
    normalize_number,
)


def test_normalize_number_handles_jids_and_phone_formatting():
    assert normalize_number("+1 (415) 555-1234") == "14155551234"
    assert normalize_number("00420 777 123 456") == "420777123456"
    assert normalize_number("14155551234@s.whatsapp.net") == "14155551234"
    assert normalize_number("14155551234:17@s.whatsapp.net") == "14155551234"


def test_normalize_allowed_numbers_accepts_lists_and_csv_strings():
    assert normalize_allowed_numbers([
        "+1 (415) 555-1234",
        "00420 777 123 456",
        "",
    ]) == {"14155551234", "420777123456"}

    assert normalize_allowed_numbers(
        "+1 (415) 555-1234, 00420 777 123 456"
    ) == {"14155551234", "420777123456"}


def test_normalize_allowed_numbers_ignores_unsupported_values():
    assert normalize_allowed_numbers(None) == set()
    assert normalize_allowed_numbers(12345) == set()

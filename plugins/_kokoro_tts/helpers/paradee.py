"""Compatibility alias for the guest-only Paradee engine."""
import sys
from plugins._kokoro_tts.sandbox import paradee
sys.modules[__name__] = paradee

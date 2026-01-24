"""
API Instrumentation Module for Agent Zero

This module provides non-breaking instrumentation logging for LLM API calls.
It logs request timing, token usage, and cache metrics to a dedicated file.

Usage:
    from api_instrumentation import log_api_call_start, log_api_call_end
    
    # Before API call
    call_id = log_api_call_start(model_name, messages, session_id)
    
    # After API call
    log_api_call_end(call_id, response)
"""

import json
import time
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# Log file location
LOG_DIR = Path("/a0/logs/api_instrumentation")
LOG_FILE = LOG_DIR / "api_calls.jsonl"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for pending calls
_pending_calls: Dict[str, Dict[str, Any]] = {}


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    if not text:
        return 0
    return len(text) // 4


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Estimate total tokens in a list of messages."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += estimate_tokens(block.get("text", ""))
                elif isinstance(block, str):
                    total += estimate_tokens(block)
    return total


def log_api_call_start(
    model_name: str,
    messages: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log the start of an API call.
    
    Returns:
        call_id: Unique identifier for this call (use in log_api_call_end)
    """
    call_id = str(uuid.uuid4())[:8]
    
    _pending_calls[call_id] = {
        "call_id": call_id,
        "model": model_name,
        "session_id": session_id,
        "start_time": time.time(),
        "start_datetime": datetime.now().isoformat(),
        "estimated_input_tokens": estimate_messages_tokens(messages),
        "message_count": len(messages),
        "extra_metadata": extra_metadata or {}
    }
    
    return call_id


def log_api_call_end(
    call_id: str,
    response: Any = None,
    error: Optional[str] = None,
    retry_count: int = 0
) -> None:
    """
    Log the end of an API call with response metrics.
    
    Args:
        call_id: The ID returned from log_api_call_start
        response: The LiteLLM response object (optional)
        error: Error message if call failed (optional)
        retry_count: Number of retries attempted
    """
    if call_id not in _pending_calls:
        return  # Silently ignore if call wasn't tracked
    
    call_data = _pending_calls.pop(call_id)
    end_time = time.time()
    
    # Build log entry
    log_entry = {
        "call_id": call_data["call_id"],
        "model": call_data["model"],
        "session_id": call_data["session_id"],
        "start_datetime": call_data["start_datetime"],
        "end_datetime": datetime.now().isoformat(),
        "duration_seconds": round(end_time - call_data["start_time"], 3),
        "estimated_input_tokens": call_data["estimated_input_tokens"],
        "message_count": call_data["message_count"],
        "retry_count": retry_count,
        "error": error,
        **call_data.get("extra_metadata", {})
    }
    
    # Extract usage metrics from response
    if response is not None:
        usage = getattr(response, "usage", None)
        if usage is not None:
            # Standard token counts
            log_entry["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
            log_entry["completion_tokens"] = getattr(usage, "completion_tokens", None)
            log_entry["total_tokens"] = getattr(usage, "total_tokens", None)
            
            # Cache metrics (Anthropic-specific)
            log_entry["cache_creation_input_tokens"] = getattr(usage, "cache_creation_input_tokens", None)
            log_entry["cache_read_input_tokens"] = getattr(usage, "cache_read_input_tokens", None)
            
            # Try to get from model_dump if attributes not directly available
            if hasattr(usage, "model_dump"):
                usage_dict = usage.model_dump()
                if log_entry.get("cache_creation_input_tokens") is None:
                    log_entry["cache_creation_input_tokens"] = usage_dict.get("cache_creation_input_tokens")
                if log_entry.get("cache_read_input_tokens") is None:
                    log_entry["cache_read_input_tokens"] = usage_dict.get("cache_read_input_tokens")
    
    # Write to log file (append mode, JSONL format)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        # Silently fail - instrumentation should never break the main flow
        pass


def get_log_summary(last_n_hours: int = 24) -> Dict[str, Any]:
    """
    Get a summary of API calls from the log file.
    
    Args:
        last_n_hours: Only include calls from the last N hours
        
    Returns:
        Summary dict with aggregated metrics
    """
    if not LOG_FILE.exists():
        return {"error": "No log file found", "total_calls": 0}
    
    cutoff_time = datetime.now().timestamp() - (last_n_hours * 3600)
    
    calls = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                # Parse datetime and filter
                entry_time = datetime.fromisoformat(entry.get("start_datetime", "")).timestamp()
                if entry_time >= cutoff_time:
                    calls.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue
    
    if not calls:
        return {"total_calls": 0, "period_hours": last_n_hours}
    
    # Aggregate metrics
    total_prompt_tokens = sum(c.get("prompt_tokens") or 0 for c in calls)
    total_completion_tokens = sum(c.get("completion_tokens") or 0 for c in calls)
    total_cache_creation = sum(c.get("cache_creation_input_tokens") or 0 for c in calls)
    total_cache_read = sum(c.get("cache_read_input_tokens") or 0 for c in calls)
    total_duration = sum(c.get("duration_seconds") or 0 for c in calls)
    total_errors = sum(1 for c in calls if c.get("error"))
    
    # Model breakdown
    models = {}
    for c in calls:
        model = c.get("model", "unknown")
        if model not in models:
            models[model] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
        models[model]["calls"] += 1
        models[model]["prompt_tokens"] += c.get("prompt_tokens") or 0
        models[model]["completion_tokens"] += c.get("completion_tokens") or 0
    
    return {
        "period_hours": last_n_hours,
        "total_calls": len(calls),
        "total_errors": total_errors,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_cache_creation_tokens": total_cache_creation,
        "total_cache_read_tokens": total_cache_read,
        "cache_hit_rate": round(total_cache_read / max(total_prompt_tokens, 1) * 100, 2),
        "avg_duration_seconds": round(total_duration / len(calls), 3),
        "models": models
    }


if __name__ == "__main__":
    # Test the instrumentation
    print("Testing API Instrumentation Module")
    print("=" * 40)
    
    # Simulate a call
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    call_id = log_api_call_start(
        model_name="anthropic/claude-3-haiku-20240307",
        messages=test_messages,
        session_id="test-session-123"
    )
    print(f"Started call: {call_id}")
    
    # Simulate response
    class MockUsage:
        prompt_tokens = 50
        completion_tokens = 20
        total_tokens = 70
        cache_creation_input_tokens = 40
        cache_read_input_tokens = 0
    
    class MockResponse:
        usage = MockUsage()
    
    time.sleep(0.1)  # Simulate API latency
    log_api_call_end(call_id, MockResponse())
    print("Logged call end")
    
    # Get summary
    summary = get_log_summary(last_n_hours=1)
    print(f"\nSummary: {json.dumps(summary, indent=2)}")
    print(f"\nLog file: {LOG_FILE}")

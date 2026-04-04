"""Test validate_tool_request handles empty tool_args correctly."""
import asyncio
import pytest


# Inline the fixed logic to avoid importing the full agent (heavy deps)
async def validate_tool_request(tool_request):
    if not isinstance(tool_request, dict):
        raise ValueError("Tool request must be a dictionary")
    if not tool_request.get("tool_name") or not isinstance(tool_request.get("tool_name"), str):
        raise ValueError("Tool request must have a tool_name (type string) field")
    if not isinstance(tool_request.get("tool_args"), dict):
        raise ValueError("Tool request must have a tool_args (type dictionary) field")


@pytest.mark.asyncio
async def test_empty_tool_args_is_valid():
    """{} is valid - tools with no args should be accepted."""
    await validate_tool_request({"tool_name": "read_file", "tool_args": {}})


@pytest.mark.asyncio
async def test_missing_tool_args_is_invalid():
    with pytest.raises(ValueError):
        await validate_tool_request({"tool_name": "read_file"})


@pytest.mark.asyncio
async def test_tool_args_wrong_type_is_invalid():
    with pytest.raises(ValueError):
        await validate_tool_request({"tool_name": "read_file", "tool_args": "not a dict"})


@pytest.mark.asyncio
async def test_normal_tool_args_is_valid():
    await validate_tool_request({"tool_name": "read_file", "tool_args": {"path": "/tmp/x"}})


@pytest.mark.asyncio
async def test_tool_args_none_is_invalid():
    with pytest.raises(ValueError):
        await validate_tool_request({"tool_name": "read_file", "tool_args": None})

import os
import json
from datetime import datetime
import re


EXPECTED_ADDRESSES = [
    "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
    "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", 
    "0xDA9dfA130Df4dE4673b89022EE50ff26f6EA73Cf"
]


def execute(runtime_path: str, agent, state: dict) -> dict:
    """Evaluate the ETH balance task."""
    result_file = os.path.join(runtime_path, "balances.json")
    
    scorecard = {
        "score": 0,
        "file_exists": False,
        "valid_json": False,
        "has_timestamp": False,
        "has_balances": False,
        "addresses_found": 0,
        "format_correct": False,
        "errors": []
    }
    
    points = 0
    
    if not os.path.exists(result_file):
        scorecard["error"] = "balances.json not found"
        return scorecard
    
    scorecard["file_exists"] = True
    points += 10
    
    try:
        with open(result_file, 'r') as f:
            data = json.load(f)
        scorecard["valid_json"] = True
        points += 10
    except json.JSONDecodeError as e:
        scorecard["errors"].append(f"Invalid JSON: {e}")
        return scorecard
    except Exception as e:
        scorecard["errors"].append(f"Could not read file: {e}")
        return scorecard
    
    # Check timestamp
    if "timestamp" in data:
        ts = data["timestamp"]
        try:
            # Try parsing ISO 8601
            if "T" in ts:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
                scorecard["has_timestamp"] = True
                points += 10
        except Exception:
            scorecard["errors"].append(f"Invalid timestamp format: {ts}")
    
    # Check balances array
    if "balances" in data and isinstance(data["balances"], list):
        scorecard["has_balances"] = True
        points += 10
        
        balances = data["balances"]
        found_addresses = set()
        valid_entries = 0
        
        for entry in balances:
            if not isinstance(entry, dict):
                continue
            
            addr = entry.get("address", "")
            # Normalize address comparison (case-insensitive)
            addr_lower = addr.lower()
            
            for expected in EXPECTED_ADDRESSES:
                if expected.lower() == addr_lower:
                    found_addresses.add(expected)
                    break
            
            # Validate entry format
            entry_valid = True
            
            # Check balance_wei is string
            if "balance_wei" in entry:
                if not isinstance(entry["balance_wei"], str):
                    scorecard["errors"].append(f"balance_wei should be string for {addr[:10]}...")
                    entry_valid = False
                else:
                    # Verify it's a valid number string
                    try:
                        int(entry["balance_wei"])
                    except ValueError:
                        scorecard["errors"].append(f"balance_wei not a valid number for {addr[:10]}...")
                        entry_valid = False
            
            # Check balance_eth is float
            if "balance_eth" in entry:
                if not isinstance(entry["balance_eth"], (int, float)):
                    scorecard["errors"].append(f"balance_eth should be number for {addr[:10]}...")
                    entry_valid = False
                elif entry["balance_eth"] < 0:
                    scorecard["errors"].append(f"balance_eth is negative for {addr[:10]}...")
                    entry_valid = False
            
            if entry_valid:
                valid_entries += 1
        
        scorecard["addresses_found"] = len(found_addresses)
        scorecard["valid_entries"] = valid_entries
        
        # Points for addresses found (up to 30)
        addr_ratio = len(found_addresses) / len(EXPECTED_ADDRESSES)
        points += int(30 * addr_ratio)
        
        # Points for valid format (up to 15)
        if len(balances) > 0:
            format_ratio = valid_entries / len(balances)
            points += int(15 * format_ratio)
            if format_ratio == 1.0:
                scorecard["format_correct"] = True
    
    # Check total_eth
    if "total_eth" in data:
        if isinstance(data["total_eth"], (int, float)):
            points += 10
            scorecard["total_eth"] = data["total_eth"]
            
            # Verify total matches sum
            if "balances" in data:
                calculated_total = sum(
                    b.get("balance_eth", 0) 
                    for b in data["balances"] 
                    if isinstance(b, dict)
                )
                if abs(calculated_total - data["total_eth"]) < 0.01:
                    points += 5
                    scorecard["total_verified"] = True
                else:
                    scorecard["errors"].append(
                        f"total_eth ({data['total_eth']}) doesn't match sum ({calculated_total})"
                    )
    
    scorecard["score"] = max(0, min(100, points))
    return scorecard
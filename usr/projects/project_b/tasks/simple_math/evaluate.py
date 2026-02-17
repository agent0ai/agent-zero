import os


def execute(runtime_path: str, agent, state: dict) -> dict:
    """Evaluate the simple math task."""
    result_file = os.path.join(runtime_path, "result.txt")
    
    # Expected answer: sum of primes 1-100 = 1060
    expected = 1060
    
    if not os.path.exists(result_file):
        return {
            "score": 0,
            "error": "result.txt not found",
            "expected": expected
        }
    
    try:
        with open(result_file, 'r') as f:
            content = f.read().strip()
            answer = int(content)
    except (ValueError, IOError) as e:
        return {
            "score": 0,
            "error": f"Could not read answer: {e}",
            "expected": expected
        }
    
    if answer == expected:
        return {
            "score": 100,
            "answer": answer,
            "expected": expected,
            "comment": "Perfect!"
        }
    else:
        # Partial credit based on how close
        diff = abs(answer - expected)
        if diff < 10:
            score = 80
        elif diff < 50:
            score = 50
        elif diff < 100:
            score = 25
        else:
            score = 0
        
        return {
            "score": score,
            "answer": answer,
            "expected": expected,
            "difference": diff,
            "comment": "Incorrect answer"
        }
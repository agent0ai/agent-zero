import os
import json
import subprocess


def execute(runtime_path: str, agent, state: dict) -> dict:
    """Evaluate the git project task."""
    scorecard = {
        "score": 0,
        "repo_cloned": False,
        "package_installed": False,
        "output_valid": False,
        "output_is_json": False,
        "errors": []
    }
    
    points = 0
    
    # Check if repo was cloned
    jc_dir = os.path.join(runtime_path, "jc")
    if os.path.exists(jc_dir) and os.path.isdir(jc_dir):
        scorecard["repo_cloned"] = True
        points += 25
        
        # Check for key files
        if os.path.exists(os.path.join(jc_dir, "setup.py")) or \
           os.path.exists(os.path.join(jc_dir, "pyproject.toml")):
            points += 5
    else:
        scorecard["errors"].append("Repository not cloned to expected location")
    
    # Check if jc is installed
    try:
        result = subprocess.run(
            ["jc", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            scorecard["package_installed"] = True
            scorecard["jc_version"] = result.stdout.strip()
            points += 25
    except Exception as e:
        scorecard["errors"].append(f"jc not installed or not in PATH: {e}")
    
    # Check output.txt
    output_file = os.path.join(runtime_path, "output.txt")
    if os.path.exists(output_file):
        points += 10
        
        try:
            with open(output_file, 'r') as f:
                content = f.read().strip()
            
            if content:
                scorecard["output_valid"] = True
                points += 10
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    scorecard["output_is_json"] = True
                    scorecard["output_preview"] = str(parsed)[:200]
                    points += 20
                except json.JSONDecodeError:
                    scorecard["errors"].append("Output is not valid JSON")
                    scorecard["output_preview"] = content[:200]
        except Exception as e:
            scorecard["errors"].append(f"Could not read output.txt: {e}")
    else:
        scorecard["errors"].append("output.txt not found")
    
    # Check errors.txt exists
    errors_file = os.path.join(runtime_path, "errors.txt")
    if os.path.exists(errors_file):
        points += 5
        try:
            with open(errors_file, 'r') as f:
                error_content = f.read().strip()
            if error_content:
                scorecard["reported_errors"] = error_content[:500]
        except Exception:
            pass
    
    scorecard["score"] = max(0, min(100, points))
    return scorecard
import json
import urllib.error
import urllib.request

from helpers.api import ApiHandler, Request, Response


class ResolveHfRepo(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        repo = str(input.get("repo", "") or "").strip()
        if not repo:
            return {"success": False, "error": "No repo ID provided."}

        try:
            url = f"https://huggingface.co/api/models/{repo}"
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"success": False, "error": f"Repo '{repo}' not found."}
            return {"success": False, "error": f"HuggingFace API error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Network error: {e}"}

        files = [s["rfilename"] for s in data.get("siblings", [])]

        # Find model: prefer full-precision .onnx
        onnx_files = [f for f in files if f.endswith(".onnx")]
        if not onnx_files:
            return {"success": False, "error": f"No .onnx file found in {repo}."}
        model_file = next(
            (
                f
                for f in onnx_files
                if not any(q in f.lower() for q in ("int8", "quantized", "fp16", "q8"))
            ),
            onnx_files[0],
        )

        # Find voices: .npz or .bin (not .onnx)
        voices_files = [
            f
            for f in files
            if f.endswith(".npz") or (f.endswith(".bin") and not f.endswith(".onnx"))
        ]
        if not voices_files:
            return {
                "success": False,
                "error": f"No voices file (.npz or .bin) found in {repo}.",
            }
        # Prefer .npz over .bin
        npz_files = [f for f in voices_files if f.endswith(".npz")]
        voices_file = npz_files[0] if npz_files else voices_files[0]

        return {
            "success": True,
            "repo": repo,
            "model_file": model_file,
            "voices_file": voices_file,
            "all_files": files,
        }

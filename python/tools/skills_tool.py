from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List

from python.helpers.tool import Tool, Response
from python.helpers import files
from python.helpers import skills as skills_helper
from python.helpers import frameworks


class SkillsTool(Tool):
    """
    Manage and use SKILL.md-based Skills (Anthropic open standard).

    Methods (tool_args.method):
      - list
      - search (query)
      - load (skill_name)
      - read_file (skill_name, file_path)
      - execute_script (skill_name, script_path, script_args, arg_style)

    arg_style options for execute_script:
      - "positional" (default): Pass values as positional args (sys.argv[1], sys.argv[2])
        Example: {"input": "file.pdf", "output": "/tmp"} → sys.argv = ['script.py', 'file.pdf', '/tmp']
      - "named": Pass as --key value pairs (for argparse/click scripts)
        Example: {"input": "file.pdf", "output": "/tmp"} → sys.argv = ['script.py', '--input', 'file.pdf', '--output', '/tmp']
      - "env": Only use environment variables (SKILL_ARG_INPUT, SKILL_ARG_OUTPUT)

    Environment variables (SKILL_ARG_*) are always set regardless of arg_style.
    """

    async def execute(self, **kwargs) -> Response:
        method = (
            (kwargs.get("method") or self.args.get("method") or self.method or "")
            .strip()
            .lower()
        )

        try:
            if method == "list":
                return Response(message=self._list(), break_loop=False)
            if method == "search":
                query = str(kwargs.get("query") or "").strip()
                return Response(message=self._search(query), break_loop=False)
            if method == "load":
                skill_name = str(kwargs.get("skill_name") or "").strip()
                return Response(message=self._load(skill_name), break_loop=False)
            if method == "read_file":
                skill_name = str(kwargs.get("skill_name") or "").strip()
                file_path = str(kwargs.get("file_path") or "").strip()
                return Response(message=self._read_file(skill_name, file_path), break_loop=False)
            if method == "execute_script":
                skill_name = str(kwargs.get("skill_name") or "").strip()
                script_path = str(kwargs.get("script_path") or "").strip()
                script_args = kwargs.get("script_args") or {}
                if not isinstance(script_args, dict):
                    script_args = {}
                # arg_style: "positional" (default), "named" (--key value), or "env" (env vars only)
                arg_style = str(kwargs.get("arg_style") or "positional").strip().lower()
                return await self._execute_script(skill_name, script_path, script_args, arg_style)

            return Response(
                message=(
                    "Error: missing/invalid 'method'. Supported methods: "
                    "list, search, load, read_file, execute_script."
                ),
                break_loop=False,
            )
        except Exception as e:  # keep tool robust; return error instead of crashing loop
            return Response(message=f"Error in skills_tool: {e}", break_loop=False)

    def _get_active_framework_id(self) -> str | None:
        """Get the active framework ID from the agent's context."""
        try:
            framework = frameworks.get_active_framework(self.agent.context)
            return framework.id if framework else None
        except Exception:
            return None

    def _list(self) -> str:
        framework_id = self._get_active_framework_id()
        skills = skills_helper.list_skills(include_content=False, dedupe=True, framework_id=framework_id)
        if not skills:
            return "No skills found. Expected SKILL.md files under: skills/{custom,builtin,shared}."

        # Stable output: sort by name
        skills_sorted = sorted(skills, key=lambda s: (s.name.lower(), s.source))

        lines: List[str] = []
        lines.append(f"Available skills ({len(skills_sorted)}):")
        for s in skills_sorted:
            tags = f" tags={','.join(s.tags)}" if s.tags else ""
            ver = f" v{s.version}" if s.version else ""
            desc = (s.description or "").strip()
            if len(desc) > 200:
                desc = desc[:200].rstrip() + "…"
            lines.append(f"- {s.name}{ver} [{s.source}]{tags}: {desc}")
        lines.append("")
        lines.append("Tip: use skills_tool method=search or method=load for details.")
        return "\n".join(lines)

    def _search(self, query: str) -> str:
        if not query:
            return "Error: 'query' is required for method=search."

        framework_id = self._get_active_framework_id()
        results = skills_helper.search_skills(query, limit=25, framework_id=framework_id)
        if not results:
            return f"No skills matched query: {query!r}"

        lines: List[str] = []
        lines.append(f"Skills matching {query!r} ({len(results)}):")
        for s in results:
            desc = (s.description or "").strip()
            if len(desc) > 200:
                desc = desc[:200].rstrip() + "…"
            lines.append(f"- {s.name} [{s.source}]: {desc}")
        lines.append("")
        lines.append("Tip: use skills_tool method=load skill_name=<name> to load full instructions.")
        return "\n".join(lines)

    def _load(self, skill_name: str) -> str:
        if not skill_name:
            return "Error: 'skill_name' is required for method=load."

        framework_id = self._get_active_framework_id()
        skill = skills_helper.find_skill(skill_name, include_content=True, framework_id=framework_id)
        if not skill:
            return f"Error: skill not found: {skill_name!r}. Try skills_tool method=list or method=search."

        # Enumerate files under the skill directory for progressive disclosure
        referenced_files = self._list_skill_files(skill.path, max_files=80)
        rel_skill_dir = Path(files.deabsolute_path(str(skill.path)))

        lines: List[str] = []
        lines.append(f"Skill: {skill.name}")
        lines.append(f"Source: {skill.source}")
        lines.append(f"Path: {rel_skill_dir}")
        if skill.version:
            lines.append(f"Version: {skill.version}")
        if skill.author:
            lines.append(f"Author: {skill.author}")
        if skill.license:
            lines.append(f"License: {skill.license}")
        if skill.tags:
            lines.append(f"Tags: {', '.join(skill.tags)}")
        if skill.allowed_tools:
            lines.append(f"Allowed tools: {', '.join(skill.allowed_tools)}")
        if skill.triggers:
            lines.append(f"Triggers: {', '.join(skill.triggers)}")

        lines.append("")
        if skill.description:
            lines.append("Description:")
            lines.append(skill.description.strip())
            lines.append("")

        lines.append("Content (SKILL.md body):")
        lines.append(skill.content.strip() or "(empty)")
        lines.append("")

        if referenced_files:
            lines.append("Files in skill directory (use skills_tool method=read_file to open):")
            for p in referenced_files:
                lines.append(f"- {p}")
        else:
            lines.append("No additional files found in skill directory.")

        return "\n".join(lines)

    def _read_file(self, skill_name: str, file_path: str) -> str:
        if not skill_name:
            return "Error: 'skill_name' is required for method=read_file."
        if not file_path:
            return "Error: 'file_path' is required for method=read_file."

        framework_id = self._get_active_framework_id()
        skill = skills_helper.find_skill(skill_name, include_content=False, framework_id=framework_id)
        if not skill:
            return f"Error: skill not found: {skill_name!r}."

        try:
            target = skills_helper.safe_path_within_dir(skill.path, file_path)
        except Exception as e:
            return f"Error: invalid file_path: {e}"

        if not target.exists() or not target.is_file():
            return f"Error: file not found: {file_path!r} (within skill {skill.name})"

        # Basic binary guard: if null byte present, do not dump
        content = target.read_bytes()
        if b"\x00" in content[:4096]:
            return f"Error: file appears to be binary; refusing to print raw bytes ({file_path})."

        text = content.decode("utf-8", errors="replace")
        return f"File: {file_path}\n\n{text}"

    async def _execute_script(
        self, skill_name: str, script_path: str, script_args: Dict[str, Any],
        arg_style: str = "positional"
    ) -> Response:
        if not skill_name:
            return Response(message="Error: 'skill_name' is required for method=execute_script.", break_loop=False)
        if not script_path:
            return Response(message="Error: 'script_path' is required for method=execute_script.", break_loop=False)

        framework_id = self._get_active_framework_id()
        skill = skills_helper.find_skill(skill_name, include_content=False, framework_id=framework_id)
        if not skill:
            return Response(message=f"Error: skill not found: {skill_name!r}.", break_loop=False)

        try:
            script_abs = skills_helper.safe_path_within_dir(skill.path, script_path)
        except Exception as e:
            return Response(message=f"Error: invalid script_path: {e}", break_loop=False)

        if not script_abs.exists() or not script_abs.is_file():
            return Response(message=f"Error: script not found: {script_path!r} (within skill {skill.name})", break_loop=False)

        ext = script_abs.suffix.lower()
        runtime: str
        code: str

        # Use /a0 paths for remote (SSH) execution inside the container; use local absolute paths otherwise.
        if self.agent.config.code_exec_ssh_enabled:
            script_runtime_path = files.normalize_a0_path(str(script_abs))
            script_runtime_dir = files.normalize_a0_path(str(script_abs.parent))
        else:
            script_runtime_path = str(script_abs)
            script_runtime_dir = str(script_abs.parent)

        # Build environment variables (SKILL_ARG_*) - always set as fallback
        env_vars: Dict[str, str] = {}
        for k, v in (script_args or {}).items():
            env_key = f"SKILL_ARG_{re.sub(r'[^A-Za-z0-9_]', '_', str(k).upper())}"
            env_vars[env_key] = str(v)

        # Build CLI args based on arg_style:
        # - "positional": ['value1', 'value2'] - for scripts using sys.argv[1], sys.argv[2]
        # - "named": ['--key1', 'value1', '--key2', 'value2'] - for argparse/click scripts
        # - "env": [] - only use environment variables, no CLI args
        cli_args: List[str] = []
        if arg_style == "positional":
            cli_args = [str(v) for v in (script_args or {}).values()]
        elif arg_style == "named":
            for k, v in (script_args or {}).items():
                cli_args.append(f"--{k}")
                cli_args.append(str(v))
        # "env" style: cli_args stays empty, only env vars are used

        if ext == ".py":
            runtime = "python"
            # Set env vars (always available as fallback)
            env_lines = [f"os.environ[{json.dumps(k)}] = {json.dumps(v)}" for k, v in env_vars.items()]
            env_setup = "\n".join(env_lines) if env_lines else "pass"
            # Set sys.argv: ['script.py', ...cli_args]
            argv_list = [script_runtime_path] + cli_args
            argv_setup = f"sys.argv = {json.dumps(argv_list)}"
            code = (
                "import os, sys, runpy\n"
                f"os.chdir({json.dumps(script_runtime_dir)})\n"
                f"{env_setup}\n"
                f"{argv_setup}\n"
                f"runpy.run_path({json.dumps(script_runtime_path)}, run_name='__main__')\n"
            )
        elif ext == ".js":
            runtime = "nodejs"
            # Set process.env (always available as fallback)
            env_lines = [f"process.env[{json.dumps(k)}] = {json.dumps(v)};" for k, v in env_vars.items()]
            env_setup = "\n".join(env_lines) if env_lines else ""
            # Node.js argv: ['node', 'script.js', ...cli_args]
            argv_list = ["node", script_runtime_path] + cli_args
            code = (
                f"process.chdir({json.dumps(script_runtime_dir)});\n"
                f"{env_setup}\n"
                f"process.argv = {json.dumps(argv_list)};\n"
                f"require({json.dumps(script_runtime_path)});\n"
            )
        elif ext == ".sh":
            runtime = "terminal"
            # Environment variables (always available as fallback)
            env_parts = [f"{k}={shlex.quote(v)}" for k, v in env_vars.items()]
            env_prefix = " ".join(env_parts)
            # Pass CLI args to script
            cli_args_str = " ".join(shlex.quote(a) for a in cli_args)
            cd_cmd = f"cd {shlex.quote(script_runtime_dir)}"
            run_cmd = f"bash {shlex.quote(script_runtime_path)}"
            if cli_args_str:
                run_cmd = f"{run_cmd} {cli_args_str}"
            if env_prefix:
                code = f"{cd_cmd} && {env_prefix} {run_cmd}"
            else:
                code = f"{cd_cmd} && {run_cmd}"
        else:
            return Response(
                message=f"Error: unsupported script type {ext!r}. Supported: .py, .js, .sh",
                break_loop=False,
            )

        # Delegate actual execution to code_execution_tool (sandboxed)
        from python.tools.code_execution_tool import CodeExecution

        cet = CodeExecution(
            agent=self.agent,
            name="code_execution_tool",
            method=None,
            args={
                "runtime": runtime,
                "code": code,
                "session": int(self.args.get("session", 0) or 0),
            },
            message=self.message,
            loop_data=self.loop_data,
        )

        # Must call before_execution to initialize self.log before execute()
        await cet.before_execution(**cet.args)
        resp = await cet.execute(**cet.args)
        # Wrap result to make it clear it was a skill script
        wrapped = (
            f"Executed script: {skill.name}/{script_path}\n"
            f"Runtime: {runtime}\n\n"
            f"{resp.message}"
        )
        return Response(message=wrapped, break_loop=False)

    def _list_skill_files(self, skill_dir: Path, *, max_files: int = 80) -> List[str]:
        if not skill_dir.exists():
            return []

        results: List[str] = []

        preferred_dirs = ["scripts", "references", "assets", "templates", "docs"]

        # 1) Root-level files (excluding SKILL.md)
        try:
            for p in sorted(skill_dir.iterdir(), key=lambda x: x.name):
                if len(results) >= max_files:
                    return results
                if p.name.startswith("."):
                    continue
                if p.is_file():
                    if p.name == "SKILL.md":
                        continue
                    results.append(p.name)
        except Exception:
            pass

        # 2) Preferred optional directories (one level deep)
        for dname in preferred_dirs:
            dpath = skill_dir / dname
            if not dpath.exists() or not dpath.is_dir():
                continue
            try:
                for p in sorted(dpath.iterdir(), key=lambda x: x.name):
                    if len(results) >= max_files:
                        return results
                    if p.name.startswith("."):
                        continue
                    if p.is_file():
                        results.append(f"{dname}/{p.name}")
                    elif p.is_dir():
                        # Show one nested level (common in assets/templates/*)
                        nested_added = False
                        try:
                            for sub in sorted(p.iterdir(), key=lambda x: x.name):
                                if sub.name.startswith("."):
                                    continue
                                if sub.is_file():
                                    results.append(f"{dname}/{p.name}/{sub.name}")
                                    nested_added = True
                                    break
                        except Exception:
                            pass
                        if not nested_added:
                            results.append(f"{dname}/{p.name}/")
            except Exception:
                continue

        # 3) Other directories (one level deep)
        try:
            for p in sorted(skill_dir.iterdir(), key=lambda x: x.name):
                if len(results) >= max_files:
                    return results
                if p.name.startswith(".") or p.name in preferred_dirs:
                    continue
                if p.is_dir():
                    for sub in sorted(p.iterdir(), key=lambda x: x.name):
                        if len(results) >= max_files:
                            return results
                        if sub.name.startswith("."):
                            continue
                        if sub.is_file():
                            results.append(f"{p.name}/{sub.name}")
        except Exception:
            pass

        return results



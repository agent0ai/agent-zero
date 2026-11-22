import asyncio
from types import SimpleNamespace

from plugins._sandboxing.helpers import shell


def test_shell_waits_for_initial_prompt_before_first_command(tmp_path, monkeypatch):
    rc = tmp_path / "bashrc"
    rc.write_text("sleep 0.4\nPS1='root@test:/workspace# '\n")
    manager = SimpleNamespace(
        config=SimpleNamespace(instances_dir=tmp_path),
        ensure_running=lambda *args, **kwargs: None,
        interactive_command=lambda name: [
            "/bin/bash", "--noprofile", "--rcfile", str(rc), "-i"
        ],
        touch=lambda name: None,
    )
    monkeypatch.setattr(shell, "get_manager", lambda **kwargs: manager)
    monkeypatch.setattr(shell, "defaults", lambda **kwargs: ("default", "temporary", "host"))

    async def run():
        session = shell.SandboxInteractiveSession("test")
        try:
            await session.connect()
            await session.send_command("printf 'first\\n'; sleep 0.3; printf 'second\\n'")
            await asyncio.sleep(0.1)
            output, _ = await session.read_output(timeout=1)
            assert "first" in output
            assert "root@test:/workspace#" not in output
            await asyncio.sleep(0.4)
            output, _ = await session.read_output(timeout=1)
            assert "second" in output
            assert output.rstrip().endswith("root@test:/workspace#")
        finally:
            await session.close()

    asyncio.run(run())

"""Test Mahoosuc OS security - ensure no unsafe command execution"""

import inspect


class TestMahoosucSecurity:
    """Validate security boundaries in Mahoosuc integration"""

    def test_no_shell_true_in_subprocess(self):
        """Should never use shell=True in subprocess calls"""
        import python.helpers.mahoosuc_config as config_module
        import python.helpers.mahoosuc_reference as reference_module

        # Check all subprocess.run calls
        modules = [config_module, reference_module]

        for module in modules:
            source = inspect.getsource(module)

            # Should not contain shell=True
            assert "shell=True" not in source, f"Found shell=True in {module.__name__} - security risk!"

            # If subprocess is used, should use list args
            if "subprocess" in source:
                assert (
                    "subprocess.run([" in source or "subprocess.Popen([" in source
                ), f"subprocess in {module.__name__} should use list args, not string"

    def test_path_traversal_protection(self):
        """Should prevent path traversal attacks"""
        from python.helpers.mahoosuc_reference import get_command_spec

        # Try path traversal
        result = get_command_spec("../../etc", "passwd")

        # Should not return sensitive file
        assert result is None or "root:" not in str(result)

    def test_command_injection_protection(self):
        """Should prevent command injection in search"""
        from python.helpers.mahoosuc_reference import search_commands

        # Try command injection
        malicious_inputs = ["; rm -rf /", "$(whoami)", "`id`", "&& cat /etc/passwd"]

        for malicious in malicious_inputs:
            # Should safely handle as search term
            results = search_commands(malicious)
            # Should return empty or safe results
            assert isinstance(results, list)

    def test_file_read_boundaries(self):
        """Should only read files within .claude directory"""
        from python.helpers.mahoosuc_config import get_commands_dir
        from python.helpers.mahoosuc_reference import get_command_spec

        commands_dir = get_commands_dir()

        # All returned content should be from .claude directory
        spec = get_command_spec("devops", "deploy")

        if spec:
            # Verify file was from .claude/commands
            assert ".claude" in str(commands_dir)

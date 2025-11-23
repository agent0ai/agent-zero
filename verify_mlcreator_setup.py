#!/usr/bin/env python3
"""
Verify MLcreator Setup for Agent Zero
This script verifies that all components are properly configured.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import sys

# Add Agent Zero to path
sys.path.insert(0, str(Path(__file__).parent))


class MLCreatorSetupVerifier:
    def __init__(self):
        self.agent_zero_path = Path.cwd()
        self.mlcreator_path = Path("D:/GithubRepos/MLcreator")
        self.memory_subdir = "mlcreator"
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def print_header(self, text):
        """Print section header"""
        print(f"\n{'=' * 60}")
        print(f"  {text}")
        print(f"{'=' * 60}")

    def check_mark(self, passed, message):
        """Print check result"""
        if passed:
            print(f"  ✅ {message}")
            self.checks_passed += 1
        else:
            print(f"  ❌ {message}")
            self.checks_failed += 1

    def warning(self, message):
        """Print warning"""
        print(f"  ⚠️ {message}")
        self.warnings += 1

    def check_directories(self):
        """Check if all required directories exist"""
        self.print_header("Checking Directory Structure")

        directories = {
            "Memory": self.agent_zero_path / "memory" / self.memory_subdir,
            "Memory DB": self.agent_zero_path / "memory" / self.memory_subdir / "db",
            "Knowledge": self.agent_zero_path / "knowledge" / self.memory_subdir,
            "Knowledge/main": self.agent_zero_path / "knowledge" / self.memory_subdir / "main",
            "Knowledge/solutions": self.agent_zero_path / "knowledge" / self.memory_subdir / "solutions",
            "Knowledge/fragments": self.agent_zero_path / "knowledge" / self.memory_subdir / "fragments",
            "Knowledge/instruments": self.agent_zero_path / "knowledge" / self.memory_subdir / "instruments",
            "Prompts": self.agent_zero_path / "prompts" / self.memory_subdir,
            "Instruments": self.agent_zero_path / "instruments" / self.memory_subdir
        }

        for name, path in directories.items():
            self.check_mark(path.exists(), f"{name}: {path}")

    def check_configuration_files(self):
        """Check configuration files"""
        self.print_header("Checking Configuration Files")

        files = {
            "CLAUDE.md": self.agent_zero_path / "prompts" / self.memory_subdir / "CLAUDE.md",
            "AGENTS.md": self.agent_zero_path / "prompts" / self.memory_subdir / "AGENTS.md",
            ".env": self.agent_zero_path / ".env",
            "populate_mlcreator_knowledge.py": self.agent_zero_path / "populate_mlcreator_knowledge.py",
            "init_mlcreator_memory.py": self.agent_zero_path / "init_mlcreator_memory.py"
        }

        for name, path in files.items():
            self.check_mark(path.exists(), f"{name}: {path.name}")

        # Check .env contents
        env_path = self.agent_zero_path / ".env"
        if env_path.exists():
            content = env_path.read_text()
            if "MEMORY_SUBDIR=mlcreator" in content:
                self.check_mark(True, ".env contains MLcreator settings")
            else:
                self.warning(".env exists but missing MLcreator settings")

    def check_knowledge_files(self):
        """Check knowledge base files"""
        self.print_header("Checking Knowledge Base")

        knowledge_base = self.agent_zero_path / "knowledge" / self.memory_subdir

        expected_files = {
            "main/project_overview.md": "Project overview",
            "main/architecture.md": "Architecture documentation",
            "main/conventions.md": "Coding conventions",
            "main/dependencies.md": "Dependencies documentation",
            "solutions/unity_patterns.md": "Unity patterns",
            "solutions/gamecreator_solutions.md": "Game Creator solutions",
            "instruments/activation_scripts.md": "Activation scripts documentation"
        }

        for file_path, description in expected_files.items():
            full_path = knowledge_base / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.check_mark(True, f"{description} ({size:,} bytes)")
            else:
                self.check_mark(False, f"{description} (missing)")

        # Count total knowledge files
        if knowledge_base.exists():
            total_files = sum(1 for _ in knowledge_base.rglob("*.md"))
            print(f"\n  📊 Total knowledge files: {total_files}")

    async def check_memory_database(self):
        """Check memory database"""
        self.print_header("Checking Memory Database")

        try:
            from python.helpers.memory import Memory

            # Try to get memory instance
            db = await Memory.get_by_subdir(
                memory_subdir=self.memory_subdir,
                log_item=None,
                preload_knowledge=False
            )

            self.check_mark(True, "Memory database accessible")

            # Try a test search
            results = await db.search_similarity_threshold(
                query="Unity Game Creator",
                limit=5,
                threshold=0.5
            )

            if results:
                self.check_mark(True, f"Memory search functional ({len(results)} results found)")
            else:
                self.warning("Memory search returned no results")

            # Check for FAISS index
            db_path = self.agent_zero_path / "memory" / self.memory_subdir / "db"
            if (db_path / "index.faiss").exists():
                self.check_mark(True, "FAISS index file exists")
            else:
                self.check_mark(False, "FAISS index file missing")

        except Exception as e:
            self.check_mark(False, f"Memory database error: {e}")

    def check_mlcreator_project(self):
        """Check MLcreator project"""
        self.print_header("Checking MLcreator Project")

        if not self.mlcreator_path.exists():
            self.check_mark(False, f"MLcreator project not found at {self.mlcreator_path}")
            return

        self.check_mark(True, f"MLcreator project found at {self.mlcreator_path}")

        # Check key MLcreator files
        important_files = {
            "MLcreator.sln": "Solution file",
            "activate-unity.ps1": "Unity activation script",
            "activate-ai.ps1": "AI activation script",
            "ML_AgentsConfig": "ML-Agents configuration directory",
            "Assets": "Unity assets directory"
        }

        for file_name, description in important_files.items():
            file_path = self.mlcreator_path / file_name
            self.check_mark(file_path.exists(), f"{description}: {file_name}")

    def check_python_environment(self):
        """Check Python environment"""
        self.print_header("Checking Python Environment")

        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Check Python version
        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            self.check_mark(True, f"Python version: {python_version} (compatible)")
        else:
            self.check_mark(False, f"Python version: {python_version} (requires 3.10+)")

        # Check required packages
        required_packages = [
            "langchain",
            "langchain_community",
            "faiss-cpu",
            "sentence-transformers"
        ]

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.check_mark(True, f"Package '{package}' installed")
            except ImportError:
                self.check_mark(False, f"Package '{package}' not installed")

    def generate_report(self):
        """Generate setup report"""
        self.print_header("Setup Verification Report")

        total_checks = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0

        print(f"\n  ✅ Checks passed: {self.checks_passed}")
        print(f"  ❌ Checks failed: {self.checks_failed}")
        print(f"  ⚠️ Warnings: {self.warnings}")
        print(f"  📊 Success rate: {success_rate:.1f}%")

        if self.checks_failed == 0:
            print("\n  🎉 All checks passed! MLcreator setup is complete.")
        elif self.checks_failed <= 3:
            print("\n  ⚠️ Setup mostly complete. Please address the failed checks.")
        else:
            print("\n  ❌ Setup incomplete. Please run setup_mlcreator_complete.bat")

        # Generate report file
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "success_rate": success_rate,
            "agent_zero_path": str(self.agent_zero_path),
            "mlcreator_path": str(self.mlcreator_path)
        }

        report_path = Path("mlcreator_setup_report.json")
        report_path.write_text(json.dumps(report, indent=2))
        print(f"\n  📄 Detailed report saved to: {report_path}")

    async def run(self):
        """Run all verification checks"""
        print("🔍 MLcreator Setup Verification for Agent Zero")
        print("=" * 60)

        # Run checks
        self.check_directories()
        self.check_configuration_files()
        self.check_knowledge_files()
        await self.check_memory_database()
        self.check_mlcreator_project()
        self.check_python_environment()

        # Generate report
        self.generate_report()

        print("\n" + "=" * 60)
        print("Verification complete!")


if __name__ == "__main__":
    verifier = MLCreatorSetupVerifier()
    asyncio.run(verifier.run())
"""Setup script for browser-agent package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="browser-agent",
    version="1.0.0",
    description="Natural language web automation using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Agent Zero Team",
    author_email="",
    url="https://github.com/frdel/agent-zero",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "browser_agent": [
            "js/*.js",
            "prompts/*.md",
        ],
    },
    install_requires=[
        "browser-use==0.5.11",
        "playwright==1.52.0",
        "litellm>=1.75.0",
        "python-dotenv==1.1.0",
        "nest-asyncio==1.6.0",
        "pydantic>=2.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "browser-agent=cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="browser automation selenium playwright AI LLM natural-language",
)

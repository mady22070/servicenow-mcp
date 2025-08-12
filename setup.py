#!/usr/bin/env python3
"""
Setup script for ServiceNow MCP Server
"""

from setuptools import setup, find_packages
import os

def read_version():
    """Read version from version.py file safely."""
    version_file = os.path.join(os.path.dirname(__file__), 'servicenow_mcp', 'version.py')
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            version_globals = {}
            exec(f.read(), version_globals)
            return version_globals['__version__']
    except (FileNotFoundError, KeyError) as e:
        raise RuntimeError(f"Unable to find version string: {e}")

def read_file(filename):
    """Read file content safely."""
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""

def read_requirements(filename):
    """Read requirements from file, filtering comments and empty lines."""
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return [
                line.strip() 
                for line in fh 
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []

# Read version, description, and requirements
__version__ = read_version()
long_description = read_file("README.md")
requirements = read_requirements("requirements.txt")

setup(
    name="servicenow-mcp",
    version=__version__,
    author="ServiceNow MCP Contributors",
    author_email="servicenow-mcp@example.com",
    maintainer="ServiceNow MCP Team",
    maintainer_email="servicenow-mcp@example.com",
    description="A comprehensive Model Context Protocol server for ServiceNow integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/servicenow-mcp",
    project_urls={
        "Homepage": "https://github.com/yourusername/servicenow-mcp",
        "Bug Tracker": "https://github.com/yourusername/servicenow-mcp/issues",
        "Documentation": "https://github.com/yourusername/servicenow-mcp/wiki",
        "Source Code": "https://github.com/yourusername/servicenow-mcp",
        "Changelog": "https://github.com/yourusername/servicenow-mcp/blob/main/CHANGELOG.md",
        "Discussions": "https://github.com/yourusername/servicenow-mcp/discussions",
    },
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Framework :: FastAPI",
        "Environment :: Console",
        "Natural Language :: English",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": read_requirements("requirements-dev.txt") or [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "servicenow-mcp=servicenow_mcp.mcp_adapter:main",
            "servicenow-mcp-doctor=doctor:main",
        ],
    },
    include_package_data=True,
    package_data={
        "servicenow_mcp": [
            "py.typed",  # PEP 561 marker for type information
        ],
    },
    keywords=[
        "servicenow",
        "mcp",
        "model-context-protocol",
        "ai",
        "automation",
        "itsm",
        "cmdb",
        "api",
        "integration",
    ],
    zip_safe=False,
    # Ensure we have minimum required data
    platforms=["any"],
    # Add security contact for vulnerability reports
    # This follows PEP 566 recommendations
)
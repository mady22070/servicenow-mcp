#!/usr/bin/env python3
"""
Setup script for ServiceNow MCP Server
"""

from setuptools import setup, find_packages
import os
from typing import List, Dict, Any

# Project constants
PACKAGE_NAME = "servicenow-mcp"
PACKAGE_DIR = "servicenow_mcp"
GITHUB_USER = "mady22070"
GITHUB_REPO = f"{GITHUB_USER}/servicenow-mcp"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"

def read_version() -> str:
    """Read version from version.py file safely.
    
    Returns:
        str: Version string from version.py
        
    Raises:
        RuntimeError: If version file cannot be read or parsed
    """
    version_file = os.path.join(os.path.dirname(__file__), PACKAGE_DIR, 'version.py')
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            version_globals = {'__builtins__': {}}  # Restrict builtins for security
            exec(f.read(), version_globals)
            return version_globals['__version__']
    except (FileNotFoundError, KeyError) as e:
        raise RuntimeError(f"Unable to find version string: {e}")
    except Exception as e:
        raise RuntimeError(f"Error reading version file: {e}")

def read_file(filename: str) -> str:
    """Read file content safely.
    
    Args:
        filename: Path to file to read
        
    Returns:
        str: File content or empty string if file not found
    """
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""

def read_requirements(filename: str) -> List[str]:
    """Read requirements from file, filtering comments and empty lines.
    
    Args:
        filename: Path to requirements file
        
    Returns:
        List[str]: List of requirement strings
    """
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return [
                line.strip() 
                for line in fh 
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []

def validate_setup() -> bool:
    """Validate setup configuration before building.
    
    Returns:
        bool: True if validation passes
        
    Raises:
        RuntimeError: If validation fails
    """
    # Check if required files exist
    required_files = ["README.md", "requirements.txt", f"{PACKAGE_DIR}/__init__.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        raise RuntimeError(f"Missing required files: {missing_files}")
    
    # Validate version format
    version = read_version()
    if not version or not isinstance(version, str):
        raise RuntimeError(f"Invalid version format: {version}")
    
    return True

# Validate setup configuration
validate_setup()

# Read version, description, and requirements
__version__ = read_version()
long_description = read_file("README.md")
requirements = read_requirements("requirements.txt")

setup(
    name=PACKAGE_NAME,
    version=__version__,
    author="ServiceNow MCP Contributors",
    author_email=f"{GITHUB_USER}@users.noreply.github.com",
    maintainer="ServiceNow MCP Team",
    maintainer_email=f"{GITHUB_USER}@users.noreply.github.com",
    description="A comprehensive Model Context Protocol server for ServiceNow integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=GITHUB_URL,
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
            # Fallback dev dependencies if requirements-dev.txt is missing
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "bandit>=1.7.0",
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
            "pytest-asyncio>=0.21.0",
        ],
        "security": [
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
        "performance": [
            "memory-profiler>=0.60.0",
            "line-profiler>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            f"{PACKAGE_NAME}={PACKAGE_DIR}.mcp_adapter:main",
            f"{PACKAGE_NAME}-doctor=doctor:main",
        ],
    },
    include_package_data=True,
    package_data={
        PACKAGE_DIR: [
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
    project_urls={
        "Homepage": GITHUB_URL,
        "Bug Tracker": f"{GITHUB_URL}/issues",
        "Documentation": f"{GITHUB_URL}/wiki",
        "Source Code": GITHUB_URL,
        "Changelog": f"{GITHUB_URL}/blob/main/CHANGELOG.md",
        "Discussions": f"{GITHUB_URL}/discussions",
        "Funding": f"{GITHUB_URL}/sponsors",
        "Security": f"{GITHUB_URL}/security/policy",
    },
    zip_safe=False,
    platforms=["any"],
    # Security contact for vulnerability reports (PEP 566)
    # Note: This would be added to project metadata when supported
)
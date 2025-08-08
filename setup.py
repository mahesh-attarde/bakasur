#!/usr/bin/env python3
"""
Setup script for CFG Analyzer package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="cfg-analyzer",
    version="1.0.0",
    description="A comprehensive Control Flow Graph analysis toolkit for assembly code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CFG Analysis Session",
    author_email="",
    url="https://github.com/user/cfg-analyzer",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    python_requires=">=3.6",
    
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    
    extras_require={
        "visualization": ["graphviz"],  # For generating PNG from DOT files
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "cfg-tool=cfg_tool:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Analysis Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    keywords="control-flow-graph assembly parsing visualization loop-detection",
    
    project_urls={
        "Bug Reports": "https://github.com/user/cfg-analyzer/issues",
        "Source": "https://github.com/user/cfg-analyzer/",
    },
)

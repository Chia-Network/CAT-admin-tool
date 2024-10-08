#!/usr/bin/env python

from __future__ import annotations

from setuptools import find_packages, setup

with open("README.md", "rt") as fh:
    long_description = fh.read()

dependencies = [
    "chia-blockchain==2.4.2",
]

dev_dependencies = [
    "black==24.8.0",
    "pytest",
    "pytest-asyncio",
    "pytest-env",
    "pre-commit==3.5.0; python_version < '3.9'",
    "pre-commit==4.0.0; python_version >= '3.9'",
    "mypy==1.11.1",
]

setup(
    name="CAT_admin_tool",
    version="0.0.1",
    author="Quexington",
    packages=find_packages(exclude=("tests",)),
    entry_points={
        "console_scripts": [
            "cats = cats.cats:main",
            "secure_the_bag = cats.secure_the_bag:main",
            "unwind_the_bag = cats.unwind_the_bag:main",
        ],
    },
    author_email="m.hauff@chia.net",
    setup_requires=["setuptools_scm"],
    install_requires=dependencies,
    url="https://github.com/Chia-Network",
    license="https://opensource.org/licenses/Apache-2.0",
    description="Tools to administer issuance and redemption of a Chia Asset Token or CAT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    extras_require=dict(
        dev=dev_dependencies,
    ),
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/cat-admin-tool",
        "Source": "https://github.com/Chia-Network/cat-admin-tool",
    },
)

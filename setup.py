#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "rt") as fh:
    long_description = fh.read()

dependencies = [
    "chik-blockchain==1.8.2.1",
]

dev_dependencies = [
    "black==21.12b0",
    "pytest",
    "pytest-env",
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
            "unwind_the_bag = cats.unwind_the_bag:main"
        ],
    },
    author_email="admin@chiknetwork.com",
    setup_requires=["setuptools_scm"],
    install_requires=dependencies,
    url="https://github.com/Chik-Network",
    license="https://opensource.org/licenses/Apache-2.0",
    description="Tools to administer issuance and redemption of a Chik Asset Token or CAT",
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
        "Bug Reports": "https://github.com/Chik-Network/cat-admin-tool",
        "Source": "https://github.com/Chik-Network/cat-admin-tool",
    },
)

#!/usr/bin/env python3

from setuptools import setup

with open("requirements.txt") as fp:
    install_requires = fp.read().strip().split("\n")

with open("requirements_dev.txt") as fp:
    dev_requires = fp.read().strip().split("\n")

setup(
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "docs": ["sphinx", "sphinx-rtd-theme"]
    }
)

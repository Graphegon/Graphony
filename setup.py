import os
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="graphony",
    version="0.0.1",
    description="Graphony",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Michel Pelletier",
    packages=["graphony"],
    install_requires=[
        "postgresql-wheel",
        "pygraphblas",
        "psycopg2-binary",
        "more-itertools",
        "graphviz",
        "Pillow",
        "matplotlib",
    ],
)

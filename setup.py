import os
from setuptools import setup

setup(
    name="graphony",
    version="0.0.1",
    description="Graphony",
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

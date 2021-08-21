from setuptools import setup
import os

setup(
    name="graphony",
    version="0.0.1",
    description="Graphony",
    author="Michel Pelletier",
    packages=["graphony"],
    setup_requires=["pygraphblas"],
    install_requires=["pygraphblas", "psycopg2-binary", "lazy-property"],
)

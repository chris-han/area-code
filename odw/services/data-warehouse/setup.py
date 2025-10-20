from setuptools import setup, find_packages
import os

requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
with open(requirements_path, "r") as f:
    requirements = []
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            requirements.append(line)

setup(
    name='data-warehouse',
    version='0.0',
    packages=find_packages(),
    install_requires=requirements,
)

from setuptools import setup, find_packages

setup(
    name="connectors",
    version="0.0",
    package_dir={"connectors": "src"},
    packages=["connectors"],
    python_requires=">=3.12",
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.25.0",
        "polars>=0.20.0",  # For data processing in future tasks
        "moose_lib",
    ],
)
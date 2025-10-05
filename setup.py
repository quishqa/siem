from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="siem",
    version="0.0.1",
    description="A package to build your emission files",
    author="Mario Gavidia-Calderón",
    author_email="mario.calderon@iag.usp.br",
    packages=find_packages(),
    setup_requires=["numpy"],
    install_requires=["numpy"],
    long_description=long_description,
)

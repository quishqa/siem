from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="siem",
    version="0.0.1",
    description="A package to build WRF-Chem and CMAQ emission files",
    author="Mario Gavidia-Calderón",
    author_email="mario.calderon@iag.usp.br",
    packages=find_packages(),
    setup_requires=["numpy"],
    install_requires=["numpy"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)

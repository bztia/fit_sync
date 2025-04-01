from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="fit_sync",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Synchronize fitness activities between different platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fit_sync",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'fit_sync=fit_sync.__main__:main',
        ],
    },
) 
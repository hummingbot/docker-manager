from setuptools import setup, find_packages

setup(
    name="docker-manager",
    version="0.1.0",
    description="This repository provides a set of functionalities for managing Docker containers in the context of the specified use case.",
    author="Federico Cardoso",
    author_email="federico.cardoso.e@gmail.com",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.8",
    install_requires=[
        # Add your dependencies here
    ],
    extras_require={
        "dev": [
            "pytest"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
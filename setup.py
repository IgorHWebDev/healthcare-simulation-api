from setuptools import setup, find_packages

setup(
    name="healthcare_framework",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-jose[cryptography]",
        "httpx",
        "pytest",
        "pytest-asyncio",
    ],
    python_requires=">=3.8",
) 
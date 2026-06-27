from setuptools import setup

setup(
    name="hector",
    version="2.1.0",
    description="HECTOR - Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval",
    author="HECTOR Team",
    py_modules=["main"],
    install_requires=[
        "chromadb>=0.4.0",
        "fastapi>=0.100.0",
        "pypdf>=3.17.0",
        "requests>=2.31.0",
        "sentence-transformers>=2.2.0",
        "typer>=0.12.0",
        "rich>=13.0.0",
        "uvicorn>=0.23.0",
    ],
    entry_points={
        "console_scripts": [
            "hector=main:main",
        ],
    },
    python_requires=">=3.9",
)

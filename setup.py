"""
Setup configuration for SofaScore data pipeline.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sofascore-pipeline",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A modular data pipeline for harvesting and processing SofaScore football data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sofascore-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.7.1",
        ],
        "ml": [
            "scikit-learn>=1.3.2",
            "tensorflow>=2.15.0",
        ],
        "viz": [
            "matplotlib>=3.8.2",
            "seaborn>=0.13.0",
            "plotly>=5.17.0",
        ],
        "api": [
            "fastapi>=0.104.1",
            "uvicorn>=0.24.0",
        ],
        "airflow": [
            "apache-airflow>=2.7.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "sofascore-scraper=src.main:main",
            "sofascore-setup=scripts.setup_database:main",
            "sofascore-quality-check=scripts.data_quality_check:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.yaml", "*.yml", "*.json"],
    },
)
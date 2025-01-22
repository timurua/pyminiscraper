from setuptools import setup, find_packages
import os

setup(
    name="pyminiscraper",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.2',
        'lxml>=4.9.3',
        'selenium>=4.11.2',
        'python-dotenv>=1.0.0',
        'urllib3>=2.0.4',
        'click>=8.1.8',
        'aiohttp>=3.11.11',
        'extruct>=0.18.0',
        'python-dateutil>=2.9.0',
        'aiolimiter>=1.2.1',
    ],
    author="Timur Valiulin",
    author_email="timurua@gmail.com",
    description="A mini web scraping utility package",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/timurua/pyminiscraper",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
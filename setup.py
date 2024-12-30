from setuptools import setup, find_packages

setup(
    name="pyminiscaper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.2',
        'lxml>=4.9.3',
        'selenium>=4.11.2',
        'python-dotenv>=1.0.0',
        'urllib3>=2.0.4',
        'pandas>=2.0.3',
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
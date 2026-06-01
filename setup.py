from setuptools import setup
import codecs
import os

VERSION = "0.0.27"
DESCRIPTION = "Getting indicators based on smart money concepts or ICT"

# read the contents of the README file
with codecs.open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

# Setting up
setup(
    name="smartmoneyconcepts",
    version=VERSION,
    author="Joshua Attridge",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=[
        "smartmoneyconcepts",
        "smartmoneyconcepts.dashboard",
        "smartmoneyconcepts.dashboard.db",
        "smartmoneyconcepts.dashboard.engine",
        "smartmoneyconcepts.dashboard.strategy",
        "smartmoneyconcepts.dashboard.execution",
        "smartmoneyconcepts.dashboard.api",
    ],
    install_requires=[
        "pandas>=2.0.2",
        "numpy>=1.24.3",
        "numba>=0.58.1",
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.29.0",
        "ccxt>=4.3.0",
        "pyyaml>=6.0",
        "aiosqlite>=0.20.0",
    ],
    keywords=[
        "smart",
        "money",
        "concepts",
        "ict",
        "indicators",
        "trading",
        "forex",
        "stocks",
        "crypto",
        "order",
        "blocks",
        "liquidity",
    ],
    url="https://github.com/joshyattridge/smartmoneyconcepts",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)

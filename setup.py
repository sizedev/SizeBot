import re
from pathlib import Path
import setuptools


def getLongDescription():
    with open("README.md", "r") as fh:
        longDescription = fh.read()
    return longDescription


def getRequirements():
    requirements = []
    with open("requirements.txt") as f:
        requirements = f.read().splitlines()
    return requirements


def getVersion():
    version = None
    path = Path(__file__).parent.resolve() / "sizebot" / "__init__.py"
    with open(path, "r") as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        version = version_match.group(1)
    if version is None:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="SizeBot",
    version=getVersion(),
    author="DigiDuncan",
    author_email="digiduncan@gmail.com",
    description="SizeBot3, Cogs Edition, rewritten.",
    long_description=getLongDescription(),
    long_description_content_type="text/markdown",
    url="https://github.com/sizedev/SizeBot3AndAHalf",
    python_requires=">=3.7",
    install_requires=getRequirements(),
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    entry_points={
        "console_scripts": [
            "sizebot=sizebot.main:main"
        ]
    }
)

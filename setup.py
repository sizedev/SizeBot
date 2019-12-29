import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="SizeBot",
    version="3.5.0",
    author="DigiDuncan",
    author_email="digiduncan@gmail.com",
    description="SizeBot3, Cogs Edition, rewritten.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sizedev/SizeBot3AndAHalf",
    python_requires=">=3.7",
    install_requires=requirements,
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

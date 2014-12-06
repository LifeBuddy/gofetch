"""Setup configuration file."""
from setuptools import setup


setup(
    name="gofetch",
    version="0.0.1",
    author="Jamie Bliss",
    author_email="astronouth7303@gmail.com",
    description="Tool to keep a git repo and working directory in sync.",
    keywords="git",
    url="https://github.com/LifeBuddy/gofetch",
    packages=['gofetch'],
    install_requires=['pyinotify'],
    # long_description=...,
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Version Control",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Utilities",
    ],
)

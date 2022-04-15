"""init module"""
from setuptools import setup
from mangadex_dl import __author__, __email__, __version__

LONG_DESC = open("README.md").read()

setup(
    name="mangadex_dl",
    version=__version__,
    description="Downloader and archiver for mangadex",
    long_description_content_type="text/markdown",
    long_description=LONG_DESC,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
    url="http://github.com/slapelachie/mangadex-dl",
    author=__author__,
    author_email=__email__,
    license="GPLv2",
    packages=["mangadex_dl"],
    entry_points={"console_scripts": ["mangadex-dl=mangadex_dl.__main__:main"]},
    install_requires=["Pillow>=9.1.0", "dict2xml", "requests"],
    zip_safe=False,
)

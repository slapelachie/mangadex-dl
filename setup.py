"""init module"""
from setuptools import setup

LONG_DESC = open("README.md").read()

setup(
    name="mangadex_dlz",
    version="1.0.0a0",
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
    url="http://github.com/slapelachie/mangadex-dlz",
    author="slapelachie",
    author_email="lslape@slapelachie.xyz",
    license="GPLv2",
    packages=["mangadex_dlz"],
    entry_points={"console_scripts": ["mangadex-dlz=mangadex_dlz.__main__:main"]},
    install_requires=["Pillow>=9.1.0", "dict2xml", "requests", "tqdm"],
    zip_safe=False,
)

from setuptools import setup

LONG_DESC = open("README.org").read()

setup(
    name="mangadex_dl",
    version="1.0.0a0",
    description="Downloader and archiver for mangadex",
    long_description_content_type="text/plain",
    long_description=LONG_DESC,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
    ],
    url="http://github.com/slapelachie/mangadex-dl",
    author="slapelachie",
    author_email="slapelachie@gmail.com",
    license="GPLv2",
    packages=["mangadex_dl"],
    entry_points={"console_scripts": ["mangadex-dl=mangadex_dl.__main__:main"]},
    install_requires=["Pillow>=9.1.0", "dict2xml"],
    zip_safe=False,
)

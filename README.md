# mangadex-dl

A command to download from MangaDex and archive it as a `CBZ` with an included `ComicInfo.xml` file

## Usage
To get the usage for this command, use `$ mangadex-dl --help`, the output matches the following:

```
usage: mangadex-dl [-h] [-v] [-o OUTPUT] url

Download mangadex manga from the command line

positional arguments:
  url                   url to download

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose logging
  -o OUTPUT, --output OUTPUT
                        output directory for volumes, defaults to ./mangadex-
                        dl

```

## Installation

``` sh
$ git clone https://github.com/slapelachie/mangadex-dl
$ cd mangadex-dl
$ pip install --user .
```

## TODO
- Add tests
- Verbose logging as a switch
- Refactor code

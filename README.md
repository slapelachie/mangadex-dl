# mangadex-dl

A command to download from MangaDex and archive it as a `CBZ` with an included `ComicInfo.xml` file

## Usage
To get the usage for this command, use `$ mangadex-dl --help`, the output matches the following:

```
usage: mangadex-dl [-h] [--version] [--progress] [--debug] [-v]
                   [-o OUT_DIRECTORY] [--cache-file CACHE_FILE] [--override]
                   [--download-cover] [--download-chapter-covers]
                   [url]

Download mangadex manga from the command line

positional arguments:
  url                   URL of series/chapter to download

options:
  -h, --help            show this help message and exit
  --version             Print version information
  --progress            Display progress bars for the download
  --debug               Debug Logging
  -v, --verbose         verbose logging
  -o OUT_DIRECTORY, --out-directory OUT_DIRECTORY
                        Output directory for series, defaults to ./mangadex-dl
  --cache-file CACHE_FILE
  --override            Ignores any UUIDs in the cache file
  --download-cover      Download the cover art
  --download-chapter-covers
                        Download only the covers for the chapters of the given
                        series/chapter
```

## Installation

``` sh
$ git clone https://github.com/slapelachie/mangadex-dl
$ cd mangadex-dl
$ pip install --user .
```

## TODO
- Implement tests
- Add tags for comicinfo
- Possibly rename to mangadex-dlz for clarity

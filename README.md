# OCR Converters

This repository contains a script to convert simple OCR data, in the form of a word list and page coordinates, into the format needed by the Internet Archive Bookreader.

To run this script, start by setting up a python virtual environment. Activate the environment, clone this repo, and install its dependencies:

```console
python3 -m venv venv
source venv/bin/activate
git clone https://github.com/uchicago-library/ocr_converters.git
cd ocr_converters
pip install -r requirements.txt
pip install -r requrements_dev.txt
```

Then, run the program like this:
```console
python build_ia_bookreader_ocr.py <identifier> <min-year> <max-year> [<shrink_to_height>]
```

<identifier> is the mvol identifier to produce OCR for, for example, mvol-0001-0002-0003. 
<min-year> is the earliest year for any item from this item's journal. (This is necessary because each item contains metadata for the entire title.)
<max-year> is the latest year for any item from this item's journal.
<shrink_to_height> is used for situations where the JPEG images used in the Internet Archive bookreader have been shrunken down to a smaller pixel height from the dimensions of the original master file. 

The script will output OCR for the Internet Archive Bookreader that is used in XTF sites like the Campus Publications.

## XTF File Layout

Get the XTF production and development server names from the systems administrators. XTF uses a data directory- cd into that directory, and cd into bookreader.
You'll find a sequence of directories, one for each digital object. Each will be named something like "mvol-0001-0002-0003"- this is the internal identifier the Preservation Department uses to track these files. 

Inside each directory is a sequence of JPEGs. Each has eight digits with leading zeroes, numbered like:
00000001.jpg
00000002.jpg
00000003.jpg
etc.

These are the page images for this item. To add a new item to XTF, use your favorite utility to convert TIFF files to JPEGs, optionally shrinking them to some smaller height. (If you shrink them you can use the <shrink_to_height> option on build_ia_bookreader_ocr.py above.)

Then, each directory contains a thumbnail image- <identifier>.jpg, which is 100px tall, e.g.:
mvol-0001-0002-0003.jpg

Each contains a PDF, with all page images:
mvol-0001-0002-0003.pdf

The OCR produced above is stored at:
mvol-0001-0002-0003.xml

And the text of the document itself, with no OCR information, lives in:
mvol-0001-0002-0003.txt

Because input data tends change with each deposit, I write ad-hoc scripts to get data into this format and scp it to the XTF servers. 

## Re-Indexing the Site

To re-index the site, look in the XTF bin directory. To rebuild the index completely, run:

```console
./textIndexer -clean -index default
```

Note that will probably take about a half hour, during which time the site will be unavailable. 


# AutoCrop
AutoCrop automatically crops scans of multiple images at once.

# Installation
AutoCrop requires Python 3 and ImageMagick 6 (7 is not supported). Set a MAGICK_HOME environment variable pointing to its installation directory.

## Linux, macOS
```
git clone https://github.com/alexhorn/AutoCrop.git
cd AutoCrop
pip install -r requirements.txt
```

## Windows
Windows users need to download Shapely from http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely.

```
git clone https://github.com/alexhorn/AutoCrop.git
cd AutoCrop
pip install Shapely-1.6.1-cp36-cp36m-win_amd64.whl # replace with path to downloaded file
pip install -r requirements.txt
```

# Example
```
python crop.py --input scan.jpg --output photo.jpg
```

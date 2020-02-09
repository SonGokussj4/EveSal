# EveSal
Small script to plot salary data with plotly extracted from pdf


## Warning...

> pdftotext library is used to extract pdf... \
> This is a problem fo Windows users. \
> If installing dependency won't work, see the readme footer.


## OS Dependencies

### Debian, Ubuntu, WSL, ...
```
sudo apt-get install build-essential libpoppler-cpp-dev pkg-config python-dev
```

### Fedora, RedHat, ...
```
sudo yum install gcc-c++ pkgconfig poppler-cpp-devel python-devel redhat-rpm-config
```

### Windows
```
See this beautiful blog post:
https://coder.haus/2019/09/27/installing-pdftotext-through-pip-on-windows-10/
```

## Installation
```
git clone <this repo>
python3 -m venv env
source env/bin/activate
python install -r requirements
```

## Usage
```
evesal /path/to/pdfs --convert
evesal /path/to/pdfs --plot

evesal --convert | --plot

    --convert ... Finds all 'VypListek*.pdf' files
                  Extract data to 'VyplListek*_res.txt'
                  Create data.db pickled object for later

    --plot    ... Grabs the pickled object database and plots it with Plotly
```
# galsynthspec
Galaxy Synthetic Spectrum fitting

[![PyPI version](https://badge.fury.io/py/galsynthspec.svg)](https://badge.fury.io/py/galsynthspec)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/robertdstein/galsynthspec/actions/workflows/continuous_integration.yml/badge.svg)](https://github.com/robertdstein/galsynthspec/actions/workflows/continuous_integration.yml)
[![Coverage Status](https://coveralls.io/repos/github/robertdstein/galsynthspec/badge.svg?branch=main)](https://coveralls.io/github/robertdstein/galsynthspec?branch=main)

Galsynthspec is a Python package for fitting synthetic galaxy spectra to observed data. It is designed to work with the `sfdmap` package for spectral fitting and provides tools for analyzing and visualizing the results.

It combines three key features:

1. Coordinate-based photometry retrieval using the [astroquery](https://github.com//astropy/astroquery) package, allowing users to fetch photometric data from various surveys.
2. Galaxy fitting using [prospector](https://github.com/bd-j/prospector).
3. Analysis and visualization tools for the fitted spectra.

If you are working with transient data, galsynthspec can also use TNS to resolve transient names to their respective 
coordinates, and identify a likely host using PS1.

**galsynthspec is a wrapper, which combines the functionality of several other packages in one easy-to-install place. If you use the package, please credit those packages as well, in particular:**
* [astroquery](https://github.com//astropy/astroquery)
* [dynesty](https://github.com/joshspeagle/dynesty)
* [FSPS](https://github.com/cconroy20/fsps)
* [prospector](https://github.com/bd-j/prospector)
* [sfdmap](https://github.com/AmpelAstro/sfdmap2)

## Installation

### Easy way (Docker):

Use Docker to run the package without needing to install it locally. This is the recommended way to use galsynthspec, as it ensures that all dependencies are correctly set up.

```bash
docker pull robertdstein/galsynthspec:latest
```

### Hard way (local installation):

#### Python Package

You can try the hard way:

```bash
git clone git@github.com:robertdstein/galsynthspec.git
cd galsynthspec
pip install -e ".[dev]"
pre-commit install
```

#### SFDMap and FSPS

galsynthspec also uses the sfdmap package for extinction corrections. While the package will be installed when using pip, it requires additional data files to function properly. 
Find a directory to store the SFDMAP data files, and then run:

```bash
wget https://github.com/kbarbary/sfddata/archive/master.tar.gz
tar xzf master.tar.gz
```

You also need to install https://github.com/cconroy20/fsps

## Usage

### Using Docker

If you want to use galsynthspec without installing it locally, you can run it in a Docker container.
After you've pulled the Docker image, you need the prefix:

```bash
docker run -v /my/local/dir:/mydata robertdstein/galsynthspec
```

This command mounts a local directory (`/my/local/dir`) to a directory inside the Docker container (`/mydata`), allowing you to access your data files from within the container.

### Using a local installation

If you prefer to install galsynthspec locally, you can do so by cloning the repository and installing the package in editable mode.
You should copy the .env.example file to .env and set the `SFD_DATA_DIR` variable to the directory where you want to store the data files.
You should also set the `FSPS_DIR` variable to the directory where you have installed fsps.
Finally, be sure to set the `GALSYNTHSPEC_DATA_DIR` variable to the directory where you want to store the galsynthspec data files.

## Running galsynthspec

You can use the package to fetch photometric data for a galaxy by its transient name or coordinates, fit a synthetic spectrum to the data, and analyze the results.

For example, to fetch photometric data for a galaxy by its transient name, you can use the following command:

```bash
docker run -v /my/local/dir:/mydata robertdstein/galsynthspec by-name AT2019fdr
```

for Docker, or

```bash
galsynthspec by-name AT2019fdr
```
for local installation.

This will run the `by-name` command with the transient name `AT2019fdr`, 
which will resolve the name to its coordinates and fetch the photometric data.
It will then use the `prospector` package to perform population synthesis.
Finally, it will analyze the results and generate plots. 
It will generate an 'average' spectrum for the galaxy, with uncertainty. 
It will also generate tabulated predictions for photometry in various bands, 
which can be used for further analysis.
Finally, it will generate diagnostic plots to visualize the results of the fitting process.
All this can be viewed in the data directory, under `AT2019fdr/`.

##

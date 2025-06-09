# galsynthspec
 Galaxy Synthetic Spectrum fitting

Galsynthspec is a Python package for fitting synthetic galaxy spectra to observed data. It is designed to work with the `sfdmap` package for spectral fitting and provides tools for analyzing and visualizing the results.

It combines three key features:

1. Coordinate-based photometry retrieval using the `astroquery` package, allowing users to fetch photometric data from various surveys.
2. Galaxy fitting using prospector, enabling users to fit galaxy spectra with a variety of models.
3. Analysis and visualization tools for the fitted spectra.

If you are working with transient data, galsynthspec can also use TNS to resolve transient names to their respective 
coordinates, and identify a likely host using PS1.

## Installation

You can try the gard way:

```bash
git clone git@github.com:robertdstein/galsynthspec.git
cd galsynthspec
pip install -e ".[dev]"
pre-commit install
```

galsynthspec also uses the sfdmap package for extinction corrections. While the package will be installed when using pip, it requires additional data files to function properly. 
To set up the data files, run the following command:

Set the environment variable `SFD_DATA_DIR` to the directory where you want to store the data files, and then run:

```bash
wget https://github.com/kbarbary/sfddata/archive/master.tar.gz
tar xzf master.tar.gz
```

You also need to install https://github.com/cconroy20/fsps

You can try the easy way, with Docker:

docker pull robertdstein/galsynthspec:latest

Then, you can run the container with:

```bash
docker run -v /my/local/dir:/mydata robertdstein/galsynthspec by-name AT2019fdr
```

This will map `/my/local/dir` on your host machine to `/mydata` in the container, allowing you to access the data files from within the container.
It will also run the `by-name` command with the transient name `AT2019fdr`, which will resolve the name to its coordinates and fetch the photometric data.


##

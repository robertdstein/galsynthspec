"""
Module to actually run galaxy synthesis and spectral synthesis.
"""

import logging

import numpy as np
from prospect.fitting import fit_model, lnprobfn
from prospect.io import write_results as writer
from prospect.utils.obsutils import fix_obs

from galsynthspec.datamodels import Galaxy, Result
from galsynthspec.download import download_all_data
from galsynthspec.model import get_model, get_sps

logger = logging.getLogger(__name__)


def fit_galaxy(galaxy: Galaxy, use_cache: bool = True) -> Result:
    """
    Fit a galaxy model to the photometry data of a given galaxy.

    :param galaxy: Galaxy The galaxy object containing the photometry data.
    :param use_cache: Bool If True, use cached results if available.
    :return:
    """

    photometry_list = galaxy.get_photometry(use_cache=use_cache)

    filters = [p.filter for p in photometry_list]
    maggies = np.array([p.maggies for p in photometry_list])
    magerr = np.array([p.mag_err for p in photometry_list])

    obs = {
        "wavelength": None,
        "spectrum": None,
        "unc": None,
        "redshift": galaxy.redshift,
        "maggies": maggies,
        "maggies_unc": magerr * maggies / 1.086,
        "filters": filters,
    }

    obs = fix_obs(obs)

    model = get_model(redshift=galaxy.redshift)

    noise_model = (None, None)

    sps = get_sps()

    fitting_kwargs = {
        "nlive_init": 400,
        "nested_method": "rwalk",
        "nested_dlogz_init": 0.05,
        "nested_target_n_effective": 1000,
    }

    output = fit_model(
        obs,
        model,
        sps,
        optimize=False,
        dynesty=True,
        lnprobfn=lnprobfn,
        noise=noise_model,
        **fitting_kwargs,
    )
    result, duration = output["sampling"]

    galaxy.mcmc_cache_file.unlink(missing_ok=True)
    writer.write_hdf5(
        str(galaxy.mcmc_cache_file),
        {},
        model,
        obs,
        output["sampling"][0],
        None,
        sps=sps,
        tsample=output["sampling"][1],
        toptimize=0.0,
    )

    logger.info(
        f"Prospector run complete for {galaxy.source_name} in {duration:.1f} seconds"
    )

    return galaxy.load_results()


def get_galaxy_results(galaxy: Galaxy, use_cache: bool = True) -> Result:
    """
    Generate synthetic spectra for a given galaxy.

    :param galaxy: Galaxy The galaxy object to generate spectra for.
    :param use_cache: bool Whether to refit the model even if a cache file exists.
                        Defaults to False.
    :return: Result The result of the fitting process, including the model and observations.
    """
    hfile = galaxy.mcmc_cache_file

    if hfile.exists() and use_cache:
        logger.info(f"Cache file {hfile} already exists, skipping fitting.")
        return galaxy.load_results()

    fit_galaxy(galaxy, use_cache=use_cache)

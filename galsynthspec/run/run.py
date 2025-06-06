import logging

from galsynthspec.datamodels.galaxy import Galaxy
from galsynthspec.run.analyse import analyse_results
from galsynthspec.run.fit import get_galaxy_results


def run_on_galaxy(galaxy: Galaxy, use_cache: bool = True):
    """
    Run the galaxy synthetic spectra pipeline for a given galaxy.

    :param galaxy: Galaxy The galaxy object to run the pipeline on.
    :param use_cache: bool Whether to use cached results if available.
    :return:
    """

    res = get_galaxy_results(galaxy, use_cache=use_cache)
    analyse_results(galaxy, res)

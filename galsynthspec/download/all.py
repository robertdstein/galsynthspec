"""
Module to iteratively download photometry data for a given galaxy.
"""

from astropy.coordinates import SkyCoord

from galsynthspec.datamodels.photometry import Photometry
from galsynthspec.download.galex import download_galex_data
from galsynthspec.download.ps1 import download_ps1_data
from galsynthspec.download.sdss import download_sdss_data
from galsynthspec.download.twomass import download_twomass_data
from galsynthspec.download.wise import download_wise_data


def download_all_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading photometry data for a given galaxy.

    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: Radius of the search in arcseconds.
    :return: Returns a list of Photometry objects.
    """

    # Optical data
    all_filters = download_sdss_data(src_position, radius_arcsec)
    # Download PS1 if SDSS is not available
    if len(all_filters) == 0:
        all_filters = download_ps1_data(src_position, radius_arcsec)

    # UV data
    all_filters.extend(download_galex_data(src_position, radius_arcsec))
    # NIR data
    all_filters.extend(download_twomass_data(src_position, radius_arcsec))
    # MIR data
    all_filters.extend(download_wise_data(src_position, radius_arcsec))

    return all_filters

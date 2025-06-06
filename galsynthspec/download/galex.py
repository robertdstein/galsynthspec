"""
Module for GALEX data
"""

import logging

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Catalogs

from galsynthspec.datamodels.photometry import Photometry

GALEX_BANDS = ["FUV", "NUV"]
GALEX_MAG_COLS = [f"{x.lower()}_mag" for x in GALEX_BANDS]
GALEX_MAGERR_COLS = [f"{x.lower()}_magerr" for x in GALEX_BANDS]

logger = logging.getLogger(__name__)


def download_galex_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading PS1 data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    catalog_data = Catalogs.query_region(
        src_position, radius=radius_arcsec * u.arcsec, catalog="Galex"
    )

    if len(catalog_data) == 0:
        logger.info("No Galex data found")
        return all_filters

    match = catalog_data.group_by("distance_arcmin")[0]

    for i, b in enumerate(GALEX_BANDS):
        mag_col = GALEX_MAG_COLS[i]
        magerr_col = GALEX_MAGERR_COLS[i]

        mag = match[mag_col]
        magerr = match[magerr_col]

        if not np.ma.is_masked(mag):

            entry = Photometry.from_position(
                src_position=src_position,
                filter_name=f"galex_{b}",
                observed_mag=mag,
                mag_err=magerr,
            )
            all_filters.append(entry)

    logger.info(f"GALEX data found with {len(all_filters)} filters")

    return all_filters

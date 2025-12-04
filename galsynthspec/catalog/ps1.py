"""
Module for PS1 data
"""

import logging

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Catalogs

from galsynthspec.datamodels.photometry import Photometry

PS1_BANDS = ["g", "r", "i", "z"]
PS1_MAG_COLS = [f"{b}MeanKronMag" for b in PS1_BANDS]
PS1_MAGERR_COLS = [f"{b}MeanKronMagStd" for b in PS1_BANDS]

logger = logging.getLogger(__name__)


def download_ps1_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading PS1 data for a given galaxy.

    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    catalog_data = Catalogs.query_region(  # pylint: disable=no-member
        src_position,
        radius=radius_arcsec * u.arcsec,  # pylint: disable=no-member
        catalog="Panstarrs",
    )

    if len(catalog_data) == 0:
        logger.info("No Panstarrs data found")
        return all_filters

    match = catalog_data.group_by("distance")[0]

    for i, b in enumerate(PS1_BANDS):
        mag_col = PS1_MAG_COLS[i]
        magerr_col = PS1_MAGERR_COLS[i]

        mag = match[mag_col]
        mag_err = match[magerr_col]

        filter_name = f"ps1::{b}" if b in ["y"] else f"sdss_{b}0"

        entry = Photometry.from_position(
            src_position=src_position,
            filter_name=filter_name,
            observed_mag=mag,
            mag_err=mag_err,
        )
        all_filters.append(entry)

    logger.info(f"PS1 data found with {len(all_filters)} filters")

    return all_filters

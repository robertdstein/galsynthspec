"""
Module for WISE data
"""

import logging

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.ipac.irsa import Irsa

from galsynthspec.datamodels.photometry import Photometry

logger = logging.getLogger(__name__)

# WISE values from
# https://wise2.ipac.caltech.edu/docs/release/allsky/expsup/sec4_4h.html
zeromag_wise = {
    "w1": 309.5 * u.Jansky,  # pylint: disable=no-member
    "w2": 171.8 * u.Jansky,  # pylint: disable=no-member
    "w3": 31.7 * u.Jansky,  # pylint: disable=no-member
    "w4": 8.4 * u.Jansky,  # pylint: disable=no-member
}
offsets_wise = {key: zm.to("mag(AB)").value for key, zm in zeromag_wise.items()}


def download_wise_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading WISE data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    allwise = Irsa.query_region(
        src_position,
        catalog="allwise_p3as_psd",
        radius=radius_arcsec * u.arcsec,  # pylint: disable=no-member
    )

    if len(allwise) == 0:
        logger.info("No WISE data found")
        return all_filters

    match = allwise[0]

    for band in zeromag_wise:
        mag_raw = match[f"{band}mpro"]
        offset = offsets_wise[band]
        mag = mag_raw + offset
        mag_err = match[f"{band}sigmpro"]

        if np.ma.is_masked(match[f"{band}sigmpro"]):
            mag_err = mag
            mag = np.nan

        entry = Photometry.from_position(
            src_position=src_position,
            filter_name=f"wise_{band}",
            observed_mag=mag,
            mag_err=mag_err,
            vega_mag=mag_raw,
        )
        all_filters.append(entry)

    logger.info(f"WISE data found with {len(all_filters)} filters")

    return all_filters

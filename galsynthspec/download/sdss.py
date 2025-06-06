"""
Module for SDSS data
"""

import logging

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.sdss import SDSS

from galsynthspec.datamodels.photometry import Photometry

SDSS_BANDS = ["u", "g", "r", "i", "z"]
SDSS_MAG_COLS = [f"cModelMag_{b}" for b in SDSS_BANDS]
SDSS_MAGERR_COLS = [f"cModelMagErr_{b}" for b in SDSS_BANDS]

logger = logging.getLogger(__name__)


def download_sdss_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading SDSS data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    cat = SDSS.query_crossid(
        src_position,
        radius=radius_arcsec * u.arcsec,  # pylint: disable=no-member
        photoobj_fields=["ra", "dec"] + SDSS_MAG_COLS + SDSS_MAGERR_COLS,
    )

    if cat is None:
        logger.info("No SDSS data found")
        return all_filters

    for i, b in enumerate(SDSS_BANDS):
        mag_col = SDSS_MAG_COLS[i]
        magerr_col = SDSS_MAGERR_COLS[i]

        mag = cat[0][mag_col]
        magerr = cat[0][magerr_col]

        # magerr = np.array([cat[0][magerr_col]])
        # magerr = np.hypot(magerr, 0.05)

        entry = Photometry.from_position(
            src_position=src_position,
            filter_name=f"sdss_{b}0",
            observed_mag=mag,
            mag_err=magerr[0],
        )
        all_filters.append(entry)

    logger.info(f"SDSS data found with {len(all_filters)} filters")

    return all_filters

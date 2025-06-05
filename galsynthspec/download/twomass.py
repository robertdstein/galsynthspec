"""
Module for 2MASS data
"""

import logging

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.gaia import Gaia
from astroquery.irsa import Irsa

from galsynthspec.datamodels.photometry import Photometry

# Silence astroquery verbiage
logging.getLogger("astroquery").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 2MASS values from https://iopscience.iop.org/article/10.1086/376474
zeromag_2mass = {"J": 1594.0 * u.Jansky, "H": 1024.0 * u.Jansky, "Ks": 666.8 * u.Jansky}
offsets_2mass = {key: zm.to("mag(AB)").value for key, zm in zeromag_2mass.items()}


def download_twomass_extended(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading 2MASS extended data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    extended_matches = Irsa.query_region(
        src_position,
        catalog="ext_src_cat",
        radius=radius_arcsec * u.arcsec,  # pylint: disable=no-member
    )

    if len(extended_matches) == 0:
        logger.info("No 2MASS extended data found")
        return all_filters

    match = extended_matches[0]

    for band in zeromag_2mass.keys():
        mag_raw = match[f"{band.lower()[0]}_m_k20fe"]
        offset = offsets_2mass[band]
        # Convert from Vega to AB mag
        mag = mag_raw + offset
        magerr = match[f"{band.lower()[0]}_msig_k20fe"]

        # if np.ma.is_masked(mag_raw):
        #     flux = 0.0
        #     magerr = mag[0]
        #
        # else:
        #     flux = 10. ** (-0.4 * mag)
        #     magerr = np.array([match[f"{band.lower()[0]}_msig_k20fe"]])
        #     magerr = np.hypot(magerr, 0.4)[0]

        entry = Photometry(
            filter_name=f"twomass_{band}", mag=mag, mag_err=magerr, vega_mag=mag_raw
        )
        all_filters.append(entry)

    logger.info(f"2MASS extended data found with {len(all_filters)} filters")

    return all_filters


def download_twomass_ps(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading 2MASS data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = []

    cmd = (
        f"SELECT * FROM gaiadr3.gaia_source AS g "
        f"JOIN gaiadr3.tmass_psc_xsc_best_neighbour AS xmatch USING (source_id) "
        f"JOIN gaiadr3.tmass_psc_xsc_join AS xjoin "
        f"  ON xmatch.original_ext_source_id = xjoin.original_psc_source_id "
        f"JOIN gaiadr1.tmass_original_valid AS tmass "
        f"  ON xjoin.original_psc_source_id = tmass.designation "
        f"WHERE CONTAINS(POINT('ICRS', g.ra, g.dec), "
        f"CIRCLE('ICRS', {src_position.ra.deg:.4f}, {src_position.dec.deg:.4f}, "
        f"{radius_arcsec / 3600.:.4f}))=1 "
        f"AND xmatch.number_of_mates=0 "
        f"AND xmatch.number_of_neighbours=1"
        f";"
    )

    job = Gaia.launch_job_async(cmd, dump_to_file=False)

    src_list = job.get_results()

    if len(src_list) == 0:
        logger.info("No 2MASS data found")
        return all_filters

    for band in zeromag_2mass.keys():
        mag_raw = src_list[f"{band.lower()}_m"][0]
        offset = offsets_2mass[band]
        # Convert from Vega to AB mag
        mag = mag_raw + offset

        mag_err = src_list[f"{band.lower()}_msigcom"][0]

        # if np.ma.is_masked(mag_raw):
        #     flux = 0.0
        #     magerr = mag
        #
        # else:
        #     flux = 10.**(-0.4 * mag)
        #     magerr = np.array([src_list[f"{band.lower()}_msigcom"][0]])
        #     magerr = np.hypot(magerr, 0.05)

        entry = Photometry(
            filter_name=f"twomass_{band}",
            mag=mag,
            mag_err=mag_err,
            vega_mag=mag_raw,
            systematic_error=0.2,
        )
        all_filters.append(entry)

    logger.info(f"2MASS data found with {len(all_filters)} filters")

    return all_filters


def download_twomass_data(
    src_position: SkyCoord,
    radius_arcsec: float,
) -> list[Photometry]:
    """
    Module for downloading 2MASS data for a given galaxy.

    Parameters
    :param src_position: SkyCoord The position of the source in the sky.
    :param radius_arcsec: float The radius of the search in arcseconds.

    Returns
    :return: list[Photometry] The photometry data for the source.
    """

    all_filters = download_twomass_extended(src_position, radius_arcsec)

    if len(all_filters) == 0:
        all_filters = download_twomass_ps(src_position, radius_arcsec)

    return all_filters

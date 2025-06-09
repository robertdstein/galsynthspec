"""
Module for querying astronomical sources by name
"""

import logging

import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Catalogs
from requests.exceptions import HTTPError

from galsynthspec.datamodels.galaxy import Galaxy
from galsynthspec.skyportal import client, query_skyportal_by_name
from galsynthspec.utils.tns import get_tns_by_name

logger = logging.getLogger(__name__)


def load_source_info(name: str, use_cache: bool = True) -> pd.Series:
    """
    Load source information from SkyPortal by name.

    :param name: The name of the astronomical source.
    :param use_cache: If True, use cached data if available.
    :return: A dictionary containing the source information.
    """
    if client.has_skyportal_token():
        if client.ping():
            try:
                return query_skyportal_by_name(name)
            except HTTPError as e:
                logger.debug(f"Error querying SkyPortal for {name}: {e}")
                logger.debug("Falling back to TNS query.")

    return get_tns_by_name(name, use_cache=use_cache)


def query_by_name(name: str, use_cache: bool = True) -> Galaxy:
    """
    Query the SkyPortal API for a source by ZTF or AT name.
    Create a Galaxy object centered on the nearest Panstarrs match.

    :param name: AT/SN/TDE or ZTF/ATLAS/Gaia etc name of the source.
    :param use_cache: If True, use cached data if available.
    :return: Galaxy object based on nearest Panstarrs host.
    """

    data = load_source_info(name, use_cache=use_cache)

    src_ra, src_dec = data["ra"], data["dec"]

    redshift = data["redshift"] if "redshift" in data else None

    src_position = SkyCoord(src_ra, src_dec, unit="deg")

    catalog_data = Catalogs.query_region(  # pylint: disable=no-member
        src_position,
        radius=10.0 * u.arcsec,  # pylint: disable=no-member
        catalog="Panstarrs",
    )

    if len(catalog_data) > 1:
        logger.warning(
            f"Multiple Panstarrs matches found for {name}. Will use the nearest one."
        )

    match = catalog_data.group_by("distance")[0]

    gal_ra, gal_dec = match["raMean"], match["decMean"]

    return Galaxy(source_name=name, ra_deg=gal_ra, dec_deg=gal_dec, redshift=redshift)

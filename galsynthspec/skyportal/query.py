"""
Module for querying the SkyPortal API for source information.
"""

import logging

import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Catalogs

from galsynthspec.datamodels import Galaxy
from galsynthspec.skyportal.base_client import client

logger = logging.getLogger(__name__)


def strip_tns_name(name: str) -> str:
    """
    Strip the TNS prefix from a name.

    :param name: The TNS name.
    :return: The stripped name.
    """
    is_digit = [x.isdigit() for x in name]
    idx = is_digit.index(True)
    tns_root = name[idx:].strip()
    return tns_root


def query_skyportal_by_name(name: str) -> pd.Series:
    """
    Query the SkyPortal API for a source by ZTF or AT name.

    :param name: AT/SN/TDE or ZTF name of the source.
    :return: Pandas Series with source data.
    """

    if not "ZTF" in name[:3]:
        # Must be TNS name, try to strip it
        name = strip_tns_name(name)

    res = client.api("GET", f"sources/{name}")
    res.raise_for_status()

    data = res.json()["data"]

    return pd.Series(data)

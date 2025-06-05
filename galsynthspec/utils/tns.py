"""
Utilities for accessing the Transient Name Server (TNS) API.
"""

import logging
from io import StringIO

import pandas as pd
import requests
from astropy import units as u
from astropy.coordinates import SkyCoord

from galsynthspec.paths import get_output_dir

logger = logging.getLogger(__name__)

# Some TNS bug prevents API queries that do not come from internet browsers
TNS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}
BASE_TNS_URL = "https://www.wis-tns.org/search?"

TNS_CACHE_NAME = "tns_info.json"


def query_tns_by_name(
    source_name: str, internal_name_bool: bool = False
) -> pd.DataFrame:
    """
    Query the Transient Name Server (TNS) by name.

    :param source_name: Name of the transient to search for.
    :param internal_name_bool: Boolean to indicate if the name is an internal survey name.
    :return: A pandas DataFrame containing the search results.
    """

    query_arg = "internal_name=" if internal_name_bool else "name="

    search_url = (
        f"{BASE_TNS_URL}{query_arg}{source_name}&include_frb=0&format=csv&page=0"
    )
    response = requests.get(search_url, headers=TNS_HEADERS)
    csv_data = StringIO(response.text)
    return pd.read_csv(csv_data)


def download_tns(source_name: str) -> pd.Series:
    """
    Download the TNS data for a given name.

    :param source_name: The name of the transient as listed in TNS.
    :return: The first row of the TNS search results as a pandas Series.
    """
    # Query TNS by name e.g "AT2020mni"
    df = query_tns_by_name(source_name)

    # If no results found, try querying by internal name e.g "ZTF20abkavqj"
    if len(df) == 0:
        df = query_tns_by_name(source_name, internal_name_bool=True)

    # If still no results, raise an error
    if len(df) == 0:
        logger.error(f"No TNS data found for {source_name}.")
        raise ValueError(f"No TNS data found for {source_name}.")

    res = df.iloc[0].copy()

    # Add coordinates in degrees
    c = SkyCoord(res["RA"], res["DEC"], unit=(u.hourangle, u.deg))
    res["ra"], res["dec"] = c.ra.deg, c.dec.deg

    return res


def get_tns_by_name(tns_name: str, use_cache: bool = True) -> pd.Series:
    """
    Get information about a transient from TNS.

    :param tns_name: The name of the transient as listed in TNS.
    :param use_cache: If True, use cached TNS data if available.
    :return: A dictionary containing the TNS data for the transient.
    """
    output_dir = get_output_dir(tns_name)
    tns_file = output_dir / TNS_CACHE_NAME

    if use_cache & tns_file.exists():
        logger.info(f"Loading cached TNS data for {tns_name}")
        res = pd.read_json(tns_file, typ="series")
    else:
        logger.info(f"Downloading TNS data for {tns_name}")
        res = download_tns(tns_name)
        logger.info(f"Saving TNS data to {tns_file}")
        res.to_json(tns_file)

    return res

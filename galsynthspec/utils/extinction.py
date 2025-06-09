"""
Module for calculating extinction from the
Schlegel, Finkbeiner, and Davis (1998) dust maps.
"""

import logging

import extinction
import numpy as np
import sfdmap
from astropy.coordinates import SkyCoord
from sedpy.observate import load_filters

from galsynthspec.paths import sfd_path

logger = logging.getLogger(__name__)

m = sfdmap.SFDMap(sfd_path.as_posix())


def get_extinction_correction(
    ra_deg: float, dec_deg: float, wavelengths_angstroms: list[float]
) -> list[float]:
    """
    Apply extinction correction

    See ... citation
    """
    coordinates = SkyCoord(ra_deg, dec_deg, frame="icrs", unit="degree")
    ebv = m.ebv(coordinates)
    wave = np.array(wavelengths_angstroms)

    return extinction.fitzpatrick99(  # pylint: disable=c-extension-no-member
        wave, 3.1 * ebv
    )


def get_extinction_for_filter(
    src_position: SkyCoord,
    filter_name: str,
) -> float:
    """
    Get the extinction correction for a given filter at the source position.

    :param src_position: SkyCoord The position of the source in the sky.
    :param filter_name: Name of the filter to get the extinction for.
    :return: Float The extinction correction value for the filter.
    """
    res = load_filters([filter_name])[0]

    mean = np.average(res.wavelength, weights=res.transmission)

    extinction_value = get_extinction_correction(
        ra_deg=src_position.ra.deg,
        dec_deg=src_position.dec.deg,
        wavelengths_angstroms=[mean],
    )[0]
    return extinction_value

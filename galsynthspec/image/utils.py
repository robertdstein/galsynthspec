"""
Utility functions for handling image files in the galsynthspec package.
"""

from typing import Tuple

from galsynthspec.image.constants import COADD_FILTERS, REF_PRIORITY
from galsynthspec.paths import data_dir


def fits_exists(name: str, survey: str) -> bool:
    """
    Check if any FITS files exist for a given target name and survey.

    :param name: Name of the target
    :param survey: Name of the survey
    :return: True if any FITS files exist, False otherwise
    """
    nested_dir = data_dir / name / survey

    # Any file for the survey (no filter restriction)
    if nested_dir.exists():
        for ext in [".fits", ".fits.gz", ".fits.fz"]:
            if len(list(nested_dir.rglob(f"*{ext}"))) > 0:
                return True

    return False


def get_ref_survey(name: str) -> Tuple[str, str]:
    """
    Get the reference survey and coadd filter for a given target name.

    :param name: Name of the target
    :return: Tuple of (reference survey name, coadd filter string)
    """
    for survey_name in REF_PRIORITY:
        if fits_exists(name, survey_name):
            return survey_name, COADD_FILTERS[survey_name]

    raise FileNotFoundError(f"No surveys found for {name}, checked {REF_PRIORITY}.")

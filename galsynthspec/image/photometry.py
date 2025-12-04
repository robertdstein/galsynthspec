"""
Module to perform host galaxy photometry using common masks and apertures
"""

# pylint: disable=wrong-import-position,wrong-import-order

import os

from galsynthspec.image.constants import SURVEYS_ALL, WISE_FILTERS, WISE_REF_FILT
from galsynthspec.paths import data_dir

os.environ["workdir"] = str(data_dir)  # Set workdir for hostphot, before importing

import logging

from hostphot.cutouts import download_images
from hostphot.photometry import global_photometry as gp
from hostphot.processing import coadd_images, masking
from hostphot.surveys_utils import (
    filters_file,
    get_survey_filters,
    load_yml,
)
from requests.exceptions import HTTPError

# Load filter configuration (for AB offsets etc.)
filters_config = load_yml(filters_file)

logger = logging.getLogger(__name__)

CORRECT_EXTINCTION = True


def download_all(name: str, host_ra: float, host_dec: float):
    """
    Download images from all supported surveys.

    :param name: Name of the target
    :param host_ra: Right Ascension of the host galaxy (in degrees)
    :param host_dec: Declination of the host galaxy (in degrees)
    :return: None
    """
    for survey_name in SURVEYS_ALL:
        try:
            download_images(
                name,
                host_ra,
                host_dec,
                survey=survey_name,
                overwrite=False,
                save_input=True,
            )
        except HTTPError as e:
            logger.error(f"Error downloading images for {survey_name}")
            logger.error(e)


def build_common_mask(
    name: str,
    host_ra: float,
    host_dec: float,
    ref_survey: str,
    ref_filter: str,
):
    """
    Create common mask from reference survey coadd and propagate to other surveys.

    :param name: Name of the target
    :param host_ra: Host RA
    :param host_dec: Host Dec
    :param ref_survey: Reference survey name
    :param ref_filter: Reference filter string
    :return:
    """
    # 1) Build the coadd for the reference survey
    # (creates images/{name}/{survey}/{survey}_{filters}.fits)
    coadd_images(name, filters=ref_filter, survey=ref_survey)  # writes coadd FITS

    # 2) Create mask on the coadd and save params
    masking.create_mask(
        name,
        host_ra,
        host_dec,
        filt=ref_filter,
        survey=ref_survey,
        threshold=12,
        sigma=6,
        r=4,
        save_plots=True,
        save_mask_params=True,
        save_input=True,
    )

    # 3) Propagate that mask to surveys except WISE
    apply_surveys = [x for x in SURVEYS_ALL if x not in ["WISE"]]
    for survey_name in apply_surveys:
        filters = get_survey_filters(survey_name)
        for filter_name in filters:
            try:
                masking.create_mask(
                    name,
                    host_ra,
                    host_dec,
                    filt=filter_name,
                    survey=survey_name,
                    ref_filt=ref_filter,
                    ref_survey=ref_survey,  # use common mask
                    save_plots=False,
                    save_mask_params=False,
                    save_input=False,
                )
            except FileNotFoundError as e:
                logger.warning(
                    f"Skipping mask propagation for {survey_name} {filter_name}: {e}"
                )


def fit_common_kron(
    name: str,
    host_ra: float,
    host_dec: float,
    ref_survey: str,
    ref_filter: str,
):
    """
    Fit global Kron on reference coadd and save aperture params.

    :param name: Name of the target
    :param host_ra: Host RA
    :param host_dec: Host Dec
    :param ref_survey: Reference survey name
    :param ref_filter: Reference filter string
    :return:
    """
    gp.extract_aperture(
        name,
        host_ra,
        host_dec,
        filt=ref_filter,
        survey=ref_survey,
        use_mask=True,
        optimize_kronrad=True,
        eps=0.001,
        gal_dist_thresh=-1,
        save_aperture_params=True,
        save_plots=True,
    )


def run_common_phot(
    name: str,
    host_ra: float,
    host_dec: float,
    ref_survey: str,
    ref_filter: str,
):
    """
    Do multi-band phot for GALEX, 2MASS, Legacy Survey,
    PanSTARRS, SDSS using common aperture.

    :param name: Name of the target
    :param host_ra: Host RA
    :param host_dec: Host Dec
    :param ref_survey: Reference survey name
    :param ref_filter: Reference filter string
    :return:
    """
    for survey_name in [x for x in SURVEYS_ALL if x not in ["WISE"]]:
        gp.multi_band_phot(
            name,
            host_ra,
            host_dec,
            filters=get_survey_filters(survey_name),
            survey=survey_name,
            use_mask=True,
            correct_extinction=CORRECT_EXTINCTION,
            common_aperture=True,
            ref_survey=ref_survey,
            ref_filt=ref_filter,
            save_plots=True,
            save_results=True,
            save_aperture_params=False,
            raise_exception=False,
        )


def run_wise_flow(
    name: str,
    host_ra: float,
    host_dec: float,
):
    """
    WISE-specific path: coadd all 4 bands → mask from coadd
    → Kron from W1 → phot on W1–W4.

    :param name: Name of the target
    :param host_ra: Host RA
    :param host_dec: Host Dec
    :return:
    """
    # 1) Coadd all 4 bands for WISE mask
    coadd_images(name, filters=WISE_FILTERS, survey="WISE")

    # 2) Create mask on WISE coadd (save params not needed when using ref_* below)
    masking.create_mask(
        name,
        host_ra,
        host_dec,
        filt=WISE_REF_FILT,
        survey="WISE",
        threshold=10,
        sigma=5,
        r=2,
        save_plots=True,
        save_mask_params=True,
        save_input=True,
    )

    for filter_name in get_survey_filters("WISE"):
        masking.create_mask(
            name,
            host_ra,
            host_dec,
            filt=filter_name,
            survey="WISE",
            ref_filt=WISE_REF_FILT,
            ref_survey="WISE",
            save_plots=False,
            save_mask_params=False,
            save_input=False,
        )

    # 3) Fit Kron using W1 with the mask
    gp.extract_aperture(
        name,
        host_ra,
        host_dec,
        filt=WISE_REF_FILT,
        survey="WISE",
        use_mask=True,
        optimize_kronrad=True,
        eps=0.001,
        gal_dist_thresh=5,
        save_aperture_params=True,
        save_plots=True,
    )

    # 4) Apply the W1 aperture to all four bands
    gp.multi_band_phot(
        name,
        host_ra,
        host_dec,
        survey="WISE",
        use_mask=True,
        correct_extinction=CORRECT_EXTINCTION,
        common_aperture=True,
        ref_survey="WISE",
        ref_filt=WISE_REF_FILT,
        save_plots=True,
        save_results=True,
        raise_exception=False,
    )

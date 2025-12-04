"""
Functions to run the full image download and photometry pipeline for a given galaxy
"""

import logging

import pandas as pd
from astropy.coordinates import SkyCoord

from galsynthspec.datamodels.photometry import Photometry
from galsynthspec.image.constants import sedpy_map
from galsynthspec.image.photometry import (
    build_common_mask,
    download_all,
    filters_config,
    fit_common_kron,
    get_survey_filters,
    run_common_phot,
    run_wise_flow,
)
from galsynthspec.image.utils import get_ref_survey
from galsynthspec.paths import get_output_dir, get_photometry_path

logger = logging.getLogger(__name__)


def batch_download_images(name: str, src_position: SkyCoord):
    """
    Run the full image download and photometry pipeline for a given galaxy.

    :param name: Name of the source
    :param src_position: SkyCoord The coordinates of the galaxy
    :return: None
    """

    logger.info(f"Downloading and processing images for {name}")

    # 0) Download what we can (skips on failure)
    download_all(name, src_position.ra.deg, src_position.dec.deg)

    # 1) Check what’s present and choose a reference survey for mask/aperture
    ref_survey, ref_filt = get_ref_survey(name)

    # 2) Build common mask from ref coadd and propagate to other surveys
    build_common_mask(
        name,
        src_position.ra.deg,
        src_position.dec.deg,
        ref_survey,
        ref_filt,
    )

    # 3) Fit common Kron from ref coadd and save aperture
    fit_common_kron(
        name,
        src_position.ra.deg,
        src_position.dec.deg,
        ref_survey,
        ref_filt,
    )

    # 4) Do common-aperture phot for GALEX, 2MASS, Legacy, PS1, SDSS
    run_common_phot(
        name,
        src_position.ra.deg,
        src_position.dec.deg,
        ref_survey,
        ref_filt,
    )

    # 5) WISE special path
    run_wise_flow(
        name,
        src_position.ra.deg,
        src_position.dec.deg,
    )


def batch_collate_photometry(name: str, src_position: SkyCoord):
    """
    Collate all photometry for a given galaxy.

    :param name: Name of the source
    :param src_position: SkyCoord The coordinates of the galaxy
    :return:
    """

    logger.info(f"Collating photometry for {name}")

    phot_files = list(get_output_dir(name).rglob("*/global_photometry.csv"))

    rows = []

    for file in phot_files:
        phot_df = pd.read_csv(file)
        survey = file.parts[-2]
        filters = get_survey_filters(survey)

        # Vega→AB offsets
        ab_offset = {
            filt: filters_config[survey][filt]["AB_offset"] for filt in filters
        }

        for filter_str in filters:
            filt_err_str = filter_str + "_err"

            if filter_str not in phot_df.columns:
                continue

            raw_mag = phot_df[filter_str].values[0]

            filter_name = sedpy_map[f"{survey.lower()}_{filter_str.lower()}"]

            if filter_name is not None:
                rows.append(
                    Photometry.from_position(
                        src_position=src_position,
                        filter_name=filter_name,
                        base_filter_name=filter_str,
                        raw_mag=raw_mag,
                        observed_mag=raw_mag + ab_offset[filter_str],
                        mag_err=phot_df[filt_err_str].values[0],
                        origin=survey,
                    )
                )

    sed_df = pd.DataFrame([p.model_dump() for p in rows])
    sed_df.to_json(get_photometry_path(name), orient="records")

    print(sed_df)

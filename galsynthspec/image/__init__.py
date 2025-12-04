import os

from galsynthspec.paths import data_dir, get_output_dir, get_photometry_path

os.environ["workdir"] = str(data_dir)  # Set workdir for hostphot
import logging
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
from hostphot.cutouts import download_images
from hostphot.photometry import global_photometry as gp
from hostphot.photometry import sed_plotting
from hostphot.processing import coadd_images, masking
from hostphot.surveys_utils import get_survey_filters

from galsynthspec.datamodels.photometry import Photometry

logger = logging.getLogger(__name__)

# --- Canonical survey names expected by HostPhot ---
SURVEYS_ALL = ["GALEX", "PanSTARRS", "SDSS", "2MASS", "WISE", "LegacySurvey"]

# Priority for reference mask/aperture
REF_PRIORITY = ["LegacySurvey", "PanSTARRS", "SDSS"]

# Coadd filter recipe per ref survey (string concat is supported)
COADD_FILTERS = {
    "LegacySurvey": "grz",
    "PanSTARRS": "griz",
    "SDSS": "griz",
}

CORRECT_EXTINCTION = True


# WISE coadd and ref choices
WISE_FILTERS = ["W1", "W2", "W3", "W4"]
WISE_COADD_STR = "".join(WISE_FILTERS)  # "W1W2W3W4"
WISE_REF_FILT = "W1"


def fits_exists(name: str, survey: str) -> bool:
    """
    Return True if any FITS file for this (survey[, filt]) exists under images/<name>/...
    Supports:
      - nested: images/<name>/<survey>/**/<whatever>.fits(.gz|.fz)
      - flat:   images/<name>/<survey>_*.fits(.gz|.fz)
    """
    nested_dir = data_dir / name / survey

    # Any file for the survey (no filter restriction)
    if nested_dir.exists():
        for ext in [".fits", ".fits.gz", ".fits.fz"]:
            if len([x for x in nested_dir.rglob(f"*{ext}")]) > 0:
                return True

    return False


def get_ref_survey(name: str) -> Tuple[str, str]:
    """
    Get the reference survey and coadd filter for a given target name.

    :param name: Name of the target
    :return: Tuple of (reference survey name, coadd filter string)
    """
    for s in REF_PRIORITY:
        if fits_exists(name, s):
            return s, COADD_FILTERS[s]

    raise FileNotFoundError(f"No surveys found for {name}, checked {REF_PRIORITY}.")


def download_all(name: str, host_ra: float, host_dec: float):
    """
    Download images from all supported surveys.

    :param name: Name of the target
    :param host_ra: Right Ascension of the host galaxy (in degrees)
    :param host_dec: Declination of the host galaxy (in degrees)
    :return: None
    """
    for survey_name in SURVEYS_ALL:
        download_images(
            name,
            host_ra,
            host_dec,
            survey=survey_name,
            overwrite=False,
            save_input=True,
        )


def build_common_mask(name, host_ra, host_dec, ra_sn, dec_sn, ref_survey, ref_filt):
    """Create mask on coadd for ref_survey, then propagate to the rest."""
    # 1) Build the coadd for the reference survey (creates images/{name}/{survey}/{survey}_{filters}.fits)
    coadd_images(name, filters=ref_filt, survey=ref_survey)  # writes coadd FITS
    # except Exception as e:
    #     print(f"[coadd] {name} {ref_survey} {ref_filt}: {e}")

    # 2) Create mask on the coadd and save params
    masking.create_mask(
        name,
        host_ra,
        host_dec,
        filt=ref_filt,
        survey=ref_survey,
        threshold=12,
        sigma=6,
        r=4,
        ra=ra_sn,
        dec=dec_sn,
        save_plots=True,
        save_mask_params=True,
        save_input=True,
    )

    # 3) Propagate that mask to GALEX, 2MASS, Legacy Survey, PanSTARRS, SDSS (all available filters)
    apply_surveys = ["GALEX", "2MASS", "LegacySurvey", "PanSTARRS", "SDSS"]
    for s in apply_surveys:
        filters = get_survey_filters(s)
        for f in filters:
            # # Only try to apply the mask if the target image exists
            # if not fits_exists(name, s, f):
            #     continue
            try:
                masking.create_mask(
                    name,
                    host_ra,
                    host_dec,
                    filt=f,
                    survey=s,
                    ref_filt=ref_filt,
                    ref_survey=ref_survey,  # use common mask
                    save_plots=False,
                    save_mask_params=False,
                    save_input=False,
                )
            except KeyboardInterrupt as e:
                print(f"[mask-apply] {name} {s}-{f}: {e}")


def fit_common_kron(name, host_ra, host_dec, ra_sn, dec_sn, ref_survey, ref_filt):
    """Fit global Kron on reference coadd and save aperture params."""
    gp.extract_aperture(
        name,
        host_ra,
        host_dec,
        filt=ref_filt,
        survey=ref_survey,
        ra=ra_sn,
        dec=dec_sn,
        use_mask=True,
        optimize_kronrad=True,
        eps=0.001,
        gal_dist_thresh=-1,
        save_aperture_params=True,
        save_plots=True,
    )


def run_common_phot(name, host_ra, host_dec, ra_sn, dec_sn, ref_survey, ref_filt):
    """Do multi-band phot for GALEX, 2MASS, Legacy Survey, PanSTARRS, SDSS using common aperture."""
    for s in ["GALEX", "2MASS", "LegacySurvey", "PanSTARRS", "SDSS"]:
        gp.multi_band_phot(
            name,
            host_ra,
            host_dec,
            filters=get_survey_filters(s),
            survey=s,
            ra=ra_sn,
            dec=dec_sn,
            use_mask=True,
            correct_extinction=CORRECT_EXTINCTION,
            common_aperture=True,
            ref_survey=ref_survey,
            ref_filt=ref_filt,
            save_plots=True,
            save_results=True,
            save_aperture_params=False,
            raise_exception=True,
        )


def run_wise_flow(name, host_ra, host_dec, ra_sn, dec_sn):
    """WISE-specific path: coadd all 4 bands → mask from coadd → Kron from W1 → phot on W1–W4."""
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
        ra=ra_sn,
        dec=dec_sn,
        save_plots=True,
        save_mask_params=True,
        save_input=True,
    )

    for filt in get_survey_filters("WISE"):
        masking.create_mask(
            name,
            host_ra,
            host_dec,
            filt=filt,
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
        ra=ra_sn,
        dec=dec_sn,
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
        ra=ra_sn,
        dec=dec_sn,
        use_mask=True,
        correct_extinction=CORRECT_EXTINCTION,
        common_aperture=True,
        ref_survey="WISE",
        ref_filt=WISE_REF_FILT,
        save_plots=True,
        save_results=True,
        raise_exception=False,
    )


from galsynthspec.datamodels.galaxy import Galaxy


def batch_download_images(galaxy: Galaxy, use_cache: bool = True):
    """
    Run the full image download and photometry pipeline for a given galaxy.

    :param galaxy: The galaxy object
    :param use_cache: Whether to use cached results if available
    :return: None
    """

    if use_cache & galaxy.photometry_cache_file.exists():
        logger.info(
            f"Photometry cache found for {galaxy.source_name}, "
            f"skipping image download and processing."
        )
        return

    name = galaxy.source_name

    logger.info(f"Downloading and processing images for {name}")

    # 0) Download what we can (skips on failure)
    download_all(name, galaxy.ra_deg, galaxy.dec_deg)

    # 1) Check what’s present and choose a reference survey for mask/aperture
    ref_survey, ref_filt = get_ref_survey(name)

    sn_ra, sn_dec = galaxy.ra_deg, galaxy.dec_deg

    # 2) Build common mask from ref coadd and propagate to other surveys
    build_common_mask(
        name, galaxy.ra_deg, galaxy.dec_deg, sn_ra, sn_dec, ref_survey, ref_filt
    )

    # 3) Fit common Kron from ref coadd and save aperture
    fit_common_kron(
        name, galaxy.ra_deg, galaxy.dec_deg, sn_ra, sn_dec, ref_survey, ref_filt
    )

    # 4) Do common-aperture phot for GALEX, 2MASS, Legacy, PS1, SDSS
    run_common_phot(
        name, galaxy.ra_deg, galaxy.dec_deg, sn_ra, sn_dec, ref_survey, ref_filt
    )

    # 5) WISE special path
    run_wise_flow(
        name,
        galaxy.ra_deg,
        galaxy.dec_deg,
        sn_ra,
        sn_dec,
    )

    plt.ioff()
    sed_plotting.plot_sed(name, z=galaxy.redshift)


import numpy as np


def get_eff_wave(filt: str, survey: str, version: str = None) -> float:
    """Effective wavelength of a filter in Angstroms."""
    wave, trans = extract_filter(filt, survey, version)
    return np.sum(wave * trans) / np.sum(trans)


import pandas as pd
from hostphot.surveys_utils import (
    extract_filter,
    filters_file,
    get_survey_filters,
    load_yml,
)

# Load filter configuration (for AB offsets etc.)
filters_config = load_yml(filters_file)

sedpy_map = {
    "sdss_u": "sdss_u0",
    "sdss_g": "sdss_g0",
    "sdss_r": "sdss_r0",
    "sdss_i": "sdss_i0",
    "sdss_z": "sdss_z0",
    "panstarrs_g": "sdss_g0",
    "panstarrs_r": "sdss_r0",
    "panstarrs_i": "sdss_i0",
    "panstarrs_z": "sdss_z0",
    "panstarrs_y": None,
    "2mass_j": "twomass_J",
    "2mass_h": "twomass_H",
    "2mass_ks": "twomass_Ks",
    "wise_w1": "wise_w1",
    "wise_w2": "wise_w2",
    "wise_w3": "wise_w3",
    "wise_w4": "wise_w4",
    "galex_fuv": "galex_FUV",
    "galex_nuv": "galex_NUV",
    "legacysurvey_g": "decam_g",
    "legacysurvey_r": "decam_r",
    "legacysurvey_z": "decam_z",
}


def batch_collate_photometry(galaxy: Galaxy):
    """
    Collate all photometry for a given galaxy.

    :param galaxy:
    :return:
    """

    name = galaxy.source_name

    source_position = galaxy.sky_coord

    logger.info(f"Collating photometry for {name}")

    """
    Build an SED table from hostphot photometry CSVs and save as CSV.
    """

    obj_path = get_output_dir(name)
    phot_files = list(obj_path.rglob(f"*/global_photometry.csv"))

    rows = []

    for file in phot_files:
        phot_df = pd.read_csv(file)
        survey = file.parts[-2]
        filters = get_survey_filters(survey)

        # Vega→AB offsets
        ab_offset = {
            filt: filters_config[survey][filt]["AB_offset"] for filt in filters
        }

        ext = ""

        for filt in filters:
            filt_str = filt + ext
            filt_err_str = filt + ext + "_err"
            if filt_str not in phot_df.columns:
                continue

            raw_mag = phot_df[filt_str].values[0]

            mag = raw_mag + ab_offset[filt]
            mag_err = phot_df[filt_err_str].values[0]

            filter_name = sedpy_map[f"{survey.lower()}_{filt.lower()}"]

            if filter_name is not None:
                rows.append(
                    Photometry.from_position(
                        src_position=source_position,
                        filter_name=filter_name,
                        observed_mag=mag,
                        mag_err=mag_err,
                        origin=survey,
                        raw_mag=raw_mag,
                        base_filter_name=filt,
                    )
                )

    sed_df = pd.DataFrame([p.model_dump() for p in rows])

    sed_df.to_json(get_photometry_path(name), orient="records")

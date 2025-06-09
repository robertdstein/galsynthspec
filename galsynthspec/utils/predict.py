"""
This module predicts the photometry for a galaxy
based on the results of a fitting procedure.
"""

import pandas as pd
from prospect.sources.constants import jansky_cgs, lightspeed
from scipy import stats
from sedpy.observate import getSED, load_filters

from galsynthspec.datamodels.fitresult import FitResult
from galsynthspec.datamodels.galaxy import Galaxy
from galsynthspec.utils.extinction import get_extinction_for_filter

DEFAULT_FILTER_LIST = [
    "galex_FUV",
    "galex_NUV",
    "uvot_w2",
    "uvot_m2",
    "uvot_w1",
    "sdss_u0",
    "sdss_g0",
    "sdss_r0",
    "sdss_i0",
    "sdss_z0",
    "twomass_J",
    "twomass_H",
    "twomass_Ks",
    "wise_w1",
    "wise_w2",
    "wise_w3",
    "wise_w4",
]


def get_lambda_cgs(x, angstroms):
    """
    Convert a wavelength in Angstroms to a wavelength in CGS units (cm).

    :param x: Flux in arbitrary units (e.g., erg/s/cm^2/Angstrom).
    :param angstroms: Array of wavelengths in Angstroms.
    :return: Flux in CGS units (erg/s/cm^2/nm).
    """
    return x * lightspeed / angstroms**2.0 * (3631 * jansky_cgs)


def get_lambda_quantile(df, q, angstroms):
    """
    Get the quantile of the wavelength in CGS units from a DataFrame.

    :param df: DataFrame containing the sampled SEDs.
    :param q: Quantile to compute (e.g., 0.5 for median).
    :param angstroms: Array of wavelengths in Angstroms.
    :return: Quantile flux in CGS units (erg/s/cm^2/nm).
    """
    return get_lambda_cgs(df.quantile(q).to_numpy(), angstroms)


def get_photometry_quantile(angstroms, df, q, filters: list[str]):
    """
    Get the photometry quantile for a given set of wavelengths and a DataFrame of SEDs.

    :param angstroms: Array of wavelengths in Angstroms.
    :param df: DataFrame containing the sampled SEDs.
    :param q: Quantile to compute (e.g., 0.5 for median).
    :param filters: List of filter names to compute the photometry for.
    :return: Magnitudes corresponding to the specified quantile for each filter.
    """
    filterlist = load_filters(filters)
    f_lambda_cgs = get_lambda_quantile(df, q, angstroms)
    mags = getSED(angstroms, f_lambda_cgs, filterlist=filterlist)
    return mags


def get_predicted_photometry(
    galaxy: Galaxy,
    result: FitResult,
    sample_df: pd.DataFrame | None = None,
    filter_list: None | list[str] = None,
) -> pd.DataFrame:
    """
    Function to get the predicted photometry for a galaxy based
    on the result of a fitting procedure.

    :param galaxy: Galaxy
    :param result: Result of the MCMC fitting procedure.
    :param sample_df: DataFrame containing the sampled SEDs from the posterior.
                        If None, it will sample 1000 SEDs.
    :param filter_list: List of filters to predict photometry for.
                        If None, it will use a default list of filters.
    :return: pd.DataFrame containing the predicted photometry.
    """

    if sample_df is None:
        sample_df = result.sample_sed_from_posterior(n_sample=1000)

    angstroms = result.rest_frame_wavelengths * (1.0 + result.get_redshift())

    if filter_list is None:
        filter_list = DEFAULT_FILTER_LIST

    photometry_dict = {x.filter_name: x for x in galaxy.get_photometry()}

    sigma = 1.0

    upper_percentile = stats.norm.cdf(sigma)
    lower_percentile = 1.0 - upper_percentile

    med = get_photometry_quantile(angstroms, sample_df, 0.5, filters=filter_list)
    up_pred = get_photometry_quantile(
        angstroms, sample_df, upper_percentile, filters=filter_list
    )
    lower_pred = get_photometry_quantile(
        angstroms, sample_df, lower_percentile, filters=filter_list
    )

    phot_df = pd.DataFrame(
        {
            "band": filter_list,
            "predicted_mag": med,
            "sigma+": med - up_pred,
            "sigma-": lower_pred - med,
            "measured_mag": [
                photometry_dict[x].observed_mag if x in photometry_dict else None
                for x in filter_list
            ],
            "measured_err": [
                photometry_dict[x].mag_err if x in photometry_dict else None
                for x in filter_list
            ],
            "extinction": [
                get_extinction_for_filter(galaxy.sky_coord, x) for x in filter_list
            ],
            "measured_mag_deextincted": [
                photometry_dict[x].mag if x in photometry_dict else None
                for x in filter_list
            ],
        }
    )
    phot_df["predicted_mag_extincted"] = (
        phot_df["predicted_mag"] + phot_df["extinction"]
    )

    print(phot_df)

    phot_df.to_json(galaxy.synthetic_photometry_file)
    return phot_df

"""
Plot the results of the fitting
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from galsynthspec.datamodels.fitresult import FitResult

logger = logging.getLogger(__name__)


def generate_sed_plot(
    res: FitResult,
    out_dir: Path,
) -> pd.DataFrame:
    """
    Function to generate a plot of the fitting results

    :param res: Result
    :param out_dir: Output path
    :return: SED DataFrame with the predicted SEDs
    """

    obs_wavelengths = res.rest_frame_wavelengths * (1 + res.get_redshift())

    df = res.sample_sed_from_posterior(n_sample=1000)

    plt.figure()
    ax = plt.subplot(111)

    # Plot Median
    plt.plot(obs_wavelengths, df.quantile(0.5), linestyle="-")

    sigmas = np.linspace(0.0, 3.0, 50)

    for sigma in sigmas:
        upper_percentile = stats.norm.cdf(sigma)
        lower_percentile = 1.0 - upper_percentile

        plt.fill_between(
            obs_wavelengths,
            df.quantile(upper_percentile),
            df.quantile(lower_percentile),
            alpha=1.0 / len(sigmas),
            color="C1",
        )

    pwave = np.array([f.wave_effective for f in res.predicted_photometry.filters])
    # plot the data

    maggies = res.predicted_photometry.maggies
    mask = maggies > 0.0

    ax.plot(pwave, maggies, linestyle="", marker="o", color="k")
    ax.errorbar(
        pwave,
        maggies,
        yerr=res.predicted_photometry.maggies_unc,
        linestyle="",
        color="k",
        zorder=10,
    )
    ax.set_ylabel(r"$f_\nu$ (maggies)")
    ax.set_xlabel(r"$\lambda$ (AA)")
    ax.set_xlim(1e3, 5e5)
    ax.set_ylim(maggies[mask].min() * 0.1, maggies[mask].max() * 5)
    ax.set_yscale("log")
    ax.set_xscale("log")

    out_path = out_dir / "sed_plot.pdf"
    logger.info(f"Saving SED plot to {out_path}")
    plt.savefig(out_path, bbox_inches="tight", dpi=300.0)
    plt.close()

    new = pd.DataFrame()
    new["wavelength"] = obs_wavelengths
    new["flux"] = df.quantile(0.5)
    new["sigma"] = 0.5 * (df.quantile(0.84) - df.quantile(0.16))
    sed_path = out_dir / "synthetic_sed.json"
    logger.info(f"Saving synthetic SED to {sed_path}")
    new.to_json(sed_path)

    return df

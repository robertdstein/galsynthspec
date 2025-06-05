"""
Create a corner plot of the chain
"""

import logging
from pathlib import Path

import matplotlib.pyplot as pl
import matplotlib.pyplot as plt
from prospect.plotting import corner

from galsynthspec.datamodels import Result

logger = logging.getLogger(__name__)


def plot_corner(res: Result, out_path: Path):
    """
    Plot the corner plot of the chain

    :param res: The result of the fitting
    :param out_path: The output of the sampling
    """
    nsamples, ndim = res.chain.shape
    cfig, axes = pl.subplots(ndim, ndim, figsize=(10, 9))
    axes = corner.allcorner(
        res.chain.T,
        res.fit_parameters,
        axes,
        weights=res.weights,
        color="royalblue",
        show_titles=True,
    )
    plt.savefig(out_path, bbox_inches="tight")
    plt.close(cfig)

    logger.info(f"Corner plot saved to {out_path}")

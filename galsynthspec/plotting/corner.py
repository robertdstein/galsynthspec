"""
Create a corner plot of the chain
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from prospect.plotting import corner

from galsynthspec.datamodels.fitresult import FitResult, weighted_quantiles

logger = logging.getLogger(__name__)


def plot_corner(res: FitResult, out_path: Path):
    """
    Plot the corner plot of the chain

    :param res: The result of the fitting
    :param out_path: The output of the sampling
    """
    _, ndim = res.chain.shape
    cfig, axes = plt.subplots(ndim, ndim, figsize=(10, 9))
    corner.allcorner(
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

    results = []
    for i, param in enumerate(res.fit_parameters):

        logify = param in ["mass"]

        vals = res.chain[:, i] if not logify else np.log10(res.chain[:, i])

        quantiles = weighted_quantiles(vals, res.weights, [0.16, 0.5, 0.84])
        results.append(
            {
                "parameter": param if not logify else f"log10({param})",
                "median": quantiles[1],
                "sigma-": quantiles[1] - quantiles[0],
                "sigma+": quantiles[2] - quantiles[1],
            }
        )

    df = pd.DataFrame(results)
    print(df)
    df.to_json(out_path.parent / "fit_results.json")

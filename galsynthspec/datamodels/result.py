"""
Base Model for source
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from numpydantic import NDArray, Shape
from prospect.io import read_results as reader
from prospect.models import SpecModel
from prospect.plotting.utils import sample_posterior
from prospect.sources import CSPSpecBasis
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sedpy.observate import Filter

from galsynthspec.model import get_model, get_sps

logger = logging.getLogger(__name__)


def weighted_quantiles(values, weights, quantiles=0.5):
    i = np.argsort(values)
    c = np.cumsum(weights[i])
    return values[i[np.searchsorted(c, np.array(quantiles) * c[-1])]]


class BestFit(BaseModel):
    """
    Base model for best fit parameters
    """

    parameter: NDArray[Shape["5-6 x"], float] = Field(description="Best fit parameters")
    photometry: NDArray[Shape["* x"], float] = Field(description="Best fit photometry")
    restframe_wavelengths: NDArray[Shape["* x"], float] = Field(
        description="Restframe wavelengths for the best fit"
    )
    spectrum: NDArray[Shape["* x"], float] = Field(description="Best fit spectrum")
    mfrac: float = Field()

    @model_validator(mode="after")
    def validate_length(self):
        """
        Validate the parameter shape
        """
        if not len(self.restframe_wavelengths) == len(self.spectrum):
            raise ValueError(
                "Restframe wavelengths and spectrum must have the same length"
            )
        return self


class PredictedPhotometry(BaseModel):
    """
    Base model for predicted photometry
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    maggies: NDArray[Shape["* x"], float] = Field(
        description="Predicted photometry in maggies"
    )
    maggies_unc: NDArray[Shape["* x"], float] = Field(
        description="Uncertainty in the predicted photometry in maggies"
    )
    phot_mask: NDArray[Shape["* x"], bool] = Field(
        description="Mask for the photometry"
    )
    filternames: list[str] = Field(
        description="Names of the filters used for the photometry"
    )
    filters: list[Filter] = Field(
        description="List of sedpy filters used for the photometry"
    )


class Result(BaseModel):
    """
    Base model for fitting result
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_path: Path = Field(description="Path to input file")
    fit_parameters: list[str] = Field(description="Names of fit parameters")
    chain: NDArray[Shape["* x, 5-6 y"], float] = Field(
        description="The chain of the fit"
    )
    weights: NDArray[Shape["* x"], float] = Field(description="The weights of the fit")
    redshift: float = Field(description="The redshift of the source")
    model: SpecModel = Field(description="The model used for fitting")
    obs: dict = Field(description="The observation data")
    sps: CSPSpecBasis = Field(description="The SPS model used for fitting")
    best_fit: BestFit = Field(description="The best fit model")
    predicted_photometry: PredictedPhotometry = Field(
        description="Predicted photometry from the model"
    )

    @classmethod
    def from_file(cls, file_path: Path):
        """
        Read the result from a file

        :param file_path: Path to the file
        :return: Result instance
        """
        out, out_obs, _ = reader.results_from(str(file_path))
        model = get_model(redshift=out["obs"]["redshift"])
        return cls(
            input_path=file_path,
            fit_parameters=out["theta_labels"],
            chain=out["chain"],
            weights=out["weights"],
            redshift=out["obs"]["redshift"],
            obs=out["obs"],
            model=model,
            sps=get_sps(),
            best_fit=BestFit(**out["bestfit"]),
            predicted_photometry=PredictedPhotometry(**out_obs),
        )

    @model_validator(mode="after")
    def validate_chain(self):
        """
        Validate the source name
        """
        assert self.chain.shape[1] == len(self.fit_parameters)
        return self

    def sample_from_posterior(self, n_sample: int = 1) -> np.ndarray:
        """
        Sample from the posterior

        :param n_sample: Number of samples to draw
        :return: The samples
        """
        return sample_posterior(self.chain, weights=self.weights, nsample=n_sample)

    def sample_sed_from_posterior(self, n_sample: int = 1) -> pd.DataFrame:
        """
        Sample the SED from the posterior

        :param n_sample: Number of samples to draw
        :return: The sampled SEDs
        """
        all_pred = []

        thetas = self.sample_from_posterior(n_sample=n_sample)
        logger.info(f"Generating {n_sample} predictions from the posterior samples")
        for theta in thetas:
            spec, _, _ = self.predict(theta)
            all_pred.append(spec)

        all_pred = np.array(all_pred)
        return pd.DataFrame(all_pred)

    def predict(self, theta, obs=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict the spectrum, photometry and mass fraction

        :param theta: Parameters to simulate
        :param obs: Set of photometric datapoints
        :return: Simulated spectrum, photometry and mass fraction
        """
        if obs is None:
            obs = self.obs

        spec, phot, mfrac = self.model.predict(theta, obs=obs, sps=self.sps)
        return spec, phot, mfrac

    @property
    def rest_frame_wavelengths(self) -> np.ndarray:
        """
        Get the restframe wavelengths for the best fit
        """
        return self.best_fit.restframe_wavelengths

    def get_redshift(self) -> float:
        """
        Get the redshift of the source

        :return: Redshift
        """
        redshift = self.redshift
        if redshift is None:
            idx = self.fit_parameters.index("zred")
            redshift = weighted_quantiles(
                self.chain[:, idx],
                self.weights,
                quantiles=0.5,
            )
            logger.info(f"Redshift is not known. Using median fit value: {redshift}")

        return redshift

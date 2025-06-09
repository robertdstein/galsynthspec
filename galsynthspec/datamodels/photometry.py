"""
Base Model for photometry data
"""

import numpy as np
from pydantic import BaseModel, Field, model_validator
from sedpy.observate import Filter, list_available_filters

from galsynthspec.utils.extinction import get_extinction_for_filter


class Photometry(BaseModel):
    """
    Base model for photometry data
    """

    filter_name: str = Field(description="Name of the filter")
    observed_mag: float = Field(description="AB Magnitude for the photometry")
    extinction: float = Field(description="Extinction factor for the photometry")
    vega_mag: float | None = Field(
        description="Vega Magnitude for the photometry", default=None
    )
    mag_err: float = Field(description="Error in the photometry")
    systematic_error: float = Field(
        description="Systematic error in the photometry", default=0.05
    )

    @property
    def mag(self) -> float:
        """
        Get the magnitude in AB system
        """
        return self.observed_mag - self.extinction

    @model_validator(mode="after")
    def validate_filter(self):
        """
        Validate the filter
        """
        if self.filter_name not in list_available_filters():
            raise ValueError(
                f"Filter {self.filter_name} not found. "
                f"Available filters are {list_available_filters()}"
            )

        return self

    @property
    def filter(self) -> Filter:
        """
        Get the filter object for the photometry
        """
        return Filter(self.filter_name)

    @property
    def maggies(self) -> float:
        """
        Convert the magnitude to maggies
        """
        return 10.0 ** (-0.4 * self.mag) if not np.isnan(self.observed_mag) else 0.0

    @property
    def mag_err_combined(self) -> float:
        """
        Get the systematic error in the magnitude
        """
        return np.hypot(self.mag_err, self.systematic_error)

    @classmethod
    def from_position(cls, src_position, filter_name: str, **kwargs) -> "Photometry":
        """
        Create a Photometry instance from source position and filter data
        """
        extinction = get_extinction_for_filter(
            src_position=src_position, filter_name=filter_name
        )
        return cls(filter_name=filter_name, extinction=extinction, **kwargs)

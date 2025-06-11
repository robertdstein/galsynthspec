"""
Base Model for source
"""

import logging
from pathlib import Path

import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from pydantic import BaseModel, Field, model_validator

from galsynthspec.datamodels.fitresult import FitResult
from galsynthspec.datamodels.photometry import Photometry
from galsynthspec.download import download_all_data
from galsynthspec.paths import get_output_dir

logger = logging.getLogger(__name__)


class Galaxy(BaseModel):
    """
    Base model for galaxy data
    """

    source_name: str | None = Field(description="Name of the source", default=None)
    ra_deg: float = Field(
        description="Right ascension of the source in degrees", ge=0.0, le=360.0
    )
    dec_deg: float = Field(
        description="Declination of the source in degrees", ge=-90.0, le=90.0
    )
    redshift: None | float = Field(description="Redshift of the source", ge=0.0)

    @model_validator(mode="after")
    def validate_source_name(self):
        """
        Validate the source name
        """
        if self.source_name is None:
            src_position = SkyCoord(self.ra_deg, self.dec_deg, unit="deg")
            ra_str = src_position.ra.to_string(
                unit=u.hour, sep="", precision=2, pad=True  # pylint: disable=no-member
            )
            dec_str = src_position.dec.to_string(
                unit=u.degree,  # pylint: disable=no-member
                sep="",
                precision=2,
                alwayssign=True,
                pad=True,
            )
            j_name = f"J{ra_str}{dec_str}"
            logger.info(f"Source name not provided. Using J2000 name {j_name}")
            self.source_name = j_name

        return self

    @property
    def base_output_dir(self) -> Path:
        """
        Get the base output directory for the source
        """
        return get_output_dir(source_name=self.source_name)

    @property
    def sky_coord(self) -> SkyCoord:
        """
        Get the sky coordinate for the source
        """
        return SkyCoord(self.ra_deg, self.dec_deg, unit="deg")

    @property
    def photometry_cache_file(self) -> Path:
        """
        Get the cache file for the photometry
        """
        return self.base_output_dir / "photometry.json"

    @property
    def mcmc_cache_file(self) -> Path:
        """
        Get the cache file for MCMC

        :return: Cache path
        """
        return self.base_output_dir / "quickstart_dynesty_mcmc_mod.h5"

    @property
    def synthetic_photometry_file(self) -> Path:
        """
        Get the synthetic photometry file

        :return: Synthetic photometry path
        """
        return self.base_output_dir / "synthetic_photometry.json"

    @property
    def corner_path(self) -> Path:
        """
        Get the cache file for MCMC

        :return: Cache path
        """
        return self.base_output_dir / "corner.pdf"

    def get_photometry(
        self, radius_arcsec: float = 3.0, use_cache: bool = True
    ) -> list[Photometry]:
        """
        Get the photometry data for the source

        :param radius_arcsec: float The radius of the search in arcseconds
        :param use_cache: bool If True, use the cached photometry data if available

        :return: list[Photometry] The photometry data
        """
        if self.photometry_cache_file.is_file() and use_cache:
            return self.load_photometry_from_cache()

        photometry = download_all_data(self.sky_coord, radius_arcsec=radius_arcsec)
        self.export_photometry_to_cache(photometry)

        return photometry

    def export_photometry_to_cache(self, photometry: list[Photometry]):
        """
        Export the photometry to a cache file

        :param photometry: list[Photometry] The photometry data

        :return: None
        """
        logger.info(f"Exporting photometry to {self.photometry_cache_file}")
        pd.DataFrame([p.model_dump() for p in photometry]).to_json(
            self.photometry_cache_file
        )

    def load_photometry_from_cache(self) -> list[Photometry]:
        """
        Load the photometry from the cache file

        :return: List of Photometry objects loaded from the cache file
        """
        logger.info(f"Loading photometry from cache file {self.photometry_cache_file}")
        df = pd.read_json(self.photometry_cache_file)
        return [Photometry.model_validate(p) for p in df.to_dict(orient="records")]

    def load_results(self) -> FitResult:
        """
        Load the results for the source

        :return: Result object containing the results
        """
        if not self.mcmc_cache_file.is_file():
            raise FileNotFoundError(
                f"MCMC cache file {self.mcmc_cache_file} does not exist."
            )

        logger.info(f"Loading results from {self.mcmc_cache_file}")
        return FitResult.from_file(self.mcmc_cache_file)

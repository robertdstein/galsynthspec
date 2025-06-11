"""
Module for testing galsynthspec
"""

import logging
import unittest
from pathlib import Path

import pandas as pd
from click.testing import CliRunner

from galsynthspec.cli.wrappers import cli
from galsynthspec.datamodels.galaxy import Galaxy

logger = logging.getLogger(__name__)

expected_df = pd.read_json(
    Path(__file__).parent / "test_data/synthetic_photometry.json"
)


class TestGalsynthspec(unittest.TestCase):
    """
    Class for testing Galsynthspec
    """

    def test_by_name(self):
        """
        Test ping

        :return: None
        """

        test_ra, test_dec = 314.262256, 14.204368
        redshift = 0.0512

        logger.info(f"Testing Galsynthspec for {test_ra}, {test_dec}")

        runner = CliRunner()
        runner.invoke(
            cli,
            ["by-ra-dec", str(test_ra), str(test_dec), "-z", str(redshift)],
            catch_exceptions=False,
        )

        # Check results

        logger.info("Checking results")

        gal = Galaxy(
            ra_deg=test_ra,
            dec_deg=test_dec,
            redshift=redshift,
        )
        assert gal.synthetic_photometry_file.exists()
        new = pd.read_json(gal.synthetic_photometry_file)

        pred_diff = (new["predicted_mag"] - expected_df["predicted_mag"]) / (
            0.5 * (expected_df["sigma+"] + expected_df["sigma-"])
        )

        max_diff = pred_diff.abs().max()
        logger.info(f"Max diff: {max_diff}")
        assert max_diff < 0.5, f"Difference too large: {pred_diff.abs().max()}"

        median_diff = pred_diff.median()
        logger.info(f"Median diff: {median_diff}")
        assert median_diff < 0.1, f"Median difference too large: {median_diff}"

        pd.testing.assert_series_equal(new["measured_mag"], expected_df["measured_mag"])
        pd.testing.assert_series_equal(
            new["extinction"], expected_df["extinction"], check_exact=False, atol=0.001
        )

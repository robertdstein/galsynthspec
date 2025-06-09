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
        result = runner.invoke(
            cli,
            ["by-ra-dec", str(test_ra), str(test_dec), "-z", str(redshift)],
            catch_exceptions=False,
        )
        if not result.exit_code == 0:
            logger.error("Command failed")
            logger.error(result.output)
            logger.error(result.stderr)
            logger.error(result.exception)
            logger.error(result.exit_code)
            logger.error(result.exc_info)
            raise RuntimeError("Command failed")

        # Check results

        logger.info("Checking results")

        gal = Galaxy(
            ra_deg=test_ra,
            dec_deg=test_dec,
            redshift=redshift,
        )
        assert gal.synthetic_photometry_file.exists()
        new = pd.read_json(gal.synthetic_photometry_file)
        pd.testing.assert_frame_equal(new, expected_df)

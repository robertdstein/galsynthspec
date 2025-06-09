"""
Module for testing galsynthspec
"""

import logging
import unittest
from pathlib import Path

import pandas as pd
from click.testing import CliRunner

from galsynthspec.cli.wrappers import cli
from galsynthspec.utils.query import query_by_name

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

        test_name = "ZTF19aapreis"

        logger.info(f"Testing Galsynthspec for {test_name}")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["by-name", test_name],
        )
        logger.info("Here")
        logger.info(result.output)
        logger.error(result.stderr)
        logger.error(result.exception)
        logger.error(result.exit_code)
        logger.error(result.exc_info)
        logger.info("Checking exit code")
        assert result.exit_code == 0

        # Check results

        logger.info(f"Checking results for {test_name}")

        gal = query_by_name(test_name)
        assert gal.synthetic_photometry_file.exists()
        new = pd.read_json(gal.synthetic_photometry_file)
        pd.testing.assert_frame_equal(new, expected_df)

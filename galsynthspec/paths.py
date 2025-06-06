"""
Module for defining paths to data files and directories.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

_data_dir = os.getenv("GALSPECSYNTH_DATA_DIR", None)


if _data_dir is None:
    data_dir = Path.home() / "Data/galspecsynth"
    logger.warning(
        f"Environment variable GALSPECSYNTH_DATA_DIR not set. "
        f"Using default data directory {data_dir}."
    )

else:
    data_dir = Path(_data_dir)
    logger.info(
        f"Using data directory {data_dir} set by environment variable GALSPECSYNTH_DATA_DIR."
    )

sfd_path = data_dir.joinpath("sfdmap/sfddata-master")


def get_output_dir(source_name: str) -> Path:
    """
    Get the output directory for a given galaxy name.

    :param source_name: Name of the galaxy
    :return: Path to the output directory
    """
    out_dir = data_dir / source_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

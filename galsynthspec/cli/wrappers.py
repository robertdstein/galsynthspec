"""
CLI wrapper for galaxy synthetic spectra
"""

import logging

import click

from galsynthspec.datamodels.galaxy import Galaxy
from galsynthspec.run import run_on_galaxy
from galsynthspec.utils.query import query_by_name

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """
    CLI for galaxy synthetic spectra.
    """
    pass


@cli.command("by-name")
@click.argument("name", type=str)
@click.option(
    "--use-cache/--no-cache", default=True, help="Enable using cached results"
)
def run_by_name(name, use_cache):
    """
    Run the galaxy synthetic spectra pipeline for a given galaxy name.
    """
    logger.info(f"Running pipeline for source name {name}")
    gal = query_by_name(name)
    run_on_galaxy(gal, use_cache=use_cache)


@cli.command("by-ra-dec")
@click.argument("ra_deg", type=float)
@click.argument("dec_deg", type=float)
@click.argument("name", type=str, default=None)
@click.argument("redshift", type=float, default=None)
def run_by_ra_dec(ra_deg: float, dec_deg: float, name=None, redshift=None):
    """
    Run the galaxy synthetic spectra pipeline for a given galaxy name.
    """
    logger.info(f"Running pipeline for position {ra_deg} {dec_deg}")

    gal = Galaxy(source_name=name, ra_deg=ra_deg, dec_deg=dec_deg, redshift=redshift)

    run_on_galaxy(gal)

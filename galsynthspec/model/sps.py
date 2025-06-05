"""
Model
"""

from prospect.sources import CSPSpecBasis


def get_sps() -> CSPSpecBasis:
    """
    Get the stellar population synthesis model

    :return: Stellar population synthesis model
    """

    return CSPSpecBasis(zcontinuous=1)

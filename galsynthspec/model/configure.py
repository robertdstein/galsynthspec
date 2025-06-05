"""
Module for generating base prospector model
"""

from prospect.models import SpecModel
from prospect.models.priors import LogUniform, Uniform
from prospect.models.templates import TemplateLibrary


def get_model(redshift: float | None = None) -> SpecModel:
    """
    Get the base prospector model

    :param redshift: Will fix the redshift if provided
    :return: SpecModel
    """

    model_params = TemplateLibrary["parametric_sfh"]
    model_params.update(TemplateLibrary["nebular"])

    if redshift is not None:
        # Fix redshift
        model_params["zred"]["init"] = redshift
    else:
        # Change redshift to free parameter
        model_params["zred"]["isfree"] = True
        model_params["zred"]["prior"] = LogUniform(mini=0.0, maxi=4.0)

    model_params["tage"]["prior"] = Uniform(mini=0.1, maxi=10.1)
    model_params["tau"]["prior"] = Uniform(mini=0.1, maxi=10.0)
    model_params["logzsol"]["prior"] = Uniform(mini=-1.8, maxi=0.2)
    model_params["dust2"]["prior"] = Uniform(mini=0.0, maxi=1.0)

    model = SpecModel(model_params)
    return model

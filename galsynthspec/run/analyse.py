from galsynthspec.datamodels import Galaxy, Result
from galsynthspec.plotting.corner import plot_corner
from galsynthspec.plotting.sed import generate_sed_plot
from galsynthspec.utils.predict import get_predicted_photometry


def analyse_results(galaxy: Galaxy, res: Result):
    """
    Analyse the results of the fitting process and plot the corner plot.

    :param galaxy: Galaxy The galaxy object to analyse results for.
    :param res: Result The result of the fitting process.
    :return: None
    """

    plot_corner(res=res, out_path=galaxy.corner_path)
    sample_df = generate_sed_plot(res=res, out_dir=galaxy.base_output_dir)
    get_predicted_photometry(galaxy, res, sample_df=sample_df)

"""
Mapping of common filter names to sedpy filter names.
"""

sedpy_map = {
    "sdss_u": "sdss_u0",
    "sdss_g": "sdss_g0",
    "sdss_r": "sdss_r0",
    "sdss_i": "sdss_i0",
    "sdss_z": "sdss_z0",
    "panstarrs_g": "sdss_g0",
    "panstarrs_r": "sdss_r0",
    "panstarrs_i": "sdss_i0",
    "panstarrs_z": "sdss_z0",
    "panstarrs_y": None,
    "2mass_j": "twomass_J",
    "2mass_h": "twomass_H",
    "2mass_ks": "twomass_Ks",
    "wise_w1": "wise_w1",
    "wise_w2": "wise_w2",
    "wise_w3": "wise_w3",
    "wise_w4": "wise_w4",
    "galex_fuv": "galex_FUV",
    "galex_nuv": "galex_NUV",
    "legacysurvey_g": "decam_g",
    "legacysurvey_r": "decam_r",
    "legacysurvey_z": "decam_z",
}

# --- Canonical survey names expected by HostPhot ---
SURVEYS_ALL = ["GALEX", "PanSTARRS", "SDSS", "2MASS", "WISE", "LegacySurvey"]

# Priority for reference mask/aperture
REF_PRIORITY = ["LegacySurvey", "PanSTARRS", "SDSS"]

# Coadd filter recipe per ref survey (string concat is supported)
COADD_FILTERS = {
    "LegacySurvey": "grz",
    "PanSTARRS": "griz",
    "SDSS": "griz",
}


# WISE coadd and ref choices
WISE_FILTERS = ["W1", "W2", "W3", "W4"]
WISE_COADD_STR = "".join(WISE_FILTERS)  # "W1W2W3W4"
WISE_REF_FILT = "W1"

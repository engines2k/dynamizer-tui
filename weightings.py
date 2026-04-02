import numpy as np

__all__ = ["a_weighting"]

def a_weighting(f):
    '''
    Take in a frequency (or array of frequencies) and return a weighting 
    to equalize loudness to human ears between different frequencies.
    '''
    f = np.asarray(f)
    f_sq = f ** 2
    num = 12194**2 * f ** 4
    den = ((f_sq + 20.6**2) * 
           np.sqrt((f_sq + 107.7**2) * (f_sq + 737.9**2)) * 
           (f_sq + 12194**2))
    weight_linear = num / den
    weight_db = 20 * np.log10(weight_linear + 1e-10) - 20 * np.log10(_a_weighting_1khz())
    return weight_db

def _a_weighting_1khz():
    f = 1000
    return 12194**2 * f**4 / ((f**2 + 20.6**2) * np.sqrt((f**2 + 107.7**2) * (f**2 + 737.9**2)) * (f**2 + 12194**2))

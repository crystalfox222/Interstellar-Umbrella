import numpy as np 
import load_all
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os
from datetime import date
import random
import solar_model as solar
#Stefan–Boltzmann constant
from scipy.constants import sigma


def adjust_solar_flux(tsi: float, distance_au: float) -> float:
    """
    Adjust the Total Solar Irradiance (TSI) based on a planets distance from the sun

    Uses the inverse-square law to calculate the solar flux received by a planet
    at a given distance in AU

    Parameters:
    - tsi (float): total solar irradiance at 1 AU (in W/m²)
    - distance_au (float): distance from the sun in AU

    Returns:
    - float: adjusted solar flux at the planets orbit (W/m²)
    """
    return tsi / (distance_au ** 2)

def estimate_blackbody_temp(tsi: float, albedo: float) -> float:
    """
    Estimate the planet's effective blackbody temperature (no atmosphere).

    Uses the Stefan–Boltzmann law assuming the planet is a perfect emitter
    with uniform temperature and energy balance between incoming and outgoing radiation.

    Parameters:
    - tsi (float): solar irradiance at the planets orbit (W/m²)
    - albedo (float): reflectivity of the planet (0 = absorbs all, 1 = reflects all)

    Returns:
    - float: estimated blackbody temperature in kelvin
    
    Math:
    - incoming energy: tsi * (1 - albedo)
    - distributed over entire surface (4πr²), not just cross-section (πr²)
    - T(k) = [(S * (1 - A)) / (4 * σ)]^0.25
    """
    return ((tsi * (1 - albedo)) / (4 * sigma)) ** 0.25

def apply_greenhouse_effect(base_temp: float, greenhouse_factor: float) -> float:
    return base_temp * greenhouse_factor

def apply_uv_chemistry(composition: dict, uv_index: float, rules: dict) -> dict:
    
    pass
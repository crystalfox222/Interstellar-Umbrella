import numpy as np 
import load_all
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os
from datetime import date
import random

#this date is a known peak in the sun cycle and will help me accurately place the solar modulation
ANCHOR_DATE = date(2014, 4, 1)

#estimated daily sunspots
def sunspot_estimation(date) -> float:
    """
    Estimate daily average sunspot numbers
    a combination of solar cycles 
    11-year Schwabe (core cycle) 
    88-year Gleissberg cycle (modulates amplitude)
    210-year Suess/de Vries cycle (long-term modulation)

    Parameters:
    - date[] - not datetime format due to limitations (4000bc = 4000ad)

    Returns:
    - sunspot_number (float) - a prediction of how many spots happened that day
    """
    #array of years
    year= date.year
    day_of_year = date.day_of_year
    #absolute value of sin - basic solar cycle
    base_amplitude = 100
    sunspot_year_average = {}
    #basic solar cycle
    core_cycle = abs(np.sin(2*(np.pi) * year / 11))
    #gleissberg model for 88 year cycle - influence on strength of solar cycles
    gleissberg_mod = .75 + .25* np.sin(2*np.pi * year / 88)
    #Suess 210 year cycle - changes sunspot strength over millennia
    suess_mod = 0.8 + 0.2 * np.sin(2*np.pi *year / 210)
    #Daily variation based on anual cycle - intra-year variation
    daily_mod = 0.9 + 0.1 * np.sin(2*np.pi * day_of_year/ 365.25)
    sunspot_number = base_amplitude * core_cycle * gleissberg_mod *suess_mod * daily_mod
    return sunspot_number

#amount of uv flux particles hitting surface of a planet
def estimate_uv_flux(f10_7=None, sunspot_number=None, distance_au=1.0, atmos_atten=1.0):
    """
    Estimate UV flux (W/m^2) based on solar radio flux (F10.7 index) and/or sunspot number

    Parameters:
    - f10_7 (float): F10.7 cm solar radio flux index (typical range: ~70 to 300)
    - sunspot_number (float): Daily sunspot number (typical rang: 0-250)

    Returns:
    - estimated_uv_flux (float): Estimated UV flux (W/m^2) at the top of the atmosphere of a planet
    """
    #this is an assumed average: subject to change
    base_uv_flux = 35.0 #uv at 1AU with F10.7 = 100

    #estimate using sunspots if f10.7 is unavaliable for whatever reason
    if f10_7 is None and sunspot_number is None:
        raise ValueError("Must provide params")
    elif f10_7 is None and sunspot_number is not None:
        f10_7 = 67 + 0.6 * sunspot_number
    
    #normalization
    solar_multiplier = f10_7 / 100.0

    #inverse relationship to distance
    distance_factor = 1 / (distance_au ** 2)

    #flux at the top of the atmosphere
    flux_toa = base_uv_flux * solar_multiplier * distance_factor

    #atmospheric attenuation will be estimated later
    estimated_solar_uv_flux = flux_toa * atmos_atten

    return estimated_solar_uv_flux

def get_real_modulation(date, amplitude=0.15, cycle_years=11, min_mod=1.15, max_mod =1.15) -> float:
    """
    Simulate long-term modulation using sine wave - model measures/tracks peaks and valleys in sun cycle for better cosmic modeling

    Parameters:
    - date[]: not datetime format due to limitations (4000bc = 4000ad)
    - amplitude (float): peak deviation from baseline 
    - cycle_years (float): solar cycle duration 
    - min_mod (float): lower limit
    - max_mod (float): upper limit

    Returns:
    -  (float): smoothed multiplier to help keep track of predictable solar behaviors like radiation and sunspots
    """
    #format date such that: 2014-04-1 = 2014.2493
    year_fraction = date.year + (date.timetuple().tm_yday / 365)

    #cycle synchronization to anchor date (peak)
    phase = 2 * np.pi * (year_fraction - ANCHOR_DATE) / cycle_years

    #calculate raw sine now that its centered
    raw_mod = 1.0 + amplitude * np.sin(phase)

    #bounds for the modulation and rounding for convenience
    return round(max(min(raw_mod, max_mod), min_mod), 4)

def estimate_phi_mv(sunspot_number: float) -> float:
    """
    Estimate solar modulation POTENTIAL in mv from sunspot numbers
    Range (250, 1500)
    """
    return 250 + 5*sunspot_number

#high energy events - highly random 
def estimate_cosmic_flux(phi_MV: float, date_obj: date) -> float:
    """
    Estimate incoming cosmic ray flux daily based on modulation
    Suppressed by solar activity

    Parameters: phi_MV (float): modulation potential in megavolts

    Returns:
    - Estimated cosmic flux in arbitrary units
    """
    #arbitrary base flux from universe
    LIS_flux = 5.0
    #how much is solar activity shielding this solar system from ray intensity
    suppression = np.exp(-phi_MV / 1000)
    #random daily fluctuation - these events themselves are highly random
    fluctuation = random.uniform(0.95, 1.05)
    #final estimation
    flux = LIS_flux * suppression * fluctuation
    return flux

#electromagnetic energy emitted by the Sun hitting planet surface
def estimate_solar_flux(date):
    """
    Estimate daily solar electromagnetic flux using cyclical variation in solar output
    sine model solar cycle used
    
    Parameters:
    - date[]

    Returns: 
    - Estimated flux solar in SFU
    """
    #a full cycle in days
    SOLAR_CYCLE_LENGTH_DAYS = 4015
    #min flux
    BASE_FLUX = 65.0
    #peak-to-peak amplitude of cycle
    FLUX_VARIATION = 25.0
    #optional offset
    PHASE_SHIFT = 0
    #time since anchor (need to alter for B.C. dates)
    days_since_anchor = (date - ANCHOR_DATE).days
    #position in radians within cycle
    cycle_position = (2 * np.pi * days_since_anchor / SOLAR_CYCLE_LENGTH_DAYS)
    #calculate using model
    flux = BASE_FLUX + FLUX_VARIATION * np.sin(cycle_position)

    return flux


# !!!!! VALIDATION !!!!!
def adf(path, names, dataset, adf, acf):
    df = pd.read_csv(
        path,
        sep=';',
        header=None,
        names=names,
        engine='python'
    )
    if dataset == 1:
        #cleaning data
        df["Sunspots"] = df["Sunspots"].replace(-1, pd.NA)
        df.dropna(subset=["Sunspots"], inplace=True)
        #convert the int to a string type date
        df["date"] = pd.to_datetime(df[["Year", "Month", "Day"]])
        #set the indexing param to the date
        df.set_index("date", inplace=True)
        
        series = df["Sunspots"]
            
        # ADF TESTING - indexing the results, limiting decimals 
        if adf == True:
            adf_result = adfuller(series.dropna())
            print(f"ADF Statistic: {adf_result[0]:.4f}")
            print(f"p-value: {adf_result[1]:.4e}")
            print(f"Lags used: {adf_result[2]}")
            print(f"Observations: {adf_result[3]}")
        if acf == True:
            fig, axes = plt.subplots(1, 2, figsize=(16, 4))
            plot_acf(series, lags=40, ax=axes[0])
            plot_pacf(series, lags=40, ax=axes[1])
            plt.show()

    elif dataset == 2:
        pass
    else:
        pass
    
    
def main():
    spot_path = os.path.join(os.getcwd(), "SN_d_tot_V2.0.csv")
    uv_flux_path = os.path.join(os.getcwd(), "fluxtable.txt")
    names_spots=["Year", "Month", "Day", "DecimalDate", "Sunspots", "STDDev", "num_obs", "Definitive"]
    names_flux=[]
    adf(spot_path, names_spots, 1, True, True)
    adf(uv_flux_path, names_flux, 2, True, True)
    
if __name__ == "__main__":
    main()

import numpy as np 
import load_all
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os

#estimated daily sunspots
def sunspot_estimation(start_year, end_year, seed):
    #array of years
    years = np.arange(start_year, end_year + 1)
    #absolute value of sin - basic solar cycle
    base_amplitude = 100
    sunspot_year_average = {}
    for year in years:
        core_cycle = abs(np.sin(2*(np.pi) * year / 11))
        #gleissberg model for 88 year cycle - influence on strength of solar cycles
        gleissberg_mod = .75 + .25* np.sin(2*np.pi * year / 88)
        #Suess 210 year cycle - changes sunspot strength over millennia
        suess_mod = 0.8 + 0.2 * np.sin(2*np.pi *year / 210)
        sunspot_number = base_amplitude * core_cycle * gleissberg_mod *suess_mod
        sunspot_year_average[year] = sunspot_number
        
    return sunspot_year_average

#amount of uv flux particles hitting surface of a planet
def estimate_uv_flux(f10_7=None, sunspot_number=None):
    #amount of flux hitting surface of a planet
    
    
    pass

#high energy events - highly random 
def cosmic_flux(start_year, end_year, seed):
    pass

#electromagnetic energy emitted by the Sun hitting planet surface
def solar_flux(start_year, end_year, seed):
    pass

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

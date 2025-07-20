import pandas as pd
import psycopg2
import os
import psycopg2.extras
import spiceypy as spice
from spiceypy import et2datetime
import numpy as np
from datetime import datetime, timedelta

#conversion constant
AU_IN_KM = 149597870.7

DATA_DIR = "data"

#SPICE target names within files
PLANET_IDS = {
    "Mercury": "MERCURY BARYCENTER",
    "Venus": "VENUS BARYCENTER",
    "Earth": "EARTH BARYCENTER",
    "Mars": "MARS BARYCENTER",
    "Jupiter": "JUPITER BARYCENTER",
    "Saturn": "SATURN BARYCENTER", 
    "Uranus": "URANUS BARYCENTER",
    "Neptune": "NEPTUNE BARYCENTER",
    "Pluto": "PLUTO BARYCENTER"
}

#connecting to database
def connect_db():
        return psycopg2.connect(
            dbname='planet_db',
            user="postgres",
            password="w0nderFul!?",
            host="localhost",
            port="5432"
    ) 
        
def load_files(seed):
    #uv flux
    if seed == 0:
        path_uv_flux= os.path.join(os.getcwd(), "fluxtable.txt")
        return path_uv_flux
    #sunspots
    elif seed == 1:
        path_sunspots= os.path.join(os.getcwd(), "SN_d_tot_V2.0.csv")
        return path_sunspots
    
def format_time(raw_time):
    return f"{raw_time[:2]}:{raw_time[2:4]}:{raw_time[4:]}"
    
def load_txt_to_postgres(file_path, seed):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    rows = []
    for line in lines:
        #skip empty lines
        if not line.strip():
            continue
        #seperate by whitespace
        parts = line.strip().split()
        #uv flux seed
        if seed == 0:
            if len(parts) != 7:
             print(f"Skipping line: quantity error: {line.strip()}")
            rows.append([
            parts[0],
            format_time(parts[1]),
            float(parts[2]),
            float(parts[3]),
            float(parts[4]),
            float(parts[5]),
            float(parts[6])
            ])
    return rows

def load_kernels():
    path_tls = os.path.join(os.getcwd(), "naif0012.tls")
    print(f"Loading kernel from: {path_tls}")
    spice.furnsh(path_tls)
    path_1_bsp = os.path.join(os.getcwd(), "de431_part-1.bsp")
    print(f"Loading kernel from: {path_1_bsp}")
    spice.furnsh(path_1_bsp)
    path_2_bsp = os.path.join(os.getcwd(), "de431_part-2.bsp")
    print(f"Loading kernel from: {path_2_bsp}")
    spice.furnsh(path_2_bsp)
      
def insert_planet_names(conn, planet_names):
    with conn.cursor() as cur:
        for name in planet_names:
            cur.execute(
                "INSERT INTO planets (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (name,)
            )
    conn.commit()
    
def insert_batch_to_db(conn, records, seed):
    with conn.cursor() as cur:
        #0= dynamic planet ephemeris data
        if seed == 0:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO ephemeris_data (
                        planet, et, date, x, y, z, vx, vy, vz,
                        distance_from_sun, velocity_mag
                    ) VALUES %s
                    """,
                    records,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    page_size=1000    
            )
        # 1 = flux data
        elif seed == 1:
            #count rows
            cur.execute("SELECT COUNT(*) FROM uv_flux_data")
            #check if populated
            if cur.fetchone()[0] > 0:
                print("uv_flux_data already populated. skip")
                conn.close()
                return
            psycopg2.extras.execute_values(
                cur, 
                """
                INSERT INTO uv_flux_data (
                        flux_date, flux_time, flux_julian,
                        flux_carrington, obs_flux,
                        adj_flux, flux_ursi
                    ) VALUES %s
                    """,
                    records,
                    template="(%s, %s, %s, %s, %s, %s, %s)",
                    page_size=1000
            )
    

def date_conversion(et):
    date_str = spice.et2utc(et, "C", 0)
    parts = date_str.split()
    
    if "B.C." in parts:
        year_str = f"{parts[0]} B.C."
        month_str = parts[2]
        day_str = parts[3]
    elif int(parts[0]) < 1000:
        year_str = parts[0]
        month_str = parts[2]
        day_str = parts[3] 
    else:
        year_str = parts[0]
        month_str = parts[1]
        day_str = parts[2]    
    month_map = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR" : "04",
        "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
        "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }
    month_num = month_map.get(month_str)
    date_formatted = f"{year_str} {month_num} {day_str}"
    return date_formatted
    
#focused on reading ephimeris data, not going to add anything to it
def stream_planet_to_db(conn, planet_name, start_date="01 JAN 13200 B.C.", end_date="31 DEC 17100 A.D.", step_days=1):
    et_start = spice.str2et(start_date)
    et_end = spice.str2et(end_date)
    step_seconds = step_days * 86400 #days to seconds
    
    et = et_start
    buffer = []
    batch_size = 1000
    with conn:
        while et <= et_end + 0.5:
            # convert current ET to readable date
            date_str = spice.et2utc(et, "C", 0)
            #ephemeris time to 
            date_only = date_str.split()[0:3]
            date_formated = date_conversion(et)
            
            state, _ = spice.spkezr(PLANET_IDS[planet_name], et, "ECLIPJ2000", "NONE", "SUN")
            #grab values
            pos_km = state[:3]
            vel_km_s = state[3:]
            #conversion
            pos_au = [x / AU_IN_KM for x in pos_km]
            #magnitude of 3d vector
            distance_au = np.linalg.norm(pos_au)
            #magnitude of velocity - scalar speed of planet in given moment
            velocity_mag = np.linalg.norm(vel_km_s)
            
            buffer.append((
                planet_name, et, date_formated, float(pos_au[0]), float(pos_au[1]), float(pos_au[2]), 
                float(vel_km_s[0]), float(vel_km_s[1]), float(vel_km_s[2]), float(distance_au),
                float(velocity_mag),
            ))
            
            if len(buffer) >= batch_size:
                insert_batch_to_db(conn, buffer, 0)
                buffer = []
            et += step_seconds
        if buffer:
            insert_batch_to_db(conn, buffer, 0)
    
    
def main():
    conn = connect_db()
    load_kernels()
    insert_planet_names(conn, PLANET_IDS.keys())
    for planet in PLANET_IDS:
        print(f"Loading: {planet}")
        stream_planet_to_db(conn, planet)
      
    #conn = connect_db()
    #rows = load_txt_to_postgres(load_files(0), 0)
    #insert_batch_to_db(conn, rows, 1)
    
    conn.close()
    #print("Fluxing awesome")
    print("All planetary data loaded into database")
    
if __name__ == "__main__":
    main()
import scipy
import numpy
import astropy
from skyfield.api import load as skyfield_load
from datetime import datetime as date, timedelta, timezone
import requests
import planetdata
import psycopg2
import json
import asyncpg
import math

class Planet:
    def __init__(self, name, mass, radius, distance_from_sun, orbital_period, atmosphere, surface_tempurature, location, tilt, albedo):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.distance_from_sun = distance_from_sun
        self.orbital_period = orbital_period
        self.atmosphere = atmosphere
        self.surface_tempurature = surface_tempurature
        self.location = location
        self.tilt = tilt
        self.albedo = albedo
    
    def average_temp_celsius(self):
        return self.surface_tempurature
    
    def distance_from_sun(self):
        return self.distance_from_sun
    
    def orbital_period(self):
        return self.orbital_period
    
    def atmosphere(self):
        return self.atmosphere
    
    def radius(self):
        return self.radius
    
    def mass(self):
        return self.mass
    
    def name(self):
        return self.name
    
    def location(self):
        return self.location
    
    def tilt(self):
        return self.tilt
    
    def albedo(self):
        return self.albedo
    
class PlanetDataLoader:
    def __init__(self, ephemeris_path, db_config):
        self.eph = skyfield_load(ephemeris_path)
        self.sun = self.eph['sun']
        self.ts = skyfield_load.timescale()
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        self.planet_names = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
            
    def load_static_planets(self):
        pass
    
    def load_planet_status_range(self, start_date, end_date):
        current = start_date
        while current <= end_date:
            t = self.ts.utc(current.year, current.month, current.day)
            for name in self.planet_names:
                self.insert_planet_status(name, t, current)
            current += timedelta(days=1)
        self.conn.commit()
        
    def update_today_planet_status(self):
        today = date.today()
        t = self.ts.utc(today.year, today.month, today.day)
        for name in self.planet_names:
            self.insert_planet_status(name, t, today)
        self.conn.commit
    
    def insert_planet_status(self, name, t, label_date):
        body = self.eph[name]
        obs = body.at(t).observe(self.sun).apparent()
        
        x, y, z = obs.position.au
        vx, vy, vz = obs.velocity.au_per_d
        distance_au = (x**2 + y**2 + z**2) ** 0.5
        speed = (vx**2 + vy**2 + vz**2) ** 0.5 #solar velocity
        
        #Orbital angle in 2d plane sun centered ecliptic
        orbital_angle_rad = math.atan2(y, x)
        orbital_angle_deg = math.degrees(orbital_angle_rad) % 360
        
        #solar radiation (inverse square law)
        radiation_level_usv = 1361/ (distance_au ** 2)
        
        self.cursor.execute("""
        INSERT INTO planet_status (
            planet_name, date,
            x_au, y_au, z_au, distance_au,
            orbital_angle_deg, solar_velocity, season, radiation_level_usv
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
            name, label_data, x, y, z, distance_au, orbital_angle_deg, speed, season, radiation_level_usv))
        
    def close(self):
        self.cursor.close()
        self.conn.close()

class SolarEventTracker:
    def __init__(self, api_key):
        self.client = APIClient("https://api.nasa.gov/DONKI/", api_key)
        
    def get_cmes(self, start, end):
        return self.client.get("CME", {"startDate": start, "endDate": end})
    
    def get_flares(self, start, end):
        return self.client.get("FLR", {"startDate": start, "endDate": end})

class SpaceWeatherAnalyzer:
    def __init__(self):
        pass
    
    def predict_temperature(self, planet_name, target_date):
        planet = self.get_planet_data(planet_name, target_date)
        constants = self.get_static_constants(planet_name)
        
        albedo = constants['albedo']
        distance_au = planet['distance_au']
        orbital_angle = math.radians(planet['orbital_angle_deg'])
        axial_tilt = math.radians(planet['axial_tilt_deg'])
        
        sigma = 5.670374419e-8 # W/m^2 - K^4
        solar_constant_earth = 1361 # W/m^2
        
        S = solar_constant_earth / (distance_au ** 2)
        
        pressure = constants['surface_pressure_kpa']
        greenhouse = self.estimate_greenhouse_warming(pressure, constants['atmosphere'])
        
        seasonal_shift = self.estimate_seasonal_temp_shift(axial_tilt, orbital_angle)
        
        base_temp = 5778 #sun temp in k
        
        estimated_temp = base_temp / (distance_au**2)
        return estimated_temp

    def predict_weather(self, planet_data):
        #simple rules for placeholding
        if planet_data['distance_au'].au < 0.5:
            event = "Solar storm likely"
        elif planet_data['distance_au'].au > 0.5:
            event = "Frozen Atmosphere"
        else:
            event = "Mild atmospheric disturbance"
        
        print(f"Predicted Event: {event}")

    def predict_wind_speed(self, planet_data):
        #dependant on solar wind???
        distance = planet_data['distance_au'].au
        wind_speed = 1000/distance #placeholder
        print(f"Predicted wind speed: {wind_speed:.2f}m/s")
        return wind_speed

    def predict_radiation(self, planet_data):
        #grab model trends or use api depending on date
        pass

    def predict_air_quality(self, planet_data):
        #rolling averages of elements to predict how heavy atmosphere is in combination with radiation data
        pass
    
    def get_season(self, planet_data):
        #ranges of x values and y values forming a top down grid
        pass
    
class APIClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        pass
    
    def get(self, endpoint, params=None):
        if params is None:
            params = {}
            
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            print(f"API Request Error: {e}")
            return []
    
class TimeManager:
    def __init__(self):
        self.timescale = skyfield_load.timescale()
    
    def now_utc(self):
        return date.now(timezone.utc)
    
    def formatted_now(self):
        return self.now_utc().strftime('%Y-%m-%d')
    
    def days_ago(self, days):
        return self.now_utc() - timedelta(days=days)
     
    def formatted_days_ago(self, days):
        return self.days_ago(days).strftime('%Y-%m-%d')
    
    def date_range(self, days):
        return self.formatted_days_ago(days), self.formatted_now()
    
    def parse(self, date_str):
        return date.strptime(date_str, '%Y-%m-%d')
    
    def skyfield_now(self):
        return self.timescale.now()
    
    def to_skyfield_time(self, dt):
        return self.timescale.utc(dt)
            
        
class ModelRunner:
    def __init__(self):
        pass

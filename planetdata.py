import calculations
import psycopg2
import json
import asyncpg

planet_static_data = {
    "Mercury": {
        "distance_from_sun_au": 0.39,
        "atmosphere": {
            "O2": 0.42,
            "Na": 0.29,
            "H2": 0.22
        },
        "gravity_g": 0.38
    },
    "Venus": {
        "distance_from_sun_au": .72,
        "atmosphere": {
            "CO2": 0.965,
            "N2": 0.035
        },
        "gravity_g": 0.9
    },
    "Earth": {
        "distance_from_sun_au": 1.0,
        "atmosphere": {
            "N2": 0.78,
            "O2": 0.21,
            "Ar": 0.0093,
            "CO2": 0.0004
        },
        "gravity_g": 1.0
    },
    "Mars": {
        "distance_from_sun_au": 1.52,
        "atmosphere": {
            "CO2": 0.95,
            "N2": 0.027,
            "Ar": 0.016
        },
        "gravity_g": 0.38
    },
    "Jupiter": {
        "distance_from_sun_au": 5.2,
        "atmosphere": {
            "H2": 0.89,
            "He": 0.10
        },
        "gravity_g": 2.53
    },
    "Saturn": {
        "distance_from_sun_au": 9.58,
        "atmosphere": {
            "H2": 0.96,
            "He": 0.03
        },
        "gravity_g": 1.07
    },
    "Uranus": {
        "distance_from_sun_au": 9.58,
        "atmosphere": {
            "H2": 0.83,
            "He": 0.15,
            "CH4": 0.02
        },
        "gravity_g": 0.89
    },
    "Neptune": {
        "distance_from_sun_au": 30.1,
        "atmosphere": {
            "H2": 0.89,
            "He": 0.19,
            "CH4": 0.01
        },
        "gravity_g": 1.14
    }
}
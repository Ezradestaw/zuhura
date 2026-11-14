from typing import List, Optional
from fastapi import APIRouter

router = APIRouter()

MARS_MISSIONS = [
    {
        "id": "mars-2020-perseverance",
        "name": "Perseverance Rover & Ingenuity Helicopter",
        "agency": "NASA / JPL",
        "type": "rover",
        "launch_year": 2020,
        "landing_date": "2021-02-18",
        "landing_site": {
            "name": "Octavia E. Butler Landing (Jezero Crater)",
            "latitude": 18.4447,
            "longitude": 77.4508,
            "elevation_m": -2560.0
        },
        "status": "active",
        "primary_science": "Astrobiology, ancient biosignatures, sample caching, geology of delta deposits."
    },
    {
        "id": "msl-curiosity",
        "name": "Curiosity Rover (Mars Science Laboratory)",
        "agency": "NASA / JPL",
        "type": "rover",
        "launch_year": 2011,
        "landing_date": "2012-08-06",
        "landing_site": {
            "name": "Bradbury Landing (Gale Crater)",
            "latitude": -4.5895,
            "longitude": 137.4417,
            "elevation_m": -4445.0
        },
        "status": "active",
        "primary_science": "Past habitability, clay/sulfate stratigraphy of Mount Sharp, environmental radiation."
    },
    {
        "id": "insight-lander",
        "name": "InSight Lander",
        "agency": "NASA / CNES / DLR",
        "type": "lander",
        "launch_year": 2018,
        "landing_date": "2018-11-26",
        "landing_site": {
            "name": "Elysium Planitia",
            "latitude": 4.5024,
            "longitude": 135.6234,
            "elevation_m": -2613.0
        },
        "status": "mission_complete",
        "primary_science": "Planetary seismology (SEIS), internal crust/mantle structure, core state."
    },
    {
        "id": "mer-b-opportunity",
        "name": "Opportunity Rover (MER-B)",
        "agency": "NASA / JPL",
        "type": "rover",
        "launch_year": 2003,
        "landing_date": "2004-01-25",
        "landing_site": {
            "name": "Meridiani Planum (Eagle Crater)",
            "latitude": -1.9483,
            "longitude": 354.4742,
            "elevation_m": -1387.0
        },
        "status": "mission_complete",
        "primary_science": "Hematite spherules ('blueberries'), ancient acidic aqueous environment evidence."
    },
    {
        "id": "mer-a-spirit",
        "name": "Spirit Rover (MER-A)",
        "agency": "NASA / JPL",
        "type": "rover",
        "launch_year": 2003,
        "landing_date": "2004-01-04",
        "landing_site": {
            "name": "Gusev Crater (Columbia Memorial Station)",
            "latitude": -14.5684,
            "longitude": 175.4729,
            "elevation_m": -1950.0
        },
        "status": "mission_complete",
        "primary_science": "Volcanic plains, hydrothermal silica deposits at Home Plate."
    },
    {
        "id": "viking-1-lander",
        "name": "Viking 1 Lander",
        "agency": "NASA",
        "type": "lander",
        "launch_year": 1975,
        "landing_date": "1976-07-20",
        "landing_site": {
            "name": "Chryse Planitia",
            "latitude": 22.48,
            "longitude": 312.05,
            "elevation_m": -2690.0
        },
        "status": "mission_complete",
        "primary_science": "First successful Mars landing and surface imagery; biology experimentation."
    },
    {
        "id": "viking-2-lander",
        "name": "Viking 2 Lander",
        "agency": "NASA",
        "type": "lander",
        "launch_year": 1975,
        "landing_date": "1976-09-03",
        "landing_site": {
            "name": "Utopia Planitia",
            "latitude": 47.97,
            "longitude": 134.28,
            "elevation_m": -3630.0
        },
        "status": "mission_complete",
        "primary_science": "Northern plains regolith analysis; seasonal water-ice frost detection."
    }
]


@router.get("/missions", summary="List Mars Missions and Landing Sites")
async def list_missions():
    """Returns list of landing sites and surface exploration missions on Mars."""
    return {
        "total": len(MARS_MISSIONS),
        "missions": MARS_MISSIONS
    }

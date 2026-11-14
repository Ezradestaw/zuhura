"""
Mars Geodetic Constants based on the IAU/IAG Working Group on Cartographic
Coordinates and Rotational Elements (WGCCRE 2015).
"""

# Equatorial Semi-Major Axis (A) in meters
MARS_A_EQUATORIAL_RADIUS_M: float = 3396190.0

# Polar Semi-Minor Axis (C / B) in meters
MARS_C_POLAR_RADIUS_M: float = 3376200.0

# Flattening: f = (A - C) / A
MARS_FLATTENING: float = (MARS_A_EQUATORIAL_RADIUS_M - MARS_C_POLAR_RADIUS_M) / MARS_A_EQUATORIAL_RADIUS_M
# Inverse Flattening: 1/f approx 169.81
MARS_INVERSE_FLATTENING: float = 1.0 / MARS_FLATTENING

# First Eccentricity Squared: e^2 = 2f - f^2 = (A^2 - C^2) / A^2
MARS_E_SQUARED: float = (MARS_A_EQUATORIAL_RADIUS_M**2 - MARS_C_POLAR_RADIUS_M**2) / (MARS_A_EQUATORIAL_RADIUS_M**2)

# Mean Volumetric Radius in meters
MARS_MEAN_RADIUS_M: float = 3389500.0

# Mars Standard Gravitational Parameter GM in m^3 / s^2
MARS_GM: float = 4.282837e13

# Mars Surface Gravity in m / s^2
MARS_SURFACE_GRAVITY_M_S2: float = 3.72076

# Mars Planetary Mass in kg
MARS_PLANETARY_MASS_KG: float = 6.4171e23

# Prime Meridian Origin Feature: Center of Crater Airy-0
MARS_PRIME_MERIDIAN_FEATURE: str = "Airy-0"

# Topography Reference Datum
MARS_TOPOGRAPHY_DATUM: str = "Mars Areoid (MOLA GMM-2B Potential Surface)"

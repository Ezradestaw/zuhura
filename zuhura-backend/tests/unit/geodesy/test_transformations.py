import math
import pytest
from zuhura.geodesy.constants import (
    MARS_A_EQUATORIAL_RADIUS_M,
    MARS_C_POLAR_RADIUS_M,
    MARS_FLATTENING,
)
from zuhura.geodesy.transformations import (
    planetographic_to_planetocentric_lat,
    planetocentric_to_planetographic_lat,
    normalize_east_longitude,
    calculate_latitudinal_positional_difference_km,
    planetocentric_to_cartesian,
    cartesian_to_planetocentric,
    mars_surface_distance_km,
)


class TestMarsGeodesyTransformations:

    def test_equator_and_poles_invariance(self):
        """At 0° (equator) and ±90° (poles), planetographic and planetocentric latitudes are identical."""
        assert planetographic_to_planetocentric_lat(0.0) == 0.0
        assert planetocentric_to_planetographic_lat(0.0) == 0.0

        assert planetographic_to_planetocentric_lat(90.0) == 90.0
        assert planetocentric_to_planetographic_lat(90.0) == 90.0

        assert planetographic_to_planetocentric_lat(-90.0) == -90.0
        assert planetocentric_to_planetographic_lat(-90.0) == -90.0

    def test_mid_latitude_transformation(self):
        """
        At 45° planetographic latitude:
        tan(phi_c) = (C/A)^2 * tan(45°) = (3376200 / 3396190)^2 * 1.0 approx 0.98826
        phi_c = atan(0.98826) approx 44.662° (discrepancy ~0.338° or ~20 km)
        """
        phi_g = 45.0
        phi_c = planetographic_to_planetocentric_lat(phi_g)
        assert phi_c < phi_g
        assert math.isclose(phi_c, 44.662, abs_tol=0.01)

        # Invert back
        phi_g_back = planetocentric_to_planetographic_lat(phi_c)
        assert math.isclose(phi_g_back, phi_g, abs_tol=1e-7)

    def test_maximum_latitudinal_discrepancy(self):
        """
        Verifies that the surface positional error between planetographic and planetocentric
        conventions reaches ~20.0 km at mid-latitudes on Mars.
        """
        diff_km = calculate_latitudinal_positional_difference_km(45.0)
        assert 19.5 <= diff_km <= 20.5

    def test_longitude_normalization(self):
        """Tests East-positive normalization across [0, 360) and [-180, 180)."""
        # Simple positive
        assert normalize_east_longitude(45.0) == 45.0

        # Negative longitude (-45° -> 315° East)
        assert normalize_east_longitude(-45.0) == 315.0

        # West-positive conversion (45° West -> 315° East)
        assert normalize_east_longitude(45.0, is_west_positive=True) == 315.0

        # Wrap around (> 360)
        assert normalize_east_longitude(400.0) == 40.0

        # Range -180 to +180
        assert normalize_east_longitude(270.0, range_180=True) == -90.0

    def test_cartesian_round_trip(self):
        """Tests converting (lat, lon, alt) -> (X, Y, Z) -> (lat, lon, alt)."""
        test_lat = 18.38   # Jezero Crater
        test_lon = 77.58
        test_alt = -2500.0 # 2500m below Areoid

        x, y, z = planetocentric_to_cartesian(test_lat, test_lon, test_alt)
        lat_back, lon_back, alt_back = cartesian_to_planetocentric(x, y, z)

        assert math.isclose(lat_back, test_lat, abs_tol=1e-5)
        assert math.isclose(lon_back, test_lon, abs_tol=1e-5)
        assert math.isclose(alt_back, test_alt, abs_tol=0.1)

    def test_mars_surface_distance(self):
        """Tests great circle distance calculation between Jezero and Gale Crater."""
        # Jezero Crater: 18.38°N, 77.58°E
        # Gale Crater: -5.37°N, 137.86°E
        dist = mars_surface_distance_km(18.38, 77.58, -5.37, 137.86)
        # Approximate distance is ~3,780 km across Martian surface
        assert 3700.0 <= dist <= 3900.0

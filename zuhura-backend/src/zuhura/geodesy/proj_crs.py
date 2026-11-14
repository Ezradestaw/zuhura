"""
PROJ 9+ and WKT definitions for Mars Coordinate Reference Systems.
"""

# IAU 2015 Mars Biaxial Ellipsoid (IAU:49902)
MARS_2015_BIAXIAL_PROJ4 = "+proj=longlat +a=3396190 +b=3376200 +no_defs +type=crs"

# IAU 2015 Mars Sphere (IAU:49900)
MARS_2015_SPHERE_PROJ4 = "+proj=longlat +R=3396190 +no_defs +type=crs"

# Mars Simple Cylindrical / Equirectangular Projection
MARS_EQC_PROJ4 = "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=3396190 +b=3376200 +units=m +no_defs +type=crs"

# Mars North Polar Stereographic
MARS_NORTH_POLAR_STERE_PROJ4 = "+proj=stere +lat_0=90 +lat_ts=90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=3396190 +b=3376200 +units=m +no_defs +type=crs"

# Mars South Polar Stereographic
MARS_SOUTH_POLAR_STERE_PROJ4 = "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=3396190 +b=3376200 +units=m +no_defs +type=crs"

MARS_2015_WKT2 = """GEOGCRS["Mars (2015) - Sphere",
    DATUM["Mars (2015) - Sphere",
        ELLIPSOID["Mars (2015) - Sphere",3396190,0,
            LENGTHUNIT["metre",1]]],
    PRIMEM["Reference Meridian",0,
        ANGLEUNIT["degree",0.0174532925199433]],
    CS[ellipsoidal,2],
        AXIS["geodetic latitude (Lat)",north,
            ORDER[1],
            ANGLEUNIT["degree",0.0174532925199433]],
        AXIS["geodetic longitude (Lon)",east,
            ORDER[2],
            ANGLEUNIT["degree",0.0174532925199433]],
    USAGE[
        SCOPE["Planetary science, Mars surface exploration."],
        AREA["Mars"],
        BBOX[-90,-180,90,180]],
    ID["IAU",49900]]"""

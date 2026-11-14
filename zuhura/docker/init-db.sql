-- =============================================================================
-- Zuhura Mars Digital Twin - PostgreSQL Initial Setup
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Install pgvector if extension is available
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'vector'
    ) THEN
        CREATE EXTENSION IF NOT EXISTS "vector";
    END IF;
END $$;

-- Planetary coordinate reference system table entry for Mars 2015 Sphere / Ellipsoid if not in spatial_ref_sys
-- IAU:49900 (Sphere 3396190m) & IAU:49902 (Biaxial Ellipsoid a=3396190, b=3376200)
INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text)
VALUES
    (49900, 'IAU', 49900, 
     'GEOGCS["Mars 2015 Sphere",DATUM["Mars_2015",SPHEROID["Mars_2015",3396190,0]],PRIMEM["Reference_Meridian",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["IAU","49900"]]', 
     '+proj=longlat +R=3396190 +no_defs +type=crs'),
    (49902, 'IAU', 49902, 
     'GEOGCS["Mars 2015",DATUM["Mars_2015",SPHEROID["Mars_2015",3396190,169.81442]],PRIMEM["Reference_Meridian",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["IAU","49902"]]', 
     '+proj=longlat +a=3396190 +b=3376200 +no_defs +type=crs')
ON CONFLICT (srid) DO NOTHING;

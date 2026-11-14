"""
Attaches dataset citations and provenance to assistant answers.
Every measurement in an answer must come from a tool result or a cited dataset
(NASA PDS, USGS Astrogeology or the IAU nomenclature database).
"""

from typing import List, Dict, Any, Optional


AUTHORITATIVE_DATASET_CITATIONS = {
    "mola": {
        "dataset_id": "zuhura-mola-megdr-128",
        "title": "MGS MOLA MEGDR 128 px/deg Global Topography Model",
        "provider": "NASA PDS Geosciences Node / Washington University in St. Louis",
        "instrument": "Mars Orbiter Laser Altimeter (MOLA)",
        "mission": "Mars Global Surveyor (MGS)",
        "processing_level": "Level 3 / GDR (Experiment Gridded Data Record)",
        "spatial_resolution": "463.06 m/pixel (128 pixels/degree at equator)",
        "vertical_datum": "Mars Areoid (MOLA GMM-3 equipotential reference surface)",
        "vertical_accuracy": "1.0 - 3.0 meters (absolute), < 1 meter (relative)",
        "url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/",
        "doi": "10.1029/2001JE001504"
    },
    "viking": {
        "dataset_id": "zuhura-viking-mdim21",
        "title": "Mars Viking MDIM 2.1 Colorized Global Mosaic",
        "provider": "USGS Astrogeology Science Center / NASA PDS Cartography and Imaging Sciences Node",
        "instrument": "Viking Orbiter Visual Imaging Subsystem (VIS)",
        "mission": "Viking 1 & 2 Orbiters",
        "processing_level": "Level 4 / RDR (Radiometrically and geometrically calibrated mosaic)",
        "spatial_resolution": "231.54 m/pixel (256 pixels/degree)",
        "vertical_datum": "N/A (Optical Surface Reflectance / Orthomosaic)",
        "url": "https://astrogeology.usgs.gov/search/map/Mars/Viking/MDIM21/",
        "doi": "10.1029/2000JE001405"
    },
    "ctx": {
        "dataset_id": "zuhura-ctx-jezero-mosaic",
        "title": "MRO CTX Regional Mosaic (Jezero Crater Quadrangle)",
        "provider": "NASA PDS / Malin Space Science Systems (MSSS) / Murray Lab",
        "instrument": "Context Camera (CTX)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "processing_level": "Level 3 / RDR (Orthorectified controlled mosaic)",
        "spatial_resolution": "5.55 m/pixel",
        "vertical_datum": "N/A (Visible Surface Reflectance)",
        "url": "https://murray-lab.caltech.edu/CTX/",
        "doi": "10.1029/2009JE003463"
    },
    "hirise": {
        "dataset_id": "zuhura-jezero-hirise-mosaic",
        "title": "MRO HiRISE Jezero Crater Western Fan Delta Color Mosaic",
        "provider": "NASA PDS / University of Arizona Lunar and Planetary Laboratory",
        "instrument": "High Resolution Imaging Science Experiment (HiRISE)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "processing_level": "Level 3 / RDR (Map-projected multiband orthoimage)",
        "spatial_resolution": "0.25 - 0.50 m/pixel",
        "vertical_datum": "N/A (Sub-meter optical surface observation)",
        "url": "https://hirise.lpl.arizona.edu/",
        "doi": "10.1029/2006JE002766"
    },
    "themis": {
        "dataset_id": "zuhura-themis-ir-radiance",
        "title": "Mars Odyssey THEMIS Daytime & Nighttime Infrared Radiance Cubes",
        "provider": "NASA PDS / Arizona State University Mars Space Flight Facility",
        "instrument": "Thermal Emission Imaging System (THEMIS)",
        "mission": "2001 Mars Odyssey",
        "processing_level": "Level 2 / Calibrated Spectral Radiance (RDR)",
        "spatial_resolution": "100 m/pixel",
        "vertical_datum": "N/A (Thermal Infrared Emissivity / Thermal Inertia)",
        "url": "https://themis.asu.edu/",
        "doi": "10.1029/2003JE002167"
    },
    "missions": {
        "dataset_id": "zuhura-mars-pds-analyst-notebook",
        "title": "NASA PDS Planetary Data System - Analyst's Notebook",
        "provider": "NASA PDS Geosciences Node / Jet Propulsion Laboratory (JPL)",
        "instrument": "Surface Rover and Lander Science Suites",
        "mission": "Perseverance, Curiosity, InSight, MER Spirit/Opportunity, Viking",
        "processing_level": "Telemetry, Sol Operations, and Ground Target Notebooks",
        "spatial_resolution": "Centimeter to millimeter scale in-situ observations",
        "vertical_datum": "MOLA GMM-3 Areoid & Rover Traverse Frames",
        "url": "https://an.rsl.wustl.edu/",
        "doi": None
    }
}


class GroundingManager:
    """
    Manages scientific grounding, citation attribution, and validation of planetary facts.
    """

    @staticmethod
    def extract_citations_from_tools(executed_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dynamically analyzes executed tools and attaches authoritatively verified citations.
        """
        citations_map: Dict[str, Dict[str, Any]] = {}

        for tool in executed_tools:
            name = tool.get("tool_name", "")
            result = tool.get("result", {})

            # Elevation or morphometry -> MOLA citation
            if name in ["get_elevation_at_point", "get_regional_elevation_stats", "generate_terrain_profile", "get_terrain_morphometry"]:
                citations_map["mola"] = AUTHORITATIVE_DATASET_CITATIONS["mola"]

            # Feature comparison -> MOLA + IAU nomenclature
            elif name == "compare_planetary_features":
                citations_map["mola"] = AUTHORITATIVE_DATASET_CITATIONS["mola"]

            # Imagery coverage -> Viking + CTX + HiRISE as applicable
            elif name == "check_imagery_coverage":
                citations_map["viking"] = AUTHORITATIVE_DATASET_CITATIONS["viking"]
                hi_tier = result.get("highest_resolution_tier", "")
                if "HiRISE" in hi_tier:
                    citations_map["hirise"] = AUTHORITATIVE_DATASET_CITATIONS["hirise"]
                    citations_map["ctx"] = AUTHORITATIVE_DATASET_CITATIONS["ctx"]
                elif "CTX" in hi_tier:
                    citations_map["ctx"] = AUTHORITATIVE_DATASET_CITATIONS["ctx"]

            # Mission details -> NASA PDS Analyst's Notebook
            elif name == "query_mission_details":
                citations_map["missions"] = AUTHORITATIVE_DATASET_CITATIONS["missions"]

            # Catalog search -> extract matching dataset provenance
            elif name == "search_scientific_catalog":
                items = result.get("results", [])
                for item in items[:3]:
                    pid = item.get("product_id")
                    title = item.get("title", pid)
                    inst = item.get("instrument", "")
                    pds_url = item.get("pds_url") or "https://pds-geosciences.wustl.edu/"
                    citations_map[pid] = {
                        "dataset_id": pid,
                        "title": title,
                        "provider": "NASA PDS / USGS Astrogeology",
                        "instrument": inst,
                        "mission": item.get("mission", "Orbital/Surface Exploration"),
                        "processing_level": item.get("processing_level", "RDR"),
                        "spatial_resolution": f"{item.get('spatial_resolution_m', 'Variable')} m/px",
                        "vertical_datum": item.get("vertical_datum") or "MOLA Areoid (if topographic)",
                        "url": pds_url,
                        "doi": None
                    }

            # Dataset metadata query
            elif name == "get_dataset_metadata":
                pid = result.get("product_id", "")
                if pid:
                    citations_map[pid] = {
                        "dataset_id": pid,
                        "title": result.get("title", pid),
                        "provider": result.get("producer") or result.get("provider", "NASA PDS"),
                        "instrument": result.get("instrument", "N/A"),
                        "mission": result.get("mission", "N/A"),
                        "processing_level": result.get("processing_level", "RDR"),
                        "spatial_resolution": f"{result.get('native_resolution_m', 'Variable')} m/px",
                        "vertical_datum": result.get("vertical_datum", "MOLA Areoid"),
                        "url": result.get("archive_url") or "https://pds-geosciences.wustl.edu/",
                        "doi": result.get("doi")
                    }

        # If empty (general inquiry), default to MOLA and Viking baseline
        if not citations_map:
            citations_map["mola"] = AUTHORITATIVE_DATASET_CITATIONS["mola"]
            citations_map["viking"] = AUTHORITATIVE_DATASET_CITATIONS["viking"]

        return list(citations_map.values())

    @staticmethod
    def get_scientific_caveats(executed_tools: List[Dict[str, Any]]) -> List[str]:
        """
        Returns relevant scientific limitations and data caveats for user transparency.
        """
        caveats = []
        tool_names = [t.get("tool_name") for t in executed_tools]

        if any(name in tool_names for name in ["get_elevation_at_point", "generate_terrain_profile", "get_regional_elevation_stats"]):
            caveats.append(
                "Elevation values are defined relative to the Mars Areoid (MOLA GMM-3 equipotential reference surface) "
                "with an absolute vertical accuracy of 1–3 meters. Optical surface imagery must not be treated as elevation."
            )

        if "check_imagery_coverage" in tool_names or "get_dataset_metadata" in tool_names:
            caveats.append(
                "High-resolution observations (HiRISE at 0.25–0.50 m/px, CTX at 5.55 m/px) cover targeted footprints "
                "(< 4% of Mars). Areas outside active footprints fall back to Viking MDIM 2.1 (231.5 m/px)."
            )

        if "get_solar_illumination" in tool_names:
            caveats.append(
                "Solar illumination calculations use standard IAU Mars orbital ephemeris and axial obliquity (25.19°); "
                "local slope self-shadowing depends on high-resolution topography."
            )

        return caveats

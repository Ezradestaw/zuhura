"""
Assistant (Ask Zuhura) engine: sends questions to Gemini with map context and
data tools, and returns the answer with citations.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from zuhura.ai.gemini_client import gemini_client, GeminiResponse
from zuhura.ai.tools import (
    dispatch_tool_call,
    get_elevation_at_point,
    get_regional_elevation_stats,
    get_terrain_morphometry,
    generate_terrain_profile,
    compare_planetary_features,
    convert_coordinates,
    search_scientific_catalog,
    get_dataset_metadata,
    check_imagery_coverage,
    query_mission_details,
    check_priority_datasets,
)
from zuhura.ai.grounding import GroundingManager
from zuhura.ai.session_manager import session_manager, MapViewportContext
from zuhura.geodesy.transformations import normalize_east_longitude, mars_surface_distance_km

logger = logging.getLogger("zuhura.ai.scientist")

MARS_AI_SCIENTIST_SYSTEM_INSTRUCTION = """You are Zuhura, a research assistant for Mars science in the Zuhura Mars web application.
You serve planetary geologists, geophysicists, remote sensing specialists, educators, and mission planners.

CORE MANDATE & SCIENTIFIC INTEGRITY:
1. Geodetic Framework:
   - Mars coordinates are strictly Planetocentric Latitude [-90° to +90°] and East-positive Longitude [0° to 360°], referenced to the IAU/IAG 2015 WGCCRE biaxial ellipsoid (A = 3,396,190 m, C = 3,376,200 m).
   - Elevation Datum: All topographic elevations are relative to the Mars Areoid (MOLA GMM-3 / MEG128 equipotential reference surface).
   - NEVER confuse optical imagery reflectance with elevation.

2. Epistemic Rigor & Calibrated Scientific Language:
   Always use calibrated scientific tags to label evidence:
   - [MEASURED]: Direct measurements or calculated derivatives from validated data (e.g. MOLA areoid elevation, Horn 1981 slope, TRI roughness).
   - [OBSERVED]: Directly supported by calibrated source imagery or mission documentation (e.g. Viking color albedo, CTX bedrock outcrops, HiRISE boulders).
   - [INTERPRETED]: Scientific reasoning based on evidence (e.g. Jezero crater delta formation from ancient lacustrine phases).
   - [HYPOTHESIS]: Plausible scientific hypothesis, not yet proven (e.g. biosignature preservation, hydrothermal circulation).
   - [UNAVAILABLE]: Insufficient data or resolution to answer the query (e.g. sub-meter elevation over quads lacking stereo DTMs).
   - NEVER present unsupported hypotheses or speculative models as established facts.
   - When citing datasets, always include the instrument, mission, and spatial resolution.

3. Answer format:
   - Be brief: answer the question directly in about 150 words or fewer, unless the user asks for more detail.
   - Use plain sentences, short bullet lists and **bold** only. Do not use tables, LaTeX, math notation or horizontal rules.
   - Write units in plain text (for example "-2,648 m", "18.4° N").
   - Mention geologic era, stratigraphy or mission history only when it helps answer the question.
"""


class AssistantUnavailableError(RuntimeError):
    """Raised when the assistant cannot answer (not configured, or Gemini failed)."""


class MarsScientistEngine:
    """
    Core engine orchestrating Mars research queries, tool interactions, and scientific grounding.
    """

    async def chat(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        map_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a scientific research inquiry with conversation context and map telemetry.
        """
        session = session_manager.get_or_create_session(session_id)
        effective_session_id = session.session_id

        # Update session map context if provided
        if map_context:
            vp = MapViewportContext(
                camera_lat=map_context.get("camera_lat", 18.38),
                camera_lon=map_context.get("camera_lon", 77.58),
                camera_altitude_m=map_context.get("camera_altitude_m", 500000.0),
                viewport_bbox=map_context.get("viewport_bbox"),
                active_layers=map_context.get("active_layers", []),
                selected_feature_id=map_context.get("selected_feature_id")
            )
            session_manager.update_map_context(effective_session_id, vp)
        else:
            vp = session.active_map_context

        # Record user turn
        session_manager.add_turn(
            session_id=effective_session_id,
            role="user",
            content=prompt,
            map_context_snapshot=vp.model_dump()
        )

        if not gemini_client.is_available():
            raise AssistantUnavailableError(
                "The assistant is not configured. Set GEMINI_API_KEY on the server to enable it."
            )

        try:
            response = await self._chat_with_gemini(prompt, session, vp)
        except Exception as exc:
            logger.error("Gemini request failed: %s", exc)
            raise AssistantUnavailableError("The assistant could not answer right now. Try again later.") from exc

        if response.is_fallback:
            raise AssistantUnavailableError(
                response.text or "The assistant could not answer right now. Try again later."
            )

        citations = GroundingManager.extract_citations_from_tools(response.tool_calls)
        session_manager.add_turn(
            session_id=effective_session_id,
            role="assistant",
            content=response.text,
            executed_tools=response.tool_calls,
            citations=citations,
        )
        return {
            "session_id": effective_session_id,
            "answer": response.text,
            "citations": citations,
            "executed_tools": response.tool_calls,
            "provider": "gemini",
            "model": gemini_client.model_name,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "candidate_tokens": response.usage.candidate_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "context_applied": {
                "latitude": vp.camera_lat,
                "longitude": normalize_east_longitude(vp.camera_lon),
                "altitude_m": vp.camera_altitude_m,
            },
        }

    async def _chat_with_gemini(
        self,
        prompt: str,
        session: Any,
        vp: MapViewportContext
    ) -> GeminiResponse:
        """
        Executes conversation with Gemini using callable tools.
        """
        context_preamble = (
            f"\n[ACTIVE MAP TELEMETRY]\n"
            f"- Camera Coordinates: {vp.camera_lat:.4f}°N, {normalize_east_longitude(vp.camera_lon):.4f}°E\n"
            f"- Camera Altitude: {vp.camera_altitude_m:,.0f} meters\n"
            f"- Active Layers: {', '.join(vp.active_layers) if vp.active_layers else 'Viking MDIM 2.1 Basemap'}\n\n"
        )
        full_prompt = context_preamble + f"User Research Query: {prompt}"

        # Convert tool functions into callables for Gemini
        tools = [
            get_elevation_at_point,
            get_regional_elevation_stats,
            get_terrain_morphometry,
            generate_terrain_profile,
            compare_planetary_features,
            convert_coordinates,
            search_scientific_catalog,
            get_dataset_metadata,
            check_imagery_coverage,
            query_mission_details,
            check_priority_datasets
        ]

        # Call Gemini with structured system prompt
        response = await gemini_client.generate(
            contents=full_prompt,
            system_instruction=MARS_AI_SCIENTIST_SYSTEM_INSTRUCTION,
            tools=tools
        )
        return response

    async def analyze_location(self, latitude: float, longitude: float, altitude_m: float = 50000.0) -> Dict[str, Any]:
        """
        Instantaneous multi-tool planetary assessment of a specific coordinate.
        """
        norm_lon = normalize_east_longitude(longitude)
        t_elev = await dispatch_tool_call("get_elevation_at_point", {"latitude": latitude, "longitude": norm_lon})
        t_morph = await dispatch_tool_call("get_terrain_morphometry", {"latitude": latitude, "longitude": norm_lon, "kernel_size": 3})
        t_cov = await dispatch_tool_call("check_imagery_coverage", {"latitude": latitude, "longitude": norm_lon})
        t_sun = await dispatch_tool_call("get_solar_illumination", {"latitude": latitude, "longitude": norm_lon, "solar_longitude_ls": 0.0, "solar_time_hours": 12.0})

        executed_tools = [t_elev, t_morph, t_cov, t_sun]
        citations = GroundingManager.extract_citations_from_tools(executed_tools)

        return {
            "coordinate": {"latitude": latitude, "longitude": norm_lon, "altitude_m": altitude_m},
            "elevation": t_elev["result"],
            "morphometry": t_morph["result"],
            "imagery_coverage": t_cov["result"],
            "solar_illumination": t_sun["result"],
            "citations": citations,
            "executed_tools": executed_tools
        }

    async def analyze_region(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Dict[str, Any]:
        """
        Regional bounding box intelligence synthesis.
        """
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = normalize_east_longitude((min_lon + max_lon) / 2.0)
        radius_km = min(250.0, max(10.0, mars_surface_distance_km(min_lat, min_lon, max_lat, max_lon) / 2.0))

        t_stats = await dispatch_tool_call("get_regional_elevation_stats", {
            "latitude": center_lat,
            "longitude": center_lon,
            "radius_km": radius_km
        })
        t_cat = await dispatch_tool_call("search_scientific_catalog", {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon
        })

        executed_tools = [t_stats, t_cat]
        citations = GroundingManager.extract_citations_from_tools(executed_tools)

        return {
            "bounding_box": [min_lon, min_lat, max_lon, max_lat],
            "center_point": {"latitude": center_lat, "longitude": center_lon},
            "regional_statistics": t_stats.get("result", {}),
            "catalog_coverage": t_cat.get("result", {}),
            "citations": citations,
            "executed_tools": executed_tools
        }

    async def stream_chat(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        map_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) formatted text chunks and tool events.
        """
        session = session_manager.get_or_create_session(session_id)
        effective_session_id = session.session_id

        # Update map context
        if map_context:
            vp = MapViewportContext(
                camera_lat=map_context.get("camera_lat", 18.38),
                camera_lon=map_context.get("camera_lon", 77.58),
                camera_altitude_m=map_context.get("camera_altitude_m", 500000.0),
                viewport_bbox=map_context.get("viewport_bbox"),
                active_layers=map_context.get("active_layers", []),
                selected_feature_id=map_context.get("selected_feature_id")
            )
            session_manager.update_map_context(effective_session_id, vp)
        else:
            vp = session.active_map_context

        if not gemini_client.is_available():
            message = "The assistant is not configured. Set GEMINI_API_KEY on the server to enable it."
            yield f"event: error\ndata: {json.dumps({'message': message})}\n\n"
            return

        yield f"event: metadata\ndata: {json.dumps({'session_id': effective_session_id, 'model': gemini_client.model_name})}\n\n"
        async for token in gemini_client.stream_generate(prompt, system_instruction=MARS_AI_SCIENTIST_SYSTEM_INSTRUCTION):
            yield f"event: chunk\ndata: {json.dumps({'text': token})}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"


# Global singleton instance
mars_scientist_engine = MarsScientistEngine()

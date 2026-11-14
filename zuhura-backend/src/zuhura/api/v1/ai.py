"""
Assistant API endpoints.
Provides streaming and standard AI endpoints, geodetic analysis,
conversation session management, and health diagnostics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from zuhura.core.config import settings
from zuhura.ai.gemini_client import gemini_client
from zuhura.ai.scientist_engine import AssistantUnavailableError, mars_scientist_engine
from zuhura.ai.session_manager import session_manager, MapViewportContext
from zuhura.ai.tools import SCIENTIFIC_TOOLS_REGISTRY, load_science_catalog_products
from zuhura.geodesy.transformations import normalize_east_longitude


router = APIRouter()


# ------------------------------------------------------------------------------
# Request / Response Models
# ------------------------------------------------------------------------------

class ViewportBbox(BaseModel):
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=360.0)
    max_lon: float = Field(..., ge=-180.0, le=360.0)


class MapContextModel(BaseModel):
    camera_lat: float = Field(default=18.38, ge=-90.0, le=90.0)
    camera_lon: float = Field(default=77.58, ge=-180.0, le=360.0)
    camera_altitude_m: float = Field(default=500000.0, ge=10.0)
    viewport_bbox: Optional[ViewportBbox] = None
    active_layers: List[str] = Field(default_factory=list)
    selected_feature_id: Optional[str] = None


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000, description="Planetary research question or analysis command")
    session_id: Optional[str] = Field(default=None, description="Optional conversation session ID for context retention")
    map_context: Optional[MapContextModel] = None


class LocationAnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Planetocentric latitude in degrees")
    longitude: float = Field(..., ge=-180.0, le=360.0, description="East-positive longitude in degrees")
    altitude_m: float = Field(default=50000.0, ge=10.0, description="Camera or perspective altitude in meters")


class RegionAnalysisRequest(BaseModel):
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=360.0)
    max_lon: float = Field(..., ge=-180.0, le=360.0)


# ------------------------------------------------------------------------------
# Chat
# ------------------------------------------------------------------------------

async def _answer(req: "ChatRequest") -> Dict[str, Any]:
    map_ctx_dict = req.map_context.model_dump() if req.map_context else None
    try:
        return await mars_scientist_engine.chat(
            prompt=req.prompt,
            session_id=req.session_id,
            map_context=map_ctx_dict,
        )
    except AssistantUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/chat", summary="Ask the assistant a question")
async def chat_with_mars_scientist(req: ChatRequest):
    """Answers a question using the current map position, data tools and Gemini."""
    return await _answer(req)


@router.post("/chat/stream", summary="Ask the assistant a question (streamed)")
async def stream_chat_with_mars_scientist(req: ChatRequest):
    """Streams the answer as Server-Sent Events."""
    map_ctx_dict = req.map_context.model_dump() if req.map_context else None

    generator = mars_scientist_engine.stream_chat(
        prompt=req.prompt,
        session_id=req.session_id,
        map_context=map_ctx_dict
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/analyze-location", summary="Instant Coordinate Scientific Analysis")
async def analyze_location(req: LocationAnalysisRequest):
    """
    Runs an instant multi-sensor planetary analysis on a specific Martian coordinate:
    MOLA elevation, Horn slope, aspect, TRI roughness, TPI geomorphic class,
    orbital imagery coverage (Viking, CTX, HiRISE), and ephemeris illumination.
    """
    result = await mars_scientist_engine.analyze_location(
        latitude=req.latitude,
        longitude=req.longitude,
        altitude_m=req.altitude_m
    )
    return result


@router.post("/analyze-region", summary="Regional Bounding Box Planetary Analysis")
async def analyze_region(req: RegionAnalysisRequest):
    """
    Computes regional elevation statistics (min, max, mean, relief) and identifies
    validated orbital datasets and DTMs covering the specified bounding box.
    """
    if req.min_lat >= req.max_lat:
        raise HTTPException(status_code=400, detail="min_lat must be strictly less than max_lat")

    result = await mars_scientist_engine.analyze_region(
        min_lat=req.min_lat,
        max_lat=req.max_lat,
        min_lon=req.min_lon,
        max_lon=req.max_lon
    )
    return result


# ------------------------------------------------------------------------------
# System Diagnostics & Model Metadata
# ------------------------------------------------------------------------------

@router.get("/health", summary="Assistant status")
async def get_ai_health():
    """Reports whether Gemini is configured, plus tool, catalogue and session counts."""
    catalog_products = load_science_catalog_products()
    sessions = session_manager.list_sessions()

    gemini_avail = gemini_client.is_available()

    return {
        "status": "healthy" if gemini_avail else "unavailable",
        "service": "assistant",
        "provider": {
            "name": "gemini",
            "active_model": gemini_client.model_name if gemini_avail else None,
            "gemini_api_configured": gemini_avail,
            "rate_limit_per_minute": settings.AI_RATE_LIMIT,
            "max_output_tokens": settings.AI_MAX_OUTPUT_TOKENS,
            "timeout_seconds": settings.AI_REQUEST_TIMEOUT
        },
        "scientific_registry": {
            "registered_tools_count": len(SCIENTIFIC_TOOLS_REGISTRY),
            "tools": list(SCIENTIFIC_TOOLS_REGISTRY.keys()),
            "catalog_products_count": len(catalog_products),
            "geodetic_datum": settings.MARS_ELEVATION_DATUM
        },
        "session_state": {
            "active_sessions_count": len(sessions)
        }
    }


@router.get("/models", summary="Configured assistant model")
async def list_ai_models():
    """Returns the Gemini model the assistant uses, or null when it is not configured."""
    available = gemini_client.is_available()
    return {
        "current_active_model": gemini_client.model_name if available else None,
        "available": available,
    }


@router.get("/tools", summary="List assistant tools")
async def list_scientific_tools():
    """Lists the data tools the assistant can call."""
    tools_list = []
    for name, tool in SCIENTIFIC_TOOLS_REGISTRY.items():
        tools_list.append({
            "name": name,
            "description": tool["description"],
            "is_async": tool["is_async"],
            "has_input_schema": tool["input_schema"] is not None
        })
    return {"tools_count": len(tools_list), "tools": tools_list}


# ------------------------------------------------------------------------------
# Conversation Session Management
# ------------------------------------------------------------------------------

@router.get("/conversations", summary="List Active Research Conversations")
async def list_conversations():
    """
    Lists active research sessions and recent coordinates.
    """
    return {"conversations": session_manager.list_sessions()}


@router.get("/conversations/{session_id}", summary="Get Conversation History")
async def get_conversation(session_id: str):
    """
    Retrieves full dialogue history, executed tool logs, and citations for a session.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session.model_dump()


@router.delete("/conversations/{session_id}", summary="Delete / Reset Conversation")
async def delete_conversation(session_id: str):
    """
    Clears or resets a conversation session.
    """
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return {"status": "deleted", "session_id": session_id}


@router.post("/query", summary="Ask the assistant a question (older path)")
async def legacy_query(req: ChatRequest):
    """Same as /chat; kept for existing callers."""
    return await _answer(req)

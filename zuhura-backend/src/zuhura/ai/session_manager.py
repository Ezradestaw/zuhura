"""
Conversation session state for the assistant.
Maintains multi-turn research context, active map coordinates, and tool execution logs.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MapViewportContext(BaseModel):
    camera_lat: float = Field(default=18.38, ge=-90.0, le=90.0)
    camera_lon: float = Field(default=77.58, ge=-180.0, le=360.0)
    camera_altitude_m: float = Field(default=500000.0, ge=10.0)
    viewport_bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    active_layers: List[str] = Field(default_factory=list)
    selected_feature_id: Optional[str] = None


class ChatTurn(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str
    timestamp: float = Field(default_factory=time.time)
    executed_tools: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    map_context_snapshot: Optional[Dict[str, Any]] = None


class ResearchSession(BaseModel):
    session_id: str
    created_at: float = Field(default_factory=time.time)
    last_accessed_at: float = Field(default_factory=time.time)
    title: str = "Martian Geological Investigation"
    active_map_context: MapViewportContext = Field(default_factory=MapViewportContext)
    history: List[ChatTurn] = Field(default_factory=list)
    total_tokens_used: int = 0


class SessionManager:
    """
    In-memory, thread-safe session manager with automatic LRU and TTL eviction.
    """

    def __init__(self, max_sessions: int = 200, ttl_seconds: float = 7200.0):
        self._sessions: Dict[str, ResearchSession] = {}
        self._max_sessions = max_sessions
        self._ttl_seconds = ttl_seconds

    def _cleanup_expired(self):
        now = time.time()
        expired_ids = [
            sid for sid, s in self._sessions.items()
            if (now - s.last_accessed_at) > self._ttl_seconds
        ]
        for sid in expired_ids:
            del self._sessions[sid]

        # Enforce max limit if still over capacity
        if len(self._sessions) > self._max_sessions:
            sorted_sids = sorted(self._sessions.keys(), key=lambda k: self._sessions[k].last_accessed_at)
            to_remove = len(self._sessions) - self._max_sessions
            for sid in sorted_sids[:to_remove]:
                del self._sessions[sid]

    def get_or_create_session(self, session_id: Optional[str] = None) -> ResearchSession:
        self._cleanup_expired()
        now = time.time()

        if not session_id or session_id.strip() == "":
            session_id = f"mars-session-{uuid.uuid4().hex[:8]}"

        if session_id not in self._sessions:
            session = ResearchSession(session_id=session_id)
            self._sessions[session_id] = session
        else:
            session = self._sessions[session_id]
            session.last_accessed_at = now

        return session

    def update_map_context(self, session_id: str, context: MapViewportContext):
        session = self.get_or_create_session(session_id)
        session.active_map_context = context
        session.last_accessed_at = time.time()

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        executed_tools: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        map_context_snapshot: Optional[Dict[str, Any]] = None
    ) -> ChatTurn:
        session = self.get_or_create_session(session_id)
        turn = ChatTurn(
            role=role,
            content=content,
            executed_tools=executed_tools or [],
            citations=citations or [],
            map_context_snapshot=map_context_snapshot
        )
        session.history.append(turn)
        session.last_accessed_at = time.time()

        # Update title based on first user prompt if still default
        if role == "user" and session.title == "Martian Geological Investigation":
            cleaned = content.strip().replace("\n", " ")
            session.title = (cleaned[:45] + "...") if len(cleaned) > 45 else cleaned

        return turn

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        self._cleanup_expired()
        session = self._sessions.get(session_id)
        if session:
            session.last_accessed_at = time.time()
        return session

    def list_sessions(self) -> List[Dict[str, Any]]:
        self._cleanup_expired()
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at,
                "last_accessed_at": s.last_accessed_at,
                "turns_count": len(s.history),
                "active_coordinates": {
                    "lat": s.active_map_context.camera_lat,
                    "lon": s.active_map_context.camera_lon
                }
            }
            for s in sorted(self._sessions.values(), key=lambda x: x.last_accessed_at, reverse=True)
        ]

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def clear_all(self):
        self._sessions.clear()


# Global singleton instance
session_manager = SessionManager()

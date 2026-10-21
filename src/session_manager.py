"""
Session management for concurrent multi-user access.

This is the "Deters fit" piece: multiple users hit the same running system
at the same time, and each user's conversation state must stay isolated
while agent work happens concurrently, not queued one-user-at-a-time.

Design choices worth calling out in a project write-up:
  - Sessions are stored in-memory keyed by session_id (swappable for Redis
    in a real deployment — kept in-memory here to stay dependency-light for
    a portfolio demo, but the interface is written so that swap is a single
    class, not a rewrite).
  - Each request's agent work (retrieval + LLM calls) runs as an independent
    asyncio task, so N concurrent users' requests genuinely overlap in
    wall-clock time rather than blocking each other.
  - A per-session lock prevents a *single* user's two rapid-fire requests
    from racing each other and corrupting their own history, while still
    allowing different users to run fully in parallel.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List
import uuid


@dataclass
class SessionState:
    session_id: str
    history: List[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._global_lock = asyncio.Lock()

    async def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        async with self._global_lock:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return session_id

    async def get_or_create(self, session_id: str = None) -> SessionState:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        new_id = session_id or str(uuid.uuid4())
        async with self._global_lock:
            if new_id not in self._sessions:
                self._sessions[new_id] = SessionState(session_id=new_id)
        return self._sessions[new_id]

    async def record_turn(self, session_id: str, query: str, response: dict):
        session = await self.get_or_create(session_id)
        async with session.lock:
            session.history.append({"query": query, "response": response, "ts": time.time()})
            session.last_active = time.time()

    def active_session_count(self) -> int:
        return len(self._sessions)

    def get_history(self, session_id: str) -> List[dict]:
        session = self._sessions.get(session_id)
        return session.history if session else []

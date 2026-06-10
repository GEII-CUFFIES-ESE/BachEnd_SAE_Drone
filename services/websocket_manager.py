"""
Gestionnaire centralisé des connexions WebSocket.

Flux de données :
    1. Un client Angular se connecte  ──> connect()    ajoute son socket à _active_connections.
    2. La source de télémétrie produit un TelemetryFrame.
    3. broadcast() sérialise le frame en JSON et l'envoie à TOUS les clients connectés.
    4. Si un client se déconnecte     ──> disconnect() retire proprement son socket.

Ce singleton est importé par le router telemetry.py et injecté via dépendance FastAPI.
"""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Maintient le registre des connexions WebSocket actives et orchestre le broadcast."""

    def __init__(self) -> None:
        # Ensemble thread-safe des sockets ouverts.
        # On utilise un set pour garantir l'unicité et O(1) sur connect/disconnect.
        self._active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accepte la poignée de main WebSocket et enregistre la connexion."""
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info("Client connecté — total: %d", len(self._active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Retire le socket du registre (appelé sur close ou erreur réseau)."""
        self._active_connections.discard(websocket)
        logger.info("Client déconnecté — total: %d", len(self._active_connections))

    async def send_personal_message(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        """Envoie `payload` uniquement au client `websocket`.

        Utilisé pour la télémétrie individuelle : chaque connexion reçoit les données
        de son propre drone sans polluer les autres clients.
        En cas d'erreur réseau, le client est retiré proprement du registre.
        """
        try:
            await websocket.send_json(payload)
        except Exception as exc:
            logger.warning("Erreur envoi personnel WebSocket : %s", exc)
            self.disconnect(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        """Envoie `payload` (sérialisé en JSON) à tous les clients connectés en parallèle.

        Les sockets défaillants sont retirés silencieusement pour ne pas bloquer le broadcast.
        """
        if not self._active_connections:
            return

        dead: set[WebSocket] = set()

        results = await asyncio.gather(
            *[ws.send_json(payload) for ws in self._active_connections],
            return_exceptions=True,
        )

        for ws, result in zip(self._active_connections, results):
            if isinstance(result, Exception):
                logger.warning("Erreur envoi WebSocket, suppression du client : %s", result)
                dead.add(ws)

        self._active_connections -= dead

    @property
    def connection_count(self) -> int:
        """Nombre de clients actuellement connectés."""
        return len(self._active_connections)


# Instance singleton partagée par toute l'application.
manager = WebSocketManager()

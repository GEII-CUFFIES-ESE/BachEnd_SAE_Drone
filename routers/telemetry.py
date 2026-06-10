"""
Router WebSocket pour la télémétrie GPS en temps réel — sécurisé par token URL.

Flux :
    Angular ouvre ws://localhost:8000/ws/telemetry?token=<TOKEN>
    ──> validation du paramètre token lors du handshake
    ──> si token absent ou vide : fermeture WebSocket code 1008 (Policy Violation)
    ──> ConnectionManager.connect() accepte et enregistre le socket
    ──> boucle toutes les 500 ms :
            - calcule lat/lon simulés (dérive aléatoire autour de 49.04 / 3.40)
            - sérialise en JSON via send_personal_message() vers CE client uniquement
    ──> WebSocketDisconnect capturé ──> ConnectionManager.disconnect() retire le client

Sécurité mock :
    Tout token non-vide est accepté. En production, remplacer la validation
    par une vérification de signature JWT (python-jose ou PyJWT).
"""

import asyncio
import random
import time

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from services.websocket_manager import manager

router = APIRouter()

# Coordonnées GPS de référence autour desquelles le drone simule son déplacement.
_BASE_LATITUDE   = 49.04
_BASE_LONGITUDE  = 3.40
_GPS_DRIFT       = 0.001   # Amplitude max de variation par tick (≈ 111 m)
_TICK_INTERVAL_S = 0.5     # Fréquence de mise à jour : 2 Hz


@router.websocket("/telemetry")
async def websocket_telemetry(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """Endpoint WebSocket de télémétrie GPS sécurisé par token.

    Paramètre URL :
        token (str, obligatoire) : jeton d'authentification passé en query string.
            Ex : ws://localhost:8000/ws/telemetry?token=mon-token

    Comportement :
        - Si token absent ou vide : connexion refusée (close 1008 Policy Violation).
        - Si token valide : streaming continu de paquets JSON à 2 Hz :
            {
                "timestamp_ms": <int>,
                "latitude":     <float>,
                "longitude":    <float>
            }

    La connexion reste ouverte jusqu'à fermeture volontaire ou perte réseau.
    """
    # ── Validation du token lors du handshake (avant accept) ──────────────────
    if not token:
        await websocket.close(code=1008)  # 1008 = Policy Violation (RFC 6455)
        return

    # Validation mock : tout token non-vide est accepté.
    # En production : vérifier la signature JWT et l'expiration.

    await manager.connect(websocket)
    try:
        while True:
            payload = {
                "timestamp_ms": int(time.time() * 1000),
                "latitude":     round(_BASE_LATITUDE  + random.uniform(-_GPS_DRIFT, _GPS_DRIFT), 6),
                "longitude":    round(_BASE_LONGITUDE + random.uniform(-_GPS_DRIFT, _GPS_DRIFT), 6),
            }
            await manager.send_personal_message(websocket, payload)
            await asyncio.sleep(_TICK_INTERVAL_S)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

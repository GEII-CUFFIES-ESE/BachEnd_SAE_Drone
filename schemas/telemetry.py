"""
Contrats de données (schemas) pour la télémétrie du drone.

Rôle dans le flux :
    Drone ──UDP/MAVLink──> service de parsing ──> ces classes ──> JSON ──> client Angular

Chaque classe est l'équivalent d'une struct C strictement typée.
Pydantic valide les types à l'instantiation et sérialise nativement en JSON via .model_dump().
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FlightMode(str, Enum):
    """États de vol possibles du drone."""
    IDLE       = "IDLE"
    TAKEOFF    = "TAKEOFF"
    HOVER      = "HOVER"
    MISSION    = "MISSION"
    RETURN     = "RETURN"
    LANDING    = "LANDING"
    EMERGENCY  = "EMERGENCY"


class Position(BaseModel):
    """Coordonnées GPS 3D du drone.

    latitude / longitude : degrés décimaux (WGS-84).
    altitude_m          : altitude en mètres au-dessus du sol (AGL).
    heading_deg         : cap magnétique 0–360°.
    """
    latitude:    float = Field(..., ge=-90.0,  le=90.0)
    longitude:   float = Field(..., ge=-180.0, le=180.0)
    altitude_m:  float = Field(..., ge=0.0)
    heading_deg: float = Field(..., ge=0.0,    lt=360.0)


class Velocity(BaseModel):
    """Vecteur vitesse dans le repère NED (North-East-Down), en m/s."""
    vx_ms: float  # Nord  (+ = avant)
    vy_ms: float  # Est   (+ = droite)
    vz_ms: float  # Bas   (+ = descente)


class BatteryStatus(BaseModel):
    """État de la batterie principale.

    voltage_v      : tension en Volts.
    current_a      : intensité consommée en Ampères.
    remaining_pct  : pourcentage restant 0–100.
    time_remaining_s: estimation du temps de vol restant en secondes.
    """
    voltage_v:        float = Field(..., ge=0.0)
    current_a:        float = Field(..., ge=0.0)
    remaining_pct:    int   = Field(..., ge=0,   le=100)
    time_remaining_s: int   = Field(..., ge=0)


class TelemetryFrame(BaseModel):
    """Paquet de télémétrie complet envoyé à chaque tick au client Angular.

    Ce modèle agrège tous les sous-systèmes et constitue le contrat principal
    du WebSocket. Il est sérialisé en JSON puis broadcasté via WebSocketManager.

    timestamp_ms : horodatage UNIX en millisecondes (côté serveur).
    drone_id     : identifiant unique du drone (utile en cas de flotte).
    """
    timestamp_ms: int
    drone_id:     str
    flight_mode:  FlightMode
    position:     Position
    velocity:     Velocity
    battery:      BatteryStatus

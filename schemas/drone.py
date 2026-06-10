"""
Schéma de données pour la gestion de la flotte de drones.

Rôle dans le flux :
    GET /drones ──> liste de DroneInfo sérialisée en JSON ──> Angular (tableau de bord flotte)

DroneInfo est le contrat public de l'API REST — distinct de TelemetryFrame qui est
réservé au flux WebSocket temps-réel.
"""

from enum import Enum

from pydantic import BaseModel


class DroneStatus(str, Enum):
    """États opérationnels possibles d'un drone dans la flotte."""
    ONLINE   = "ONLINE"    # Connecté, en attente de mission
    OFFLINE  = "OFFLINE"   # Non joignable
    MISSION  = "MISSION"   # En cours de mission autonome
    CHARGING = "CHARGING"  # Au sol, en charge


class DroneInfo(BaseModel):
    """Fiche d'identité d'un drone dans la flotte.

    id     : identifiant unique stable (utilisé comme clé dans Angular).
    name   : nom lisible affiché dans l'interface.
    status : état opérationnel courant.
    """
    id:     str
    name:   str
    status: DroneStatus

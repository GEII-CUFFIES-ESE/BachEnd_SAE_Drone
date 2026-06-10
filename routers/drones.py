"""
Router HTTP pour la gestion de la flotte de drones et le streaming vidéo par drone.

Remplace routers/fleet.py (qui est conservé mais non enregistré dans main.py).

Flux :
    GET  /drones            ──> liste la flotte complète (DroneInfo)
    PATCH /drones/{id}      ──> met à jour la configuration d'un drone
    POST /drones/{id}/calibrate ──> déclenche une calibration simulée
    GET  /drones/{id}/video ──> flux MJPEG synthétique via VideoStreamer
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from schemas.drone import DroneInfo, DroneStatus
from services.video_streamer import VideoStreamer

router = APIRouter()

# Flotte simulée — liste mutable pour permettre les PATCH en mémoire.
_MOCK_FLEET: list[DroneInfo] = [
    DroneInfo(id="DRONE-01", name="Falcon Alpha",   status=DroneStatus.ONLINE),
    DroneInfo(id="DRONE-02", name="Falcon Bravo",   status=DroneStatus.MISSION),
    DroneInfo(id="DRONE-03", name="Falcon Charlie", status=DroneStatus.CHARGING),
    DroneInfo(id="DRONE-04", name="Falcon Delta",   status=DroneStatus.OFFLINE),
]

_streamer = VideoStreamer()


# ──────────────────────────────────────────────────────────────
# Schemas locaux (spécifiques aux opérations de configuration)
# ──────────────────────────────────────────────────────────────

class AvoidanceMode(str):
    pass


class DroneUpdateRequest(BaseModel):
    """Corps de la requête PATCH /drones/{id} — tous les champs sont optionnels."""

    avoidance_mode: str | None = Field(
        default=None,
        description="Mode d'évitement d'obstacles : 'off', 'bypass', 'brake'",
        pattern="^(off|bypass|brake)$",
    )
    rth_altitude_m: float | None = Field(
        default=None,
        ge=10.0,
        le=120.0,
        description="Altitude de retour au sol (Return To Home) en mètres",
    )
    name: str | None = Field(default=None, min_length=2)


class CalibrateRequest(BaseModel):
    """Corps de la requête POST /drones/{id}/calibrate."""

    calibration_type: str = Field(
        description="Type de calibration : 'imu', 'compass' ou 'gimbal'",
        pattern="^(imu|compass|gimbal)$",
    )


class DroneDetail(BaseModel):
    """Fiche drone étendue — retournée après PATCH pour confirmer les changements."""

    id: str
    name: str
    status: DroneStatus
    avoidance_mode: str
    rth_altitude_m: float


# État de configuration simulé en mémoire par drone_id.
_DRONE_CONFIG: dict[str, dict] = {
    "DRONE-01": {"avoidance_mode": "bypass", "rth_altitude_m": 30.0},
    "DRONE-02": {"avoidance_mode": "brake",  "rth_altitude_m": 50.0},
    "DRONE-03": {"avoidance_mode": "off",    "rth_altitude_m": 20.0},
    "DRONE-04": {"avoidance_mode": "bypass", "rth_altitude_m": 40.0},
}


def _find_drone(drone_id: str) -> DroneInfo:
    """Cherche un drone par id dans la flotte mock.

    Lève :
        404 si le drone_id n'existe pas dans la flotte.
    """
    for drone in _MOCK_FLEET:
        if drone.id == drone_id:
            return drone
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Drone '{drone_id}' introuvable dans la flotte.",
    )


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@router.get(
    "/drones",
    response_model=list[DroneInfo],
    summary="Liste de la flotte",
)
async def get_drones() -> list[DroneInfo]:
    """Retourne la liste complète des drones enregistrés dans la flotte.

    Codes HTTP : 200 OK dans tous les cas (liste vide si flotte vide).
    """
    return _MOCK_FLEET


@router.patch(
    "/drones/{drone_id}",
    response_model=DroneDetail,
    summary="Modifier la configuration d'un drone",
)
async def update_drone(drone_id: str, body: DroneUpdateRequest) -> DroneDetail:
    """Met à jour la configuration opérationnelle d'un drone.

    Accepte une mise à jour partielle (PATCH sémantique) :
    - avoidance_mode : mode d'évitement ('off', 'bypass', 'brake')
    - rth_altitude_m : altitude de retour au sol (10 à 120 m)
    - name           : nom d'affichage du drone

    Lève :
        404 si le drone_id est inconnu.
    """
    drone = _find_drone(drone_id)
    config = _DRONE_CONFIG.setdefault(drone_id, {"avoidance_mode": "bypass", "rth_altitude_m": 30.0})

    if body.avoidance_mode is not None:
        config["avoidance_mode"] = body.avoidance_mode
    if body.rth_altitude_m is not None:
        config["rth_altitude_m"] = body.rth_altitude_m
    if body.name is not None:
        drone.name = body.name  # type: ignore[assignment]

    return DroneDetail(
        id=drone.id,
        name=drone.name,
        status=drone.status,
        avoidance_mode=config["avoidance_mode"],
        rth_altitude_m=config["rth_altitude_m"],
    )


@router.post(
    "/drones/{drone_id}/calibrate",
    summary="Déclencher une calibration",
)
async def calibrate_drone(drone_id: str, body: CalibrateRequest) -> dict:
    """Déclenche une séquence de calibration simulée pour le drone indiqué.

    Types de calibration supportés :
    - imu     : centrale inertielle
    - compass : magnétomètre
    - gimbal  : stabilisateur de caméra

    Retourne le statut 'calibrating' avec les détails de la tâche.

    Lève :
        404 si le drone_id est inconnu.
    """
    _find_drone(drone_id)
    return {
        "drone_id":         drone_id,
        "status":           "calibrating",
        "calibration_type": body.calibration_type,
        "estimated_seconds": {"imu": 45, "compass": 30, "gimbal": 15}[body.calibration_type],
        "message": (
            f"Calibration '{body.calibration_type}' démarrée sur {drone_id}. "
            "Ne pas déplacer le drone pendant la procédure."
        ),
    }


@router.get(
    "/drones/{drone_id}/video",
    summary="Flux vidéo MJPEG par drone",
    response_description="Flux multipart/x-mixed-replace contenant des frames JPEG",
)
async def drone_video_stream(drone_id: str) -> StreamingResponse:
    """Retourne un flux MJPEG synthétique simulant la caméra embarquée du drone.

    Chaque frame est une image BGR 640×360 générée en mémoire via OpenCV :
    - Couleur de fond unique dérivée du drone_id
    - Overlay : identifiant du drone, horodatage, réticule FPV

    Utilisé par Angular pour le debug visuel et les tests de performance front-end.
    Affichage : <img src="http://localhost:8000/drones/DRONE-01/video">

    Lève :
        404 si le drone_id est inconnu.
    """
    _find_drone(drone_id)
    return StreamingResponse(
        _streamer.generate_mjpeg_frames(drone_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

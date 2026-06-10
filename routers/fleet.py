"""
Router HTTP pour la gestion de la flotte de drones.

Flux :
    Angular ──GET /drones──> renvoie la liste complète des drones connus du système
                          ──> Angular peuple son tableau de bord de flotte

Les données sont actuellement en mémoire (mock). Elles seront remplacées par
un appel base de données (ex: SQLAlchemy + PostgreSQL) dans une prochaine itération.
"""

from fastapi import APIRouter

from schemas.drone import DroneInfo, DroneStatus

router = APIRouter()

# Flotte simulée — source de vérité temporaire en attendant la persistance DB.
_MOCK_FLEET: list[DroneInfo] = [
    DroneInfo(id="DRONE-01", name="Falcon Alpha",  status=DroneStatus.ONLINE),
    DroneInfo(id="DRONE-02", name="Falcon Bravo",  status=DroneStatus.MISSION),
    DroneInfo(id="DRONE-03", name="Falcon Charlie", status=DroneStatus.CHARGING),
    DroneInfo(id="DRONE-04", name="Falcon Delta",  status=DroneStatus.OFFLINE),
]


@router.get("/drones", response_model=list[DroneInfo])
async def get_drones() -> list[DroneInfo]:
    """Retourne la liste complète des drones enregistrés dans la flotte.

    Réponse : tableau JSON de DroneInfo (id, name, status).
    Codes HTTP : 200 OK dans tous les cas (liste vide si flotte vide).
    """
    return _MOCK_FLEET

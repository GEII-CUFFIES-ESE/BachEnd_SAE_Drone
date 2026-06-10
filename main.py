"""
Point d'entrée de l'application FastAPI — Station de Contrôle Drone v0.2.0.

Modules enregistrés :
    /auth        ──> Authentification (login, logout, profil, reset password)
    /drones      ──> Flotte & vidéo par drone (liste, config, calibration, stream MJPEG)
    /ws          ──> Télémétrie WebSocket temps réel (sécurisé par token URL)
    /users       ──> Gestion des utilisateurs (CRUD + statut)
    /settings    ──> Paramètres globaux et politique de sécurité
    /inventory   ──> Inventaire (liste, stats agrégées, export CSV)
    /video       ──> Flux MJPEG générique legacy (<img src="/video/stream">)
    /health      ──> Healthcheck Docker/K8s
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, drones, inventory, settings, telemetry, video

app = FastAPI(
    title="Drone Control Station API",
    description=(
        "Backend de la station de contrôle de drones — "
        "Authentification, Flotte, Télémétrie WebSocket, Vidéo MJPEG, "
        "Gestion utilisateurs, Inventaire."
    ),
    version="0.2.0",
)

# Autorise l'application Angular à se connecter depuis son port de développement.
# En production, remplacer par le domaine exact du front-end.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Enregistrement des routers ─────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentification"])
app.include_router(drones.router,                         tags=["Flotte & Vidéo"])
app.include_router(telemetry.router, prefix="/ws",        tags=["Télémétrie"])
app.include_router(settings.router,                       tags=["Utilisateurs & Paramètres"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventaire"])
app.include_router(video.router,     prefix="/video",     tags=["Vidéo (legacy)"])


@app.get("/health", tags=["Santé"])
async def health_check() -> dict[str, str]:
    """Endpoint de vérification de vie — utilisé par les healthchecks Docker/K8s."""
    return {"status": "ok", "version": "0.2.0"}

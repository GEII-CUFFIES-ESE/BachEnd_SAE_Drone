"""
Service de génération Motion JPEG (MJPEG) synthétique via OpenCV + NumPy.

Flux :
    VideoStreamer.generate_mjpeg_frames(drone_id)
        ──> frame NumPy BGR 640×360 colorée selon drone_id
        ──> cv2.imencode('.jpg') ──> bytes JPEG
        ──> yield chunk multipart/x-mixed-replace
        ──> StreamingResponse dans routers/drones.py et routers/video.py

Mode simulation :
    Aucune caméra physique requise — les frames sont générées en mémoire.
    Chaque drone_id reçoit une couleur de fond unique (hash du nom) et un
    affichage de ses données simulées : ID, timestamp, mode LIVE SIMULATION.
"""

import asyncio
import time
from typing import AsyncGenerator

import cv2
import numpy as np

# Dimensions et qualité des frames simulées.
_FRAME_WIDTH  = 640
_FRAME_HEIGHT = 360
_JPEG_QUALITY = 80
_FPS          = 15


def _drone_color(drone_id: str) -> tuple[int, int, int]:
    """Dérive une couleur BGR reproductible depuis le drone_id via son hash."""
    h = hash(drone_id) & 0xFFFFFF
    r = (h >> 16) & 0xFF
    g = (h >> 8)  & 0xFF
    b = h & 0xFF
    # Assombrir pour que le texte blanc reste lisible (éviter les teintes trop claires).
    return (max(20, b // 2), max(20, g // 2), max(20, r // 2))


def _build_frame(drone_id: str) -> bytes:
    """Construit et encode en JPEG une frame de simulation pour le drone donné."""
    color = _drone_color(drone_id)
    frame = np.full((_FRAME_HEIGHT, _FRAME_WIDTH, 3), color, dtype=np.uint8)

    # Dégradé subtil pour simuler une image non-uniforme.
    gradient = np.linspace(0, 40, _FRAME_WIDTH, dtype=np.uint8)
    frame[:, :, 0] = np.clip(frame[:, :, 0] + gradient, 0, 255)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC")

    cv2.putText(frame, "LIVE SIMULATION",      (20, 40),  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 80),  2)
    cv2.putText(frame, f"Drone: {drone_id}",   (20, 90),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    cv2.putText(frame, timestamp,              (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, "SRC: mock / no feed", (20, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

    # Réticule central simulant une caméra FPV.
    cx, cy = _FRAME_WIDTH // 2, _FRAME_HEIGHT // 2
    cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 0), 1)
    cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 0), 1)
    cv2.circle(frame, (cx, cy), 30, (0, 200, 0), 1)

    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
    if not ok:
        raise RuntimeError("cv2.imencode a échoué — impossible d'encoder la frame JPEG.")
    return buffer.tobytes()


class VideoStreamer:
    """Générateur asynchrone de flux MJPEG simulé par drone."""

    async def generate_mjpeg_frames(self, drone_id: str = "DRONE-00") -> AsyncGenerator[bytes, None]:
        """Génère un flux MJPEG infini de frames synthétiques pour `drone_id`.

        Chaque itération produit un chunk multipart/x-mixed-replace conforme
        à la spec MJPEG attendue par Angular (<img src="...">) et les navigateurs.

        Args:
            drone_id: Identifiant du drone — détermine la couleur et le libellé de la frame.

        Yields:
            bytes : chunk MJPEG (boundary + headers MIME + données JPEG).
        """
        interval = 1.0 / _FPS
        while True:
            jpeg = _build_frame(drone_id)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"\r\n" + jpeg + b"\r\n"
            )
            await asyncio.sleep(interval)

"""
Router HTTP pour le flux vidéo Motion JPEG générique (route legacy).

Route : GET /video/stream
    ──> VideoStreamer.generate_mjpeg_frames() produit des chunks JPEG en continu
    ──> StreamingResponse multipart/x-mixed-replace pousse chaque frame au navigateur
    ──> Angular affiche le flux via un simple <img src="http://localhost:8000/video/stream">

Pour le flux vidéo par drone individuel, voir GET /drones/{id}/video dans routers/drones.py.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.video_streamer import VideoStreamer

router = APIRouter()

_streamer = VideoStreamer()


@router.get(
    "/stream",
    summary="Flux vidéo MJPEG générique",
    response_description="Flux multipart/x-mixed-replace contenant des frames JPEG",
)
async def video_stream() -> StreamingResponse:
    """Retourne un flux MJPEG synthétique simulant une caméra drone générique.

    Utilise VideoStreamer pour générer des frames BGR 640×360 en mémoire via OpenCV.
    Compatible navigateur et balise <img> Angular.
    """
    return StreamingResponse(
        _streamer.generate_mjpeg_frames("DRONE-00"),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

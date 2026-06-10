"""
Router HTTP pour le module inventaire.

Flux :
    GET /inventory          ──> liste brute des articles
    GET /inventory/stats    ──> agrégats calculés côté serveur (totalItems, volume, etc.)
    GET /inventory/export.csv ──> fichier CSV téléchargeable généré en mémoire

Les calculs sont centralisés ici pour décharger Angular de la logique d'agrégation.
"""

import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.inventory import InventoryItem, InventoryStats

router = APIRouter()

# ──────────────────────────────────────────────────────────────
# Mock data
# ──────────────────────────────────────────────────────────────

_MOCK_INVENTORY: list[InventoryItem] = [
    InventoryItem(id="INV-001", name="Batterie LiPo 6S",        category="Énergie",     quantity=12, volume_m3=0.002, scan_accuracy=98.5, location="Hangar A - Étagère 1"),
    InventoryItem(id="INV-002", name="Hélice 9.4x4.3 CW",       category="Propulsion",  quantity=40, volume_m3=0.001, scan_accuracy=99.1, location="Hangar A - Étagère 2"),
    InventoryItem(id="INV-003", name="Hélice 9.4x4.3 CCW",      category="Propulsion",  quantity=38, volume_m3=0.001, scan_accuracy=99.1, location="Hangar A - Étagère 2"),
    InventoryItem(id="INV-004", name="Contrôleur de vol Pixhawk",category="Électronique",quantity=4,  volume_m3=0.0005,scan_accuracy=100.0,location="Atelier - Armoire B"),
    InventoryItem(id="INV-005", name="Module GPS M8N",           category="Navigation",  quantity=6,  volume_m3=0.0002,scan_accuracy=97.3, location="Atelier - Armoire B"),
    InventoryItem(id="INV-006", name="Câble XT60 30cm",          category="Câblage",     quantity=25, volume_m3=0.0001,scan_accuracy=95.0, location="Hangar B - Bac 3"),
    InventoryItem(id="INV-007", name="Moteur 2306 2400KV",       category="Propulsion",  quantity=16, volume_m3=0.001, scan_accuracy=98.0, location="Hangar A - Étagère 3"),
    InventoryItem(id="INV-008", name="Caméra FPV 4K",            category="Capteurs",    quantity=3,  volume_m3=0.001, scan_accuracy=100.0,location="Atelier - Vitrine"),
    InventoryItem(id="INV-009", name="Régulateur 5V BEC",        category="Électronique",quantity=10, volume_m3=0.0002,scan_accuracy=96.5, location="Hangar B - Bac 1"),
    InventoryItem(id="INV-010", name="Kit de réparation carbone",category="Structure",   quantity=8,  volume_m3=0.015, scan_accuracy=92.0, location="Hangar A - Sol"),
]


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[InventoryItem],
    summary="Liste brute de l'inventaire",
)
async def get_inventory() -> list[InventoryItem]:
    """Retourne la liste complète des articles de l'inventaire sans agrégation."""
    return _MOCK_INVENTORY


@router.get(
    "/stats",
    response_model=InventoryStats,
    summary="Statistiques agrégées de l'inventaire",
)
async def get_inventory_stats() -> InventoryStats:
    """Calcule et retourne les agrégats de l'inventaire côté serveur.

    Agrégats retournés :
    - total_items      : nombre d'articles distincts
    - total_quantity   : somme des quantités de tous les articles
    - total_volume_m3  : volume total stocké en m³
    - average_accuracy : précision moyenne de scan (%)
    - categories       : dictionnaire {nom_catégorie: nombre_d_articles}
    """
    total_quantity  = sum(item.quantity for item in _MOCK_INVENTORY)
    total_volume    = round(sum(item.volume_m3 * item.quantity for item in _MOCK_INVENTORY), 4)
    avg_accuracy    = round(
        sum(item.scan_accuracy for item in _MOCK_INVENTORY) / len(_MOCK_INVENTORY), 2
    )

    categories: dict[str, int] = {}
    for item in _MOCK_INVENTORY:
        categories[item.category] = categories.get(item.category, 0) + 1

    return InventoryStats(
        total_items=len(_MOCK_INVENTORY),
        total_quantity=total_quantity,
        total_volume_m3=total_volume,
        average_accuracy=avg_accuracy,
        categories=categories,
    )


@router.get(
    "/export.csv",
    summary="Exporter l'inventaire en CSV",
    response_description="Fichier CSV téléchargeable de l'inventaire complet",
)
async def export_inventory_csv() -> StreamingResponse:
    """Génère et retourne un fichier CSV complet de l'inventaire.

    Le fichier est produit en mémoire via csv.writer + io.StringIO —
    aucune écriture disque n'est nécessaire.

    Headers CSV : id, name, category, quantity, volume_m3, scan_accuracy, location

    Utilisé par Angular pour le bouton d'export de la vue inventaire.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # En-têtes
    writer.writerow(["id", "name", "category", "quantity", "volume_m3", "scan_accuracy", "location"])

    for item in _MOCK_INVENTORY:
        writer.writerow([
            item.id,
            item.name,
            item.category,
            item.quantity,
            item.volume_m3,
            item.scan_accuracy,
            item.location,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=inventaire_drone.csv"},
    )

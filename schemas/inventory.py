"""
Schémas Pydantic pour le module inventaire.

Utilisés par /routers/inventory.py pour valider les items
et structurer les statistiques agrégées côté serveur.
"""

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """Un article de l'inventaire de la station drone."""

    id: str
    name: str
    category: str
    quantity: int = Field(ge=0)
    volume_m3: float = Field(ge=0.0)
    scan_accuracy: float = Field(ge=0.0, le=100.0, description="Précision de scan en %")
    location: str


class InventoryStats(BaseModel):
    """Agrégats de l'inventaire calculés côté serveur."""

    total_items: int
    total_quantity: int
    total_volume_m3: float
    average_accuracy: float
    categories: dict[str, int] = Field(description="Nombre d'articles par catégorie")

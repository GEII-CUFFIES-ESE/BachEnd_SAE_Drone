"""
Router HTTP pour la gestion des utilisateurs et des paramètres applicatifs.

Flux :
    GET/POST /users              ──> CRUD de la table de contrôle d'accès
    PATCH /users/{id}/status     ──> modification du statut d'un compte
    DELETE /users/{id}           ──> suppression d'un compte
    GET/PUT /settings/global     ──> paramètres généraux (entreprise, timezone, rétention)
    GET/PUT /settings/security   ──> politique de sécurité (2FA, reset forcé, timeout)

Les données sont maintenues en mémoire (mock mutable) pour la simulation.
"""

import uuid

from fastapi import APIRouter, HTTPException, status

from schemas.settings import (
    CreateUserRequest,
    GlobalSettings,
    SecuritySettings,
    UpdateUserStatusRequest,
    UserRecord,
    UserStatus,
    Role,
)

router = APIRouter()

# ──────────────────────────────────────────────────────────────
# Mock data (mutable en mémoire)
# ──────────────────────────────────────────────────────────────

_MOCK_USERS: list[UserRecord] = [
    UserRecord(
        id="USR-001",
        full_name="Administrateur Système",
        email="admin@dronesys.io",
        role=Role.ADMIN,
        status=UserStatus.ACTIVE,
    ),
    UserRecord(
        id="USR-002",
        full_name="Jean Dupont",
        email="operator@dronesys.io",
        role=Role.OPERATOR,
        status=UserStatus.ACTIVE,
    ),
    UserRecord(
        id="USR-003",
        full_name="Marie Martin",
        email="viewer@dronesys.io",
        role=Role.VIEWER,
        status=UserStatus.INACTIVE,
    ),
]

_GLOBAL_SETTINGS = GlobalSettings(
    company_name="DroneSys Industries",
    timezone="Europe/Paris",
    data_retention_days=90,
    language="fr",
)

_SECURITY_SETTINGS = SecuritySettings(
    two_factor_enabled=False,
    force_password_reset=False,
    session_timeout_minutes=60,
    max_login_attempts=5,
)


def _find_user(user_id: str) -> UserRecord:
    """Retourne l'utilisateur correspondant à user_id ou lève une 404."""
    for user in _MOCK_USERS:
        if user.id == user_id:
            return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Utilisateur '{user_id}' introuvable.",
    )


# ──────────────────────────────────────────────────────────────
# Gestion des utilisateurs
# ──────────────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserRecord],
    summary="Lister tous les utilisateurs",
)
async def list_users() -> list[UserRecord]:
    """Retourne la liste complète des utilisateurs enregistrés dans l'interface."""
    return _MOCK_USERS


@router.post(
    "/users",
    response_model=UserRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouvel utilisateur",
)
async def create_user(body: CreateUserRequest) -> UserRecord:
    """Crée un nouvel utilisateur dans la table de contrôle d'accès.

    Vérifie l'unicité de l'email avant l'insertion.

    Lève :
        409 si l'email est déjà utilisé.
    """
    for existing in _MOCK_USERS:
        if existing.email == body.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"L'email '{body.email}' est déjà associé à un compte.",
            )

    new_user = UserRecord(
        id=f"USR-{str(uuid.uuid4())[:8].upper()}",
        full_name=body.full_name,
        email=body.email,
        role=body.role,
        status=UserStatus.ACTIVE,
    )
    _MOCK_USERS.append(new_user)
    return new_user


@router.patch(
    "/users/{user_id}/status",
    response_model=UserRecord,
    summary="Modifier le statut d'un utilisateur",
)
async def update_user_status(user_id: str, body: UpdateUserStatusRequest) -> UserRecord:
    """Met à jour le statut (ACTIVE, INACTIVE, SUSPENDED) d'un utilisateur existant.

    Lève :
        404 si l'utilisateur est introuvable.
    """
    user = _find_user(user_id)
    # Pydantic v2 : les modèles sont immuables par défaut, on reconstruit l'objet.
    idx = _MOCK_USERS.index(user)
    updated = user.model_copy(update={"status": body.status})
    _MOCK_USERS[idx] = updated
    return updated


@router.delete(
    "/users/{user_id}",
    summary="Supprimer un utilisateur",
)
async def delete_user(user_id: str) -> dict[str, str]:
    """Supprime définitivement un utilisateur de la table de contrôle d'accès.

    Lève :
        404 si l'utilisateur est introuvable.
    """
    user = _find_user(user_id)
    _MOCK_USERS.remove(user)
    return {"message": f"Utilisateur '{user_id}' supprimé avec succès."}


# ──────────────────────────────────────────────────────────────
# Paramètres globaux
# ──────────────────────────────────────────────────────────────

@router.get(
    "/settings/global",
    response_model=GlobalSettings,
    summary="Lire les paramètres généraux",
)
async def get_global_settings() -> GlobalSettings:
    """Retourne les paramètres généraux courants de l'application."""
    return _GLOBAL_SETTINGS


@router.put(
    "/settings/global",
    response_model=GlobalSettings,
    summary="Mettre à jour les paramètres généraux",
)
async def update_global_settings(body: GlobalSettings) -> GlobalSettings:
    """Remplace les paramètres généraux par les valeurs fournies.

    La validation Pydantic garantit les contraintes (data_retention_days 1–3650, etc.).
    """
    global _GLOBAL_SETTINGS
    _GLOBAL_SETTINGS = body
    return _GLOBAL_SETTINGS


# ──────────────────────────────────────────────────────────────
# Paramètres de sécurité
# ──────────────────────────────────────────────────────────────

@router.get(
    "/settings/security",
    response_model=SecuritySettings,
    summary="Lire la politique de sécurité",
)
async def get_security_settings() -> SecuritySettings:
    """Retourne la politique de sécurité courante (2FA, reset forcé, timeout de session)."""
    return _SECURITY_SETTINGS


@router.put(
    "/settings/security",
    response_model=SecuritySettings,
    summary="Mettre à jour la politique de sécurité",
)
async def update_security_settings(body: SecuritySettings) -> SecuritySettings:
    """Remplace la politique de sécurité par les valeurs fournies.

    La validation Pydantic garantit les contraintes
    (session_timeout_minutes 5–1440, max_login_attempts 1–20, etc.).
    """
    global _SECURITY_SETTINGS
    _SECURITY_SETTINGS = body
    return _SECURITY_SETTINGS

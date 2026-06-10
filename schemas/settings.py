"""
Schémas Pydantic pour la gestion des utilisateurs et des paramètres globaux.

Utilisés par /routers/settings.py pour valider et sérialiser
les données de la table de contrôle d'accès et des réglages applicatifs.
"""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    """Rôles applicatifs disponibles dans l'interface de contrôle."""

    ADMIN      = "ADMIN"
    OPERATOR   = "OPERATOR"
    VIEWER     = "VIEWER"


class UserStatus(str, Enum):
    """États possibles d'un compte utilisateur."""

    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class UserRecord(BaseModel):
    """Représentation complète d'un utilisateur dans la table de contrôle d'accès."""

    id: str
    full_name: str
    email: EmailStr
    role: Role
    status: UserStatus


class CreateUserRequest(BaseModel):
    """Corps de la requête POST /users."""

    full_name: str = Field(min_length=2)
    email: EmailStr
    role: Role
    password: str = Field(min_length=8)


class UpdateUserStatusRequest(BaseModel):
    """Corps de la requête PATCH /users/{id}/status."""

    status: UserStatus


class GlobalSettings(BaseModel):
    """Paramètres généraux de l'application."""

    company_name: str
    timezone: str
    data_retention_days: int = Field(ge=1, le=3650)
    language: str = "fr"


class SecuritySettings(BaseModel):
    """Politique de sécurité de l'application."""

    two_factor_enabled: bool
    force_password_reset: bool
    session_timeout_minutes: int = Field(ge=5, le=1440)
    max_login_attempts: int = Field(ge=1, le=20)

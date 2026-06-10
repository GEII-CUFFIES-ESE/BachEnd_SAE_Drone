"""
Schémas Pydantic pour le module d'authentification.

Utilisés par /routers/auth.py pour valider les requêtes entrantes
et structurer les réponses renvoyées à Angular.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Corps de la requête POST /auth/login."""

    email: EmailStr
    password: str = Field(min_length=1)


class UserProfile(BaseModel):
    """Profil utilisateur embarqué dans la réponse de login et GET /auth/me."""

    id: str
    email: EmailStr
    full_name: str
    role: str
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    """Réponse de connexion réussie — contient le jeton d'accès et le profil."""

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class ForgotPasswordRequest(BaseModel):
    """Corps de la requête POST /auth/forgot-password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Corps de la requête POST /auth/reset-password."""

    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class MessageResponse(BaseModel):
    """Réponse générique de confirmation (logout, forgot, reset)."""

    message: str

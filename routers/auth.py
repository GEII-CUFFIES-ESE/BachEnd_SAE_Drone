"""
Router HTTP pour le module d'authentification.

Flux :
    Angular ──POST /auth/login──> valide email+password ──> retourne TokenResponse (mock JWT + profil)
            ──GET  /auth/me──>   retourne le profil de l'utilisateur connecté (sidebar Angular)
            ──POST /auth/logout──> simulation d'invalidation de session

Le jeton retourné est un mock JWT (format header.payload.signature en base64)
non cryptographiquement signé — suffisant pour peupler le front-end en développement.
"""

import base64
import json
import time

from fastapi import APIRouter, HTTPException, status

from schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter()

# Utilisateur mock — source de vérité en attendant la persistance DB.
_MOCK_ADMIN = UserProfile(
    id="USR-001",
    email="admin@dronesys.io",
    full_name="Administrateur Système",
    role="ADMIN",
    avatar_url=None,
)

# Credentials acceptés en mode simulation (email → mot de passe).
_MOCK_CREDENTIALS: dict[str, str] = {
    "admin@dronesys.io":    "admin123",
    "operator@dronesys.io": "operator123",
}


def _build_mock_jwt(email: str) -> str:
    """Construit un faux jeton JWT lisible (non signé) à des fins de développement.

    Structure : base64(header) . base64(payload) . base64(signature_vide)
    Le payload contient : sub (email), role, iat (Unix timestamp).
    """
    header  = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    payload = base64.urlsafe_b64encode(
        json.dumps({
            "sub":  email,
            "role": "ADMIN" if email == "admin@dronesys.io" else "OPERATOR",
            "iat":  int(time.time()),
            "exp":  int(time.time()) + 3600,
        }).encode()
    ).rstrip(b"=").decode()

    signature = base64.urlsafe_b64encode(b"mock-signature").rstrip(b"=").decode()

    return f"{header}.{payload}.{signature}"


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion utilisateur",
)
async def login(body: LoginRequest) -> TokenResponse:
    """Authentifie un utilisateur et retourne un jeton d'accès mock + profil.

    Valide la présence et le format de l'email et du mot de passe via Pydantic,
    puis vérifie les credentials contre le dictionnaire de simulation.

    Retourne :
        TokenResponse contenant access_token (mock JWT), token_type et UserProfile.

    Lève :
        401 si les credentials ne correspondent pas.
    """
    expected_password = _MOCK_CREDENTIALS.get(body.email)
    if expected_password is None or expected_password != body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_profile = UserProfile(
        id="USR-001" if body.email == "admin@dronesys.io" else "USR-002",
        email=body.email,
        full_name="Administrateur Système" if body.email == "admin@dronesys.io" else "Opérateur",
        role="ADMIN" if body.email == "admin@dronesys.io" else "OPERATOR",
    )

    return TokenResponse(
        access_token=_build_mock_jwt(body.email),
        token_type="bearer",
        user=user_profile,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Déconnexion utilisateur",
)
async def logout() -> MessageResponse:
    """Invalide la session courante (simulation).

    En production : révoquer le jeton dans un store Redis ou liste noire JWT.
    """
    return MessageResponse(message="Session invalidée avec succès.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Demande de réinitialisation de mot de passe",
)
async def forgot_password(body: ForgotPasswordRequest) -> MessageResponse:
    """Déclenche l'envoi simulé d'un email de réinitialisation de mot de passe.

    En production : générer un token signé à durée limitée et l'envoyer par email.
    Ici, on simule la réponse sans envoyer de message réel.
    """
    return MessageResponse(
        message=f"Un lien de réinitialisation a été envoyé à {body.email} (simulation)."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Réinitialisation du mot de passe",
)
async def reset_password(body: ResetPasswordRequest) -> MessageResponse:
    """Applique le nouveau mot de passe à partir du jeton de réinitialisation.

    Valide que le token est non-vide et que le nouveau mot de passe respecte
    la longueur minimale (8 caractères, contrôlé par Pydantic).

    En production : vérifier la signature et l'expiration du token.
    """
    if body.token != "mock-reset-token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jeton de réinitialisation invalide ou expiré.",
        )
    return MessageResponse(message="Mot de passe réinitialisé avec succès.")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Profil de l'utilisateur connecté",
)
async def get_me() -> UserProfile:
    """Retourne le profil de l'utilisateur actuellement authentifié.

    Utilisé par Angular pour peupler le bloc profil de la sidebar (nom, rôle, avatar).
    En production : extraire l'identité depuis le JWT via un middleware de dépendance.
    """
    return _MOCK_ADMIN

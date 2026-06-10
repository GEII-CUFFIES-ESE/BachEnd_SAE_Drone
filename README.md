# Drone Control Station — Backend

Backend FastAPI de la station de contrôle de drones. Fournit une API REST et un
flux WebSocket temps réel pour l'interface Angular cliente.

## Présentation du projet

Ce serveur constitue le moteur de la station de contrôle. Il expose :

- une **authentification mock** (login / logout / profil / reset password)
- la **gestion de la flotte** de drones (liste, configuration, calibration)
- un **flux de télémétrie GPS** en temps réel via WebSocket (simulation 2 Hz)
- un **flux vidéo MJPEG** synthétique généré par OpenCV par drone
- la **gestion des utilisateurs** (CRUD + statuts)
- la **configuration globale** et la **politique de sécurité** de l'application
- un **inventaire** de pièces avec export CSV

Toutes les données sont simulées en mémoire — aucune base de données n'est requise
pour faire tourner le projet en développement.

---

## Prérequis

- Python **3.11** ou supérieur
- `pip` (inclus avec Python)

---

## Installation

### 1. Cloner le dépôt

```bash
git clone <url-du-repo>
cd BachEnd_SAE_Drone
```

### 2. Créer et activer un environnement virtuel

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> **Note :** `opencv-python` compile des binaires natifs. L'installation peut prendre
> quelques minutes selon la machine.

---

## Démarrage du serveur

```bash
uvicorn main:app --reload --port 8000
```

| Option | Effet |
|--------|-------|
| `--reload` | Redémarre automatiquement à chaque modification de fichier |
| `--port 8000` | Port d'écoute (doit correspondre à la config Angular) |

Le serveur est accessible sur **http://localhost:8000**.

---

## Documentation interactive

FastAPI génère automatiquement deux interfaces de documentation :

| URL | Interface |
|-----|-----------|
| http://localhost:8000/docs | Swagger UI — test interactif de toutes les routes |
| http://localhost:8000/redoc | ReDoc — documentation lisible |

---

## Architecture du projet

```
BachEnd_SAE_Drone/
│
├── main.py                     # Point d'entrée — CORS + enregistrement des routers
│
├── schemas/                    # Contrats de données (équivalent structs C)
│   ├── auth.py                 # LoginRequest, TokenResponse, UserProfile…
│   ├── drone.py                # DroneInfo, DroneStatus
│   ├── telemetry.py            # TelemetryFrame, Position, Velocity, BatteryStatus
│   ├── inventory.py            # InventoryItem, InventoryStats
│   └── settings.py             # UserRecord, GlobalSettings, SecuritySettings…
│
├── services/                   # Logique métier réutilisable
│   ├── websocket_manager.py    # Gestionnaire de connexions WS (connect/broadcast)
│   └── video_streamer.py       # Générateur de frames MJPEG via OpenCV
│
└── routers/                    # Endpoints HTTP et WebSocket
    ├── auth.py                 # /auth/*
    ├── drones.py               # /drones/*  (flotte + vidéo par drone)
    ├── telemetry.py            # /ws/telemetry  (WebSocket)
    ├── inventory.py            # /inventory/*
    ├── settings.py             # /users/* et /settings/*
    └── video.py                # /video/stream  (flux générique legacy)
```

**Principe de séparation des couches :**

```
Requête HTTP/WS
    │
    ▼
routers/       ← valide les entrées, orchestre la réponse
    │
    ▼
services/      ← logique métier (WebSocket, vidéo, parsing MAVLink futur)
    │
    ▼
schemas/       ← contrats de données Pydantic (validation + sérialisation JSON)
```

---

## Référence des endpoints

### Authentification — `/auth`

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/auth/login` | Connexion — retourne un mock JWT + profil |
| `POST` | `/auth/logout` | Déconnexion simulée |
| `GET` | `/auth/me` | Profil de l'utilisateur connecté |
| `POST` | `/auth/forgot-password` | Envoi simulé d'un email de reset |
| `POST` | `/auth/reset-password` | Application du nouveau mot de passe |

**Credentials de test :**

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| `admin@dronesys.io` | `admin123` | ADMIN |
| `operator@dronesys.io` | `operator123` | OPERATOR |

> Ces credentials sont des données de simulation. Ne pas utiliser en production.

---

### Flotte de drones — `/drones`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/drones` | Liste complète de la flotte |
| `PATCH` | `/drones/{id}` | Modifier la config d'un drone (mode évitement, altitude RTH, nom) |
| `POST` | `/drones/{id}/calibrate` | Déclencher une calibration (`imu`, `compass`, `gimbal`) |
| `GET` | `/drones/{id}/video` | Flux MJPEG synthétique de la caméra embarquée |

**Drones disponibles en mock :** `DRONE-01`, `DRONE-02`, `DRONE-03`, `DRONE-04`

**Exemple d'affichage vidéo dans Angular :**
```html
<img src="http://localhost:8000/drones/DRONE-01/video" />
```

---

### Télémétrie WebSocket — `ws://localhost:8000/ws/telemetry`

Connexion avec un token (obligatoire) :
```
ws://localhost:8000/ws/telemetry?token=<TOKEN>
```

- Tout token non-vide est accepté en mode simulation.
- Sans token : fermeture avec code `1008 Policy Violation`.
- Le serveur envoie un paquet JSON toutes les **500 ms** :

```json
{
  "timestamp_ms": 1749600000000,
  "latitude":     49.040123,
  "longitude":    3.400456
}
```

Les coordonnées dérivent aléatoirement autour de `49.04 / 3.40` (± 0.001°, ≈ 111 m).

---

### Inventaire — `/inventory`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/inventory` | Liste brute des articles |
| `GET` | `/inventory/stats` | Agrégats (total articles, volume, précision moyenne, catégories) |
| `GET` | `/inventory/export.csv` | Export CSV téléchargeable |

---

### Utilisateurs — `/users`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/users` | Liste de tous les utilisateurs |
| `POST` | `/users` | Créer un utilisateur |
| `PATCH` | `/users/{id}/status` | Modifier le statut (`ACTIVE`, `INACTIVE`, `SUSPENDED`) |
| `DELETE` | `/users/{id}` | Supprimer un utilisateur |

---

### Paramètres — `/settings`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET/PUT` | `/settings/global` | Paramètres généraux (entreprise, timezone, rétention) |
| `GET/PUT` | `/settings/security` | Politique de sécurité (2FA, timeout, tentatives max) |

---

### Vidéo générique — `/video`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/video/stream` | Flux MJPEG pour le drone `DRONE-00` (route legacy) |

---

### Santé — `/health`

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.2.0"}
```

---

## CORS

Le middleware CORS est configuré pour autoriser exclusivement :

```
http://localhost:4200   ← port de développement Angular
```

Pour ajouter une autre origine (staging, production), modifier `main.py` :

```python
allow_origins=["http://localhost:4200", "https://mon-domaine.com"]
```

---

## Dépendances

| Package | Version | Usage |
|---------|---------|-------|
| `fastapi` | 0.115.0 | Framework web asynchrone |
| `uvicorn[standard]` | 0.30.6 | Serveur ASGI |
| `pydantic` | 2.9.2 | Validation des données et sérialisation JSON |
| `websockets` | 13.1 | Support du protocole WebSocket |
| `opencv-python` | 4.10.0.84 | Génération des frames MJPEG simulées |
| `python-multipart` | 0.0.9 | Parsing des formulaires multipart |

---

## Évolutions prévues

- Remplacement de la télémétrie simulée par un parseur **MAVLink/UDP**
- Remplacement du flux vidéo synthétique par la capture **cv2.VideoCapture** réelle
- Persistance des données via **SQLAlchemy + PostgreSQL**
- Validation des tokens WebSocket par **signature JWT** (PyJWT)
- Déploiement via **Docker Compose** (serveur + base de données)

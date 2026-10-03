# MigrationMind AI

MigrationMind AI est un projet Full-Stack professionnel de préparation et de contrôle des migrations de données ERP. Il combine une interface PHP, une API FastAPI, un moteur de mapping intelligent, des transformations explicables, un dry run sans écriture et un journal d'audit.

## Fonctionnalités

- Création et gestion de projets de migration.
- Import d'une source CSV et profilage automatique des colonnes.
- Import d'un schéma cible JSON avec types, champs requis, unicité, alias et valeurs par défaut.
- Suggestions de mapping basées sur des vecteurs TF-IDF, les alias métier, la similarité des noms et la compatibilité des types.
- Transformations configurables : découpage de nom, normalisation de téléphone, dates, nombres, booléens, casse et valeurs par défaut.
- Validation humaine champ par champ.
- Simulation complète avant exécution.
- Détection des valeurs manquantes, formats invalides et doublons.
- Génération d'un fichier CSV migré.
- Journal d'audit horodaté.
- Tests unitaires du moteur de mapping et des contrôles qualité.

## Architecture

```text
Navigateur
   |
   v
Frontend PHP 8.3 + Bootstrap 5 + JavaScript
   |
   v
API FastAPI
   |-- Profilage CSV avec pandas
   |-- Moteur de mapping intelligent
   |-- Moteur de transformations
   |-- Contrôles qualité
   |-- Audit SQLAlchemy
   |
   v
SQLite + stockage local des fichiers
```

Le projet utilise SQLite pour rester immédiatement exécutable. La couche SQLAlchemy permet de passer ensuite à PostgreSQL en modifiant `DATABASE_URL`.

## Démarrage rapide sous Windows

Avec Python et PHP disponibles dans le PATH :

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

Le script crée l'environnement Python, installe les dépendances, lance les deux serveurs et ouvre l'interface.

## Démarrage avec Docker

### Prérequis

- Docker Desktop avec Docker Compose.

### Lancer

```bash
cp .env.example .env
docker compose up --build
```

Ouvrir ensuite :

- Interface : `http://localhost:8080`
- Documentation API : `http://localhost:8000/docs`
- Santé API : `http://localhost:8000/health`

### Démonstration

1. Créer un projet.
2. Charger `demo/source_customers.csv`.
3. Charger `demo/target_schema.json`.
4. Générer le mapping intelligent.
5. Vérifier et valider chaque proposition.
6. Lancer la simulation.
7. Confirmer l'exécution.
8. Télécharger le CSV migré et consulter l'audit.

## Démarrage sans Docker

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

Depuis le dossier `frontend/public` :

```bash
php -S localhost:8080
```

Le frontend utilise par défaut `http://localhost:8000` comme URL backend.

## Tests

Depuis la racine, après activation de l'environnement virtuel :

```bash
cd backend
pytest -q
```

## Format du schéma cible

```json
{
  "entity": "customers",
  "fields": [
    {
      "name": "email",
      "label": "Adresse e-mail",
      "type": "email",
      "required": true,
      "unique": true,
      "aliases": ["mail", "courriel"]
    }
  ]
}
```

Types pris en charge :

- `string`
- `integer`
- `float`
- `date`
- `datetime`
- `email`
- `phone`
- `boolean`

## Transformations prises en charge

- `direct`
- `trim`
- `lowercase`
- `uppercase`
- `split_first`
- `split_last`
- `normalize_phone`
- `parse_date`
- `parse_datetime`
- `to_int`
- `to_float`
- `to_boolean`
- `default`

## Sécurité intégrée au MVP

- Types de fichiers limités à CSV et JSON.
- Taille maximale d'upload configurable.
- Validation Pydantic du schéma et des requêtes.
- CORS configurable.
- Aucun SQL fourni par l'utilisateur n'est exécuté.
- Exécution impossible sans validation du mapping et dry run sans erreur.
- Traçabilité des opérations critiques.
- Noms de fichiers générés côté serveur.

## Évolutions possibles pour une version entreprise

- Connecteurs MySQL, PostgreSQL, SQL Server et API REST.
- Authentification SSO et permissions par société.
- PostgreSQL, Redis et workers de migration par lots.
- Reprise sur incident et idempotence.
- Chiffrement des fichiers et coffre de secrets.
- RAG sur la documentation métier.
- Adaptateur LLM optionnel pour enrichir les explications et les règles complexes.
- Déploiement Kubernetes, métriques Prometheus et traces OpenTelemetry.

## Structure du projet

```text
migrationmind-ai/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── assets/
│   │   └── index.php
│   └── Dockerfile
├── demo/
├── storage/
├── docker-compose.yml
├── Makefile
└── README.md
```

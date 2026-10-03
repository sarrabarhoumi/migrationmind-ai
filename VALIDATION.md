# Validation technique

Le projet a été vérifié avec les contrôles suivants :

- Syntaxe PHP de `frontend/public/index.php`.
- Syntaxe JavaScript de `frontend/public/assets/app.js`.
- Compilation des modules Python.
- Trois tests unitaires du mapping, des transformations, des anomalies et des dates.
- Scénario API complet : création, import CSV, import JSON, mapping, validation, dry run, exécution, téléchargement et audit.
- Validation syntaxique YAML de `docker-compose.yml`.

Résultat du scénario de démonstration :

- 5 lignes analysées.
- 5 lignes migrées.
- 0 erreur bloquante.
- 0 avertissement.
- 7 événements d'audit.

<?php
if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}

$apiBaseUrl = getenv('API_BASE_URL') ?: 'http://localhost:8000';

// Session de démonstration. Lorsqu'un vrai login sera ajouté,
// renseignez cette variable après l'authentification.
if (!isset($_SESSION['migrationmind_user'])) {
    $_SESSION['migrationmind_user'] = [
        'name' => 'Sarra Barhoumi',
        'role' => 'Administratrice',
    ];
}

$currentUser = $_SESSION['migrationmind_user'];
$currentUserName = $currentUser['name'] ?? 'Utilisateur';
$currentUserRole = $currentUser['role'] ?? 'Membre';
$nameParts = preg_split('/\s+/', trim($currentUserName));
$userInitials = '';
foreach (array_slice($nameParts, 0, 2) as $part) {
    $userInitials .= strtoupper(substr($part, 0, 1));
}
?>
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Migration de données</title>
    <meta name="description" content="Espace de préparation, de contrôle et de migration des données.">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <link href="assets/styles.css" rel="stylesheet">
</head>
<body>
<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>

<nav class="app-navbar sticky-top" aria-label="Navigation principale">
    <div class="container-fluid px-lg-4">
        <div class="header-shell">
            <a class="app-brand" href="#" aria-label="Accueil">
                <span class="app-symbol" aria-hidden="true">
                    <i class="bi bi-database"></i>
                </span>
                <span class="brand-copy">
                    <span class="brand-name">Migration de données</span>
                    <span class="brand-subtitle">Préparation et contrôle</span>
                </span>
            </a>

            <div class="user-account" title="Utilisateur connecté">
                <span class="user-account-avatar" aria-hidden="true">
                    <i class="bi bi-person-circle"></i>
                </span>
                <span class="user-account-copy d-none d-sm-flex">
                    <strong><?= htmlspecialchars($currentUserName) ?></strong>
                    <span><?= htmlspecialchars($currentUserRole) ?></span>
                </span>
            </div>
        </div>
    </div>
</nav>

<div class="container-fluid px-lg-4 py-4">
    <div class="row g-4">
        <aside class="col-xl-3 col-lg-4">
            <div class="panel sticky-lg-top sidebar-panel">
                <div class="sidebar-header">
                    <div>
                        <div class="sidebar-kicker">
                            <i class="bi bi-grid-1x2"></i>
                            Espace de travail
                        </div>
                        <div class="sidebar-title-row">
                            <div>
                                <h4>Projets</h4>
                                <p id="projectCount">Chargement...</p>
                            </div>
                            <button class="btn sidebar-add-btn" id="newProjectBtn" title="Nouveau projet" aria-label="Créer un projet">
                                <i class="bi bi-plus-lg"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="project-section-label">
                    <span>Récents</span>
                    <i class="bi bi-clock-history"></i>
                </div>

                <div id="projectList" class="project-list"></div>

                <div class="empty-sidebar d-none" id="emptyProjectState">
                    <div class="empty-sidebar-icon"><i class="bi bi-folder-plus"></i></div>
                    <strong>Aucun projet</strong>
                    <p>Créez votre premier espace de migration.</p>
                    <button class="btn btn-sm btn-outline-primary" id="emptyCreateBtn" type="button">
                        Créer un projet
                    </button>
                </div>
            </div>
        </aside>

        <main class="col-xl-9 col-lg-8">
            <section id="welcomeView" class="welcome-card welcome-animate">
                <div class="welcome-layout">
                    <div class="welcome-content">
                        <div class="welcome-badge">
                            <i class="bi bi-shield-check"></i>
                            Migration maîtrisée
                        </div>

                        <h1>Faites évoluer vos données en toute confiance.</h1>

                        <p>
                            Préparez chaque migration avec une vision claire : correspondance des champs,
                            contrôle qualité, simulation et traçabilité complète.
                        </p>

                        <div class="welcome-actions">
                            <button class="btn btn-primary btn-lg" id="welcomeCreateBtn">
                                Créer un projet
                                <i class="bi bi-arrow-right ms-2"></i>
                            </button>
                            <span class="welcome-helper">
                                <i class="bi bi-check2-circle"></i>
                                Aucune donnée modifiée avant validation
                            </span>
                        </div>

                        <div class="welcome-features">
                            <div class="welcome-feature">
                                <i class="bi bi-diagram-3"></i>
                                <div>
                                    <strong>Mapping structuré</strong>
                                    <span>Des correspondances claires et ajustables.</span>
                                </div>
                            </div>
                            <div class="welcome-feature">
                                <i class="bi bi-clipboard2-check"></i>
                                <div>
                                    <strong>Contrôle avant import</strong>
                                    <span>Les anomalies sont détectées en amont.</span>
                                </div>
                            </div>
                            <div class="welcome-feature">
                                <i class="bi bi-journal-check"></i>
                                <div>
                                    <strong>Suivi complet</strong>
                                    <span>Chaque étape reste consultable et datée.</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="migration-preview" aria-hidden="true">
                        <div class="preview-topbar">
                            <span>Vue d’ensemble</span>
                            <span class="preview-live"><i></i> Prêt</span>
                        </div>

                        <div class="preview-flow">
                            <div class="preview-node source-node">
                                <div class="preview-node-icon"><i class="bi bi-database"></i></div>
                                <div>
                                    <span>Source</span>
                                    <strong>Ancien système</strong>
                                    <small>8 colonnes détectées</small>
                                </div>
                                <i class="bi bi-check-circle-fill node-check"></i>
                            </div>

                            <div class="preview-connector">
                                <span></span>
                                <i class="bi bi-arrow-down"></i>
                                <span></span>
                            </div>

                            <div class="preview-process">
                                <div class="process-row">
                                    <span><i class="bi bi-link-45deg"></i> Correspondances</span>
                                    <strong>8 / 8</strong>
                                </div>
                                <div class="process-progress"><span></span></div>
                                <div class="process-row muted">
                                    <span><i class="bi bi-shield-check"></i> Contrôles qualité</span>
                                    <strong>Validés</strong>
                                </div>
                            </div>

                            <div class="preview-connector">
                                <span></span>
                                <i class="bi bi-arrow-down"></i>
                                <span></span>
                            </div>

                            <div class="preview-node target-node">
                                <div class="preview-node-icon"><i class="bi bi-box-arrow-in-down"></i></div>
                                <div>
                                    <span>Destination</span>
                                    <strong>Nouvel ERP</strong>
                                    <small>Fichier prêt à importer</small>
                                </div>
                                <span class="target-ready">Prêt</span>
                            </div>
                        </div>

                        <div class="preview-footer">
                            <span><i class="bi bi-file-earmark-check"></i> Données validées</span>
                            <span>100 %</span>
                        </div>
                    </div>
                </div>
            </section>

            <section id="workspaceView" class="d-none">
                <div class="workspace-header panel mb-4">
                    <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="eyebrow">PROJET ACTIF</span>
                                <span id="projectStatusBadge" class="badge rounded-pill text-bg-secondary">Brouillon</span>
                            </div>
                            <h2 id="projectTitle" class="mb-1">Projet</h2>
                            <p id="projectDescription" class="text-secondary mb-0"></p>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-secondary" id="refreshProjectBtn"><i class="bi bi-arrow-clockwise"></i></button>
                            <button class="btn btn-outline-danger" id="deleteProjectBtn"><i class="bi bi-trash3 me-1"></i>Supprimer</button>
                        </div>
                    </div>
                </div>

                <div class="stepper panel mb-4" id="stepper">
                    <button class="step active" data-step="1"><span>1</span><small>Sources</small></button>
                    <div class="step-line"></div>
                    <button class="step" data-step="2"><span>2</span><small>Mapping IA</small></button>
                    <div class="step-line"></div>
                    <button class="step" data-step="3"><span>3</span><small>Simulation</small></button>
                    <div class="step-line"></div>
                    <button class="step" data-step="4"><span>4</span><small>Exécution</small></button>
                    <div class="step-line"></div>
                    <button class="step" data-step="5"><span>5</span><small>Audit</small></button>
                </div>

                <div id="step1" class="step-content">
                    <div class="row g-4">
                        <div class="col-xl-6">
                            <div class="panel h-100">
                                <div class="panel-heading">
                                    <div class="panel-icon"><i class="bi bi-filetype-csv"></i></div>
                                    <div><h5>Source CSV</h5><p>Données extraites de l’ancien système</p></div>
                                </div>
                                <label class="dropzone" for="sourceFile">
                                    <input type="file" id="sourceFile" accept=".csv" hidden>
                                    <i class="bi bi-cloud-arrow-up"></i>
                                    <strong>Déposer ou sélectionner un CSV</strong>
                                    <small>20 Mo maximum</small>
                                </label>
                                <div id="sourceSummary" class="mt-3"></div>
                            </div>
                        </div>
                        <div class="col-xl-6">
                            <div class="panel h-100">
                                <div class="panel-heading">
                                    <div class="panel-icon"><i class="bi bi-braces-asterisk"></i></div>
                                    <div><h5>Schéma cible JSON</h5><p>Structure attendue dans le nouvel ERP</p></div>
                                </div>
                                <label class="dropzone" for="schemaFile">
                                    <input type="file" id="schemaFile" accept=".json" hidden>
                                    <i class="bi bi-file-earmark-code"></i>
                                    <strong>Déposer ou sélectionner un JSON</strong>
                                    <small>Types, contraintes et alias métier</small>
                                </label>
                                <div id="schemaSummary" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex justify-content-end align-items-center mt-4">
                        <button class="btn btn-primary px-4" id="goMappingBtn" disabled>
                            Générer le mapping <i class="bi bi-arrow-right ms-2"></i>
                        </button>
                    </div>
                </div>

                <div id="step2" class="step-content d-none">
                    <div class="panel">
                        <div class="mapping-header">
                            <div>
                                <span class="section-kicker">Configuration</span>
                                <h4>Correspondance des champs</h4>
                            </div>
                            <div class="mapping-legend">
                                <span><i class="confidence-dot high"></i>Élevée</span>
                                <span><i class="confidence-dot medium"></i>Moyenne</span>
                                <span><i class="confidence-dot low"></i>Faible</span>
                            </div>
                        </div>
                        <div class="table-responsive mapping-table-wrap">
                            <table class="table mapping-table">
                                <thead>
                                    <tr>
                                        <th>Cible</th>
                                        <th>Source</th>
                                        <th>Traitement</th>
                                        <th class="text-center">Score</th>
                                        <th class="text-center">Valider</th>
                                    </tr>
                                </thead>
                                <tbody id="mappingTableBody"></tbody>
                            </table>
                        </div>
                        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 border-top pt-3">
                            <div id="mappingProgressText" class="text-secondary small"></div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-outline-secondary" data-go-step="1"><i class="bi bi-arrow-left me-1"></i>Retour</button>
                                <button class="btn btn-primary" id="saveMappingBtn">Valider et simuler <i class="bi bi-arrow-right ms-1"></i></button>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="step3" class="step-content d-none">
                    <div class="row g-4 mb-4">
                        <div class="col-md-3"><div class="metric-card"><span>Lignes analysées</span><strong id="metricRows">—</strong><i class="bi bi-table"></i></div></div>
                        <div class="col-md-3"><div class="metric-card success"><span>Lignes prêtes</span><strong id="metricReady">—</strong><i class="bi bi-check2-circle"></i></div></div>
                        <div class="col-md-3"><div class="metric-card danger"><span>Erreurs</span><strong id="metricErrors">—</strong><i class="bi bi-x-octagon"></i></div></div>
                        <div class="col-md-3"><div class="metric-card warning"><span>Avertissements</span><strong id="metricWarnings">—</strong><i class="bi bi-exclamation-triangle"></i></div></div>
                    </div>
                    <div class="panel mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div><h5 class="mb-1">Aperçu transformé</h5><p class="text-secondary small mb-0">Les 20 premières lignes après application des règles.</p></div>
                            <span class="badge text-bg-light border"><i class="bi bi-eye me-1"></i>Aucune écriture</span>
                        </div>
                        <div class="table-responsive"><table class="table table-sm preview-table"><thead id="previewHead"></thead><tbody id="previewBody"></tbody></table></div>
                    </div>
                    <div class="panel mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div><h5 class="mb-1">Contrôles qualité</h5><p class="text-secondary small mb-0">Contraintes, types, unicité et transformations.</p></div>
                            <span id="executionReadiness" class="badge rounded-pill text-bg-secondary">En attente</span>
                        </div>
                        <div id="issuesContainer"></div>
                    </div>
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-outline-secondary" data-go-step="2"><i class="bi bi-arrow-left me-1"></i>Modifier le mapping</button>
                        <button class="btn btn-primary" id="goExecuteBtn" disabled>Préparer l’exécution <i class="bi bi-arrow-right ms-1"></i></button>
                    </div>
                </div>

                <div id="step4" class="step-content d-none">
                    <div class="panel execution-panel">
                        <div class="execution-hero">
                            <div class="execution-icon"><i class="bi bi-database-check"></i></div>
                            <h3>Validation finale</h3>
                            <p>Vérifiez les règles validées avant de générer le fichier cible.</p>
                        </div>
                        <div class="execution-checklist">
                            <div><i class="bi bi-check-circle-fill"></i><span>Mapping validé champ par champ</span></div>
                            <div><i class="bi bi-check-circle-fill"></i><span>Transformations testées sur les données</span></div>
                            <div><i class="bi bi-check-circle-fill"></i><span>Contraintes de qualité contrôlées</span></div>
                            <div><i class="bi bi-check-circle-fill"></i><span>Événement enregistré dans l’audit</span></div>
                        </div>
                        <div class="row justify-content-center mt-4">
                            <div class="col-lg-7">
                                <input type="hidden" id="approvedBy" value="<?= htmlspecialchars($currentUserName) ?>">
                                <div class="execution-user-card">
                                    <div class="user-avatar user-avatar-sm"><?= htmlspecialchars($userInitials) ?></div>
                                    <div>
                                        <span>Exécution par</span>
                                        <strong><?= htmlspecialchars($currentUserName) ?></strong>
                                    </div>
                                </div>
                                <div class="form-check mt-3">
                                    <input class="form-check-input" type="checkbox" id="confirmExecution">
                                    <label class="form-check-label" for="confirmExecution">Je confirme l’exécution avec les règles validées.</label>
                                </div>
                                <button class="btn btn-primary btn-lg w-100 mt-4" id="executeBtn" disabled>
                                    <i class="bi bi-play-circle me-2"></i>Exécuter la migration
                                </button>
                            </div>
                        </div>
                        <div id="executionResult" class="mt-4"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-4">
                        <button class="btn btn-outline-secondary" data-go-step="3"><i class="bi bi-arrow-left me-1"></i>Retour à la simulation</button>
                        <button class="btn btn-outline-primary" id="goAuditBtn">Consulter l’audit <i class="bi bi-arrow-right ms-1"></i></button>
                    </div>
                </div>

                <div id="step5" class="step-content d-none">
                    <div class="panel">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <div><div class="eyebrow">TRAÇABILITÉ</div><h4 class="mb-1">Journal d’audit</h4><p class="text-secondary mb-0">Historique horodaté des décisions et opérations.</p></div>
                            <button class="btn btn-outline-secondary" id="refreshAuditBtn"><i class="bi bi-arrow-clockwise me-1"></i>Actualiser</button>
                        </div>
                        <div id="auditTimeline" class="audit-timeline"></div>
                    </div>
                </div>
            </section>
        </main>
    </div>
</div>

<div class="modal fade" id="projectModal" tabindex="-1" aria-labelledby="projectModalTitle" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered project-modal-dialog">
        <form class="modal-content project-modal" id="projectForm" novalidate>
            <div class="project-modal-accent" aria-hidden="true"></div>

            <div class="project-modal-header">
                <div class="project-modal-heading">
                    <span class="project-modal-icon" aria-hidden="true">
                        <i class="bi bi-folder-plus"></i>
                    </span>
                    <div>
                        <span class="project-modal-kicker">Nouveau projet</span>
                        <h3 class="modal-title" id="projectModalTitle">Créer un espace de migration</h3>
                        <p>Définissez les informations essentielles. Vous pourrez importer les données à l’étape suivante.</p>
                    </div>
                </div>

                <button type="button" class="project-modal-close" data-bs-dismiss="modal" aria-label="Fermer">
                    <i class="bi bi-x-lg" aria-hidden="true"></i>
                </button>
            </div>

            <div class="project-modal-body">
                <div class="project-form-section">
                    <div class="project-form-section-title">
                        <div>
                            <span>Informations générales</span>
                            <small>Identifiez clairement le périmètre de la migration.</small>
                        </div>
                        <span class="required-note"><i class="bi bi-asterisk"></i> Obligatoire</span>
                    </div>

                    <div class="project-form-group">
                        <label class="project-form-label" for="projectName">
                            Nom du projet
                            <span aria-hidden="true">*</span>
                        </label>
                        <div class="project-input-wrap">
                            <i class="bi bi-folder project-input-icon" aria-hidden="true"></i>
                            <input
                                class="form-control project-form-control"
                                id="projectName"
                                name="projectName"
                                minlength="3"
                                maxlength="150"
                                required
                                autocomplete="off"
                                placeholder="Ex. Migration clients vers le nouvel ERP"
                                aria-describedby="projectNameHelp projectNameCount"
                            >
                        </div>
                        <div class="project-field-meta">
                            <small id="projectNameHelp">Choisissez un nom court, précis et facilement identifiable.</small>
                            <span id="projectNameCount">0 / 150</span>
                        </div>
                        <div class="invalid-feedback">Saisissez un nom d’au moins 3 caractères.</div>
                    </div>

                    <div class="project-form-group">
                        <label class="project-form-label" for="projectDesc">Description</label>
                        <textarea
                            class="form-control project-form-control project-form-textarea"
                            id="projectDesc"
                            name="projectDesc"
                            rows="4"
                            maxlength="1000"
                            placeholder="Précisez la source, la cible et l’objectif principal de la migration."
                            aria-describedby="projectDescHelp projectDescCount"
                        ></textarea>
                        <div class="project-field-meta">
                            <small id="projectDescHelp">Facultatif, mais utile pour documenter le contexte du projet.</small>
                            <span id="projectDescCount">0 / 1000</span>
                        </div>
                    </div>
                </div>

                <div class="project-modal-note">
                    <span class="project-modal-note-icon" aria-hidden="true">
                        <i class="bi bi-shield-check"></i>
                    </span>
                    <div>
                        <strong>Création sans impact sur les données</strong>
                        <p>Le projet est initialisé en mode brouillon. Aucun fichier n’est traité avant votre import et votre validation.</p>
                    </div>
                </div>
            </div>

            <div class="project-modal-footer">
                <button type="button" class="btn project-modal-cancel" data-bs-dismiss="modal">Annuler</button>
                <button type="submit" class="btn btn-primary project-modal-submit">
                    <i class="bi bi-plus-lg" aria-hidden="true"></i>
                    Créer le projet
                </button>
            </div>
        </form>
    </div>
</div>

<script>window.API_BASE_URL = <?= json_encode($apiBaseUrl, JSON_UNESCAPED_SLASHES) ?>;</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="assets/app.js"></script>
</body>
</html>

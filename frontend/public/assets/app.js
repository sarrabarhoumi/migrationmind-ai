const API = window.API_BASE_URL.replace(/\/$/, '');

const state = {
    projects: [],
    activeProjectId: null,
    projectData: null,
    currentStep: 1,
    mappings: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const projectModalElement = $('#projectModal');
const projectForm = $('#projectForm');
const projectNameInput = $('#projectName');
const projectDescInput = $('#projectDesc');
const projectNameGroup = projectNameInput.closest('.project-form-group');
const projectModal = new bootstrap.Modal(projectModalElement);

const transformations = [
    ['direct', 'Direct'], ['trim', 'Nettoyer les espaces'], ['lowercase', 'Minuscules'],
    ['uppercase', 'Majuscules'], ['split_first', 'Extraire le prénom'], ['split_last', 'Extraire le nom'],
    ['normalize_phone', 'Normaliser téléphone'], ['parse_date', 'Convertir en date'],
    ['parse_datetime', 'Convertir en date/heure'], ['to_int', 'Convertir en entier'],
    ['to_float', 'Convertir en décimal'], ['to_boolean', 'Convertir en booléen'], ['default', 'Valeur par défaut']
];

const statusLabels = {
    draft: ['Brouillon', 'secondary'], source_ready: ['Source prête', 'info'], schema_ready: ['Schéma prêt', 'info'],
    mapping_ready: ['Mapping prêt', 'primary'], dry_run_ready: ['Simulation prête', 'warning'], completed: ['Terminée', 'success']
};

const auditLabels = {
    PROJECT_CREATED: ['Projet créé', 'bi-folder-plus'], SOURCE_UPLOADED: ['Source importée', 'bi-filetype-csv'],
    TARGET_SCHEMA_UPLOADED: ['Schéma cible importé', 'bi-braces'], MAPPING_SUGGESTED: ['Mapping suggéré par le moteur IA', 'bi-magic'],
    MAPPING_UPDATED: ['Mapping validé', 'bi-check2-square'], DRY_RUN_COMPLETED: ['Simulation terminée', 'bi-flask'],
    MIGRATION_EXECUTED: ['Migration exécutée', 'bi-rocket-takeoff']
};

async function api(path, options = {}) {
    const config = { ...options, headers: { ...(options.headers || {}) } };
    if (config.body && !(config.body instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
        config.body = JSON.stringify(config.body);
    }
    const response = await fetch(`${API}${path}`, config);
    if (!response.ok) {
        let payload;
        try { payload = await response.json(); } catch { payload = { detail: response.statusText }; }
        const detail = typeof payload.detail === 'string' ? payload.detail : payload.detail?.message || JSON.stringify(payload.detail);
        throw new Error(detail || 'Une erreur est survenue');
    }
    if (response.status === 204) return null;
    return response.json();
}

function toast(message, type = 'success') {
    const id = `toast-${Date.now()}`;
    const icon = type === 'success' ? 'bi-check-circle-fill' : type === 'warning' ? 'bi-exclamation-triangle-fill' : 'bi-x-circle-fill';
    const html = `<div id="${id}" class="toast align-items-center border-0 shadow" role="alert">
        <div class="d-flex"><div class="toast-body"><i class="bi ${icon} me-2 text-${type}"></i>${escapeHtml(message)}</div>
        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
    $('#toastContainer').insertAdjacentHTML('beforeend', html);
    const element = document.getElementById(id);
    const instance = new bootstrap.Toast(element, { delay: 4200 });
    instance.show();
    element.addEventListener('hidden.bs.toast', () => element.remove());
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[char]));
}

function playWelcomeAnimations() {
    const welcome = $('#welcomeView');
    if (!welcome || welcome.classList.contains('d-none')) return;

    welcome.classList.remove('welcome-animate');
    void welcome.offsetWidth;
    welcome.classList.add('welcome-animate');
}

function setBusy(element, busy, label = 'Traitement...') {
    if (!element) return;
    if (busy) {
        element.dataset.originalHtml = element.innerHTML;
        element.disabled = true;
        element.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${label}`;
    } else {
        element.disabled = false;
        if (element.dataset.originalHtml) element.innerHTML = element.dataset.originalHtml;
    }
}

async function checkHealth() {
    try {
        await api('/health');
    } catch {
        toast('Le serveur de traitement est indisponible. Vérifiez le lancement du projet.', 'danger');
    }
}

async function loadProjects(selectId = null) {
    state.projects = await api('/api/projects');
    renderProjectList();
    if (selectId) await selectProject(selectId);
    else if (state.activeProjectId && state.projects.some(p => p.id === state.activeProjectId)) await selectProject(state.activeProjectId, false);
}

function renderProjectList() {
    const list = $('#projectList');
    const emptyState = $('#emptyProjectState');
    const projectCount = $('#projectCount');

    list.innerHTML = '';
    emptyState.classList.toggle('d-none', state.projects.length > 0);

    if (projectCount) {
        const count = state.projects.length;
        projectCount.textContent = count === 0
            ? 'Aucun projet enregistré'
            : `${count} projet${count > 1 ? 's' : ''} enregistré${count > 1 ? 's' : ''}`;
    }

    state.projects.forEach(project => {
        const [statusLabel] = statusLabels[project.status] || [project.status];
        const statusClass = String(project.status || 'draft').replace(/_/g, '-');
        const date = new Date(project.updated_at);
        const formattedDate = Number.isNaN(date.getTime())
            ? 'Date indisponible'
            : date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            }).replace('.', '');

        const div = document.createElement('div');
        div.className = `project-item ${project.id === state.activeProjectId ? 'active' : ''}`;
        div.dataset.id = project.id;
        div.setAttribute('role', 'button');
        div.setAttribute('tabindex', '0');
        div.setAttribute('aria-label', `Ouvrir le projet ${project.name}`);

        div.innerHTML = `
            <div class="project-item-main">
                <div class="project-item-icon">
                    <i class="bi bi-database"></i>
                </div>
                <div class="project-item-copy">
                    <h6>${escapeHtml(project.name)}</h6>
                    <span>Migration de données</span>
                </div>
                <i class="bi bi-chevron-right project-item-arrow"></i>
            </div>
            <div class="project-item-meta">
                <span class="project-status project-status-${escapeHtml(statusClass)}">
                    <i></i>${escapeHtml(statusLabel)}
                </span>
                <time datetime="${escapeHtml(project.updated_at)}">
                    <i class="bi bi-calendar3"></i>${escapeHtml(formattedDate)}
                </time>
            </div>`;

        div.addEventListener('click', () => selectProject(project.id));
        div.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                selectProject(project.id);
            }
        });
        list.appendChild(div);
    });
}

async function selectProject(id, resetStep = true) {
    state.activeProjectId = Number(id);
    state.projectData = await api(`/api/projects/${id}`);
    state.mappings = state.projectData.mapping || [];
    $('#welcomeView').classList.add('d-none');
    $('#workspaceView').classList.remove('d-none');
    renderProjectList();
    renderProjectHeader();
    renderSourceSummary();
    renderSchemaSummary();
    updateSourceNextButton();
    if (resetStep) {
        let step = 1;
        const status = state.projectData.project.status;
        if (status === 'mapping_ready') step = 2;
        if (status === 'dry_run_ready') step = 3;
        if (status === 'completed') step = 4;
        goToStep(step);
    } else {
        goToStep(state.currentStep);
    }
}

function renderProjectHeader() {
    const project = state.projectData.project;
    $('#projectTitle').textContent = project.name;
    $('#projectDescription').textContent = project.description || 'Migration intelligente de données métier.';
    const [label, style] = statusLabels[project.status] || [project.status, 'secondary'];
    $('#projectStatusBadge').className = `badge rounded-pill text-bg-${style}`;
    $('#projectStatusBadge').textContent = label;
}

function goToStep(step) {
    state.currentStep = Number(step);
    $$('.step-content').forEach(el => el.classList.add('d-none'));
    $(`#step${step}`).classList.remove('d-none');
    $$('.step').forEach(button => {
        const n = Number(button.dataset.step);
        button.classList.toggle('active', n === step);
        button.classList.toggle('done', n < step);
    });
    if (step === 2) renderMapping();
    if (step === 3 && state.projectData?.dry_run) renderDryRun(state.projectData.dry_run);
    if (step === 5) loadAudit();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderSourceSummary() {
    const profile = state.projectData?.source_profile;
    if (!profile) { $('#sourceSummary').innerHTML = ''; return; }
    const tags = profile.columns.slice(0, 8).map(c => `<span class="summary-tag">${escapeHtml(c.name)} · ${escapeHtml(c.inferred_type)}</span>`).join('');
    $('#sourceSummary').innerHTML = `<div class="summary-card"><div class="summary-top"><div><i class="bi bi-check-circle-fill text-success me-2"></i><strong>${escapeHtml(profile.filename)}</strong></div><span class="badge text-bg-light border">${profile.row_count} lignes</span></div><div class="summary-tags">${tags}${profile.columns.length > 8 ? `<span class="summary-tag">+${profile.columns.length - 8}</span>` : ''}</div></div>`;
}

function renderSchemaSummary() {
    const schema = state.projectData?.target_schema;
    if (!schema) { $('#schemaSummary').innerHTML = ''; return; }
    const required = schema.fields.filter(f => f.required).length;
    const tags = schema.fields.slice(0, 8).map(f => `<span class="summary-tag">${escapeHtml(f.name)} · ${escapeHtml(f.type)}</span>`).join('');
    $('#schemaSummary').innerHTML = `<div class="summary-card"><div class="summary-top"><div><i class="bi bi-check-circle-fill text-success me-2"></i><strong>${escapeHtml(schema.entity)}</strong></div><span class="badge text-bg-light border">${schema.fields.length} champs · ${required} requis</span></div><div class="summary-tags">${tags}${schema.fields.length > 8 ? `<span class="summary-tag">+${schema.fields.length - 8}</span>` : ''}</div></div>`;
}

function updateSourceNextButton() {
    $('#goMappingBtn').disabled = !(state.projectData?.source_profile && state.projectData?.target_schema);
}

async function uploadFile(kind, input) {
    if (!input.files?.[0] || !state.activeProjectId) return;
    const file = input.files[0];
    const form = new FormData();
    form.append('file', file);
    const endpoint = kind === 'source' ? 'source' : 'target-schema';
    input.closest('.dropzone').classList.add('loading-overlay');
    try {
        await api(`/api/projects/${state.activeProjectId}/${endpoint}`, { method: 'POST', body: form });
        toast(kind === 'source' ? 'Source analysée avec succès.' : 'Schéma cible validé.');
        await selectProject(state.activeProjectId, false);
    } catch (error) {
        toast(error.message, 'danger');
    } finally {
        input.closest('.dropzone').classList.remove('loading-overlay');
        input.value = '';
    }
}

async function generateMapping() {
    const button = $('#goMappingBtn');
    setBusy(button, true, 'Analyse...');
    try {
        const result = await api(`/api/projects/${state.activeProjectId}/suggest-mapping`, { method: 'POST' });
        state.mappings = result.mappings;
        await selectProject(state.activeProjectId, false);
        goToStep(2);
        toast('Mapping intelligent généré. Vérifiez les propositions.');
    } catch (error) { toast(error.message, 'danger'); }
    finally { setBusy(button, false); }
}

function renderMapping() {
    if (!state.projectData?.target_schema) return;
    const sourceColumns = state.projectData.source_profile?.columns || [];
    const targetFields = state.projectData.target_schema.fields || [];
    const body = $('#mappingTableBody');
    body.innerHTML = '';

    targetFields.forEach(field => {
        let mapping = state.mappings.find(m => m.target_field === field.name);
        if (!mapping) mapping = { target_field: field.name, source_field: null, transformation: 'direct', confidence: 0, explanation: '', approved: false };
        const sourceOptions = ['<option value="">Non mappé</option>', ...sourceColumns.map(c => `<option value="${escapeHtml(c.name)}" ${mapping.source_field === c.name ? 'selected' : ''}>${escapeHtml(c.name)} (${escapeHtml(c.inferred_type)})</option>`)].join('');
        const transformOptions = transformations.map(([value, label]) => `<option value="${value}" ${mapping.transformation === value ? 'selected' : ''}>${label}</option>`).join('');
        const confidence = Math.round((mapping.confidence || 0) * 100);
        const level = confidence >= 85 ? 'high' : confidence >= 60 ? 'medium' : 'low';
        const row = document.createElement('tr');
        row.dataset.target = field.name;
        row.innerHTML = `<td class="mapping-target-cell">
                <div class="mapping-field-label">${escapeHtml(field.label || field.name)} ${field.required ? '<span class="text-danger">*</span>' : ''}</div>
                <span class="mapping-field-meta">${escapeHtml(field.name)} · ${escapeHtml(field.type)}</span>
            </td>
            <td><select class="form-select mapping-source" aria-label="Champ source pour ${escapeHtml(field.name)}">${sourceOptions}</select></td>
            <td><select class="form-select mapping-transform" aria-label="Transformation pour ${escapeHtml(field.name)}">${transformOptions}</select></td>
            <td class="text-center"><span class="confidence-badge ${level}" title="${escapeHtml(mapping.explanation || 'Score de correspondance')}">${confidence}%</span></td>
            <td class="text-center"><div class="form-check form-switch mapping-switch"><input class="form-check-input mapping-approved" type="checkbox" aria-label="Valider ${escapeHtml(field.name)}" ${mapping.approved ? 'checked' : ''}></div></td>`;
        body.appendChild(row);
    });

    $$('.mapping-source, .mapping-transform, .mapping-approved').forEach(el => el.addEventListener('change', updateMappingProgress));
    updateMappingProgress();
}

function collectMappings() {
    return $$('#mappingTableBody tr').map(row => {
        const original = state.mappings.find(m => m.target_field === row.dataset.target) || {};
        return {
            target_field: row.dataset.target,
            source_field: row.querySelector('.mapping-source').value || null,
            transformation: row.querySelector('.mapping-transform').value,
            confidence: Number(original.confidence || 0),
            explanation: original.explanation || 'Mapping ajusté manuellement.',
            approved: row.querySelector('.mapping-approved').checked,
        };
    });
}

function updateMappingProgress() {
    const mappings = collectMappings();
    const approved = mappings.filter(m => m.approved).length;
    const unmapped = mappings.filter(m => !m.source_field && m.transformation !== 'default').length;
    $('#mappingProgressText').innerHTML = `<strong>${approved}/${mappings.length}</strong> champs validés${unmapped ? ` · <span class="text-danger">${unmapped} non mappé(s)</span>` : ''}`;
}

async function saveMappingAndDryRun() {
    const button = $('#saveMappingBtn');
    const mappings = collectMappings();
    const invalid = mappings.filter(m => !m.approved || (!m.source_field && m.transformation !== 'default'));
    if (invalid.length) {
        toast('Validez chaque mapping et choisissez une source ou une valeur par défaut.', 'warning');
        return;
    }
    setBusy(button, true, 'Simulation...');
    try {
        await api(`/api/projects/${state.activeProjectId}/mapping`, { method: 'PUT', body: { mappings } });
        const result = await api(`/api/projects/${state.activeProjectId}/dry-run`, { method: 'POST', body: { row_limit: 5000 } });
        await selectProject(state.activeProjectId, false);
        state.projectData.dry_run = result;
        renderDryRun(result);
        goToStep(3);
        toast('Simulation terminée. Aucune donnée cible n’a été écrite.');
    } catch (error) { toast(error.message, 'danger'); }
    finally { setBusy(button, false); }
}

function renderDryRun(result) {
    $('#metricRows').textContent = result.rows_analyzed;
    $('#metricReady').textContent = result.rows_ready;
    $('#metricErrors').textContent = result.error_count;
    $('#metricWarnings').textContent = result.warning_count;
    renderPreview(result.preview || []);
    renderIssues(result.issues || []);
    $('#goExecuteBtn').disabled = !result.can_execute;
    $('#executionReadiness').className = `badge rounded-pill text-bg-${result.can_execute ? 'success' : 'danger'}`;
    $('#executionReadiness').textContent = result.can_execute ? 'Prête à exécuter' : 'Corrections requises';
}

function renderPreview(rows) {
    if (!rows.length) { $('#previewHead').innerHTML = ''; $('#previewBody').innerHTML = '<tr><td>Aucune donnée</td></tr>'; return; }
    const columns = Object.keys(rows[0]);
    $('#previewHead').innerHTML = `<tr>${columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;
    $('#previewBody').innerHTML = rows.map(row => `<tr>${columns.map(c => `<td>${escapeHtml(row[c] ?? '—')}</td>`).join('')}</tr>`).join('');
}

function renderIssues(issues) {
    const container = $('#issuesContainer');
    if (!issues.length) {
        container.innerHTML = `<div class="no-issues"><i class="bi bi-check-circle-fill"></i><h5 class="mt-2">Aucune anomalie bloquante</h5><p class="mb-0">Les données satisfont le schéma cible et les règles validées.</p></div>`;
        return;
    }
    container.innerHTML = issues.slice(0, 100).map(issue => {
        const severity = issue.severity || 'error';
        const icon = severity === 'warning' ? 'bi-exclamation-triangle' : 'bi-x-octagon';
        return `<div class="issue-item"><div class="issue-icon ${severity}"><i class="bi ${icon}"></i></div><div class="issue-body"><strong>${escapeHtml(issue.code)} · ${escapeHtml(issue.field || 'global')}</strong><p>${issue.row ? `Ligne ${issue.row} · ` : ''}${escapeHtml(issue.message)}</p></div></div>`;
    }).join('');
}

async function executeMigration() {
    const button = $('#executeBtn');
    const approvedBy = $('#approvedBy').value.trim();
    if (!approvedBy) { toast('Indiquez le nom de la personne qui valide.', 'warning'); return; }
    setBusy(button, true, 'Exécution...');
    try {
        const result = await api(`/api/projects/${state.activeProjectId}/execute`, { method: 'POST', body: { approved_by: approvedBy } });
        $('#executionResult').innerHTML = `<div class="result-success"><i class="bi bi-check-circle-fill text-success fs-2"></i><h4 class="mt-2">Migration terminée</h4><p>${result.rows_migrated} lignes ont été transformées et exportées.</p><a class="btn btn-success" href="${API}${result.download_url}"><i class="bi bi-download me-2"></i>Télécharger le CSV migré</a></div>`;
        await selectProject(state.activeProjectId, false);
        toast('Migration exécutée et audit enregistrée.');
    } catch (error) { toast(error.message, 'danger'); }
    finally { setBusy(button, false); }
}

async function loadAudit() {
    if (!state.activeProjectId) return;
    const container = $('#auditTimeline');
    container.innerHTML = '<div class="text-secondary">Chargement...</div>';
    try {
        const events = await api(`/api/projects/${state.activeProjectId}/audit`);
        if (!events.length) { container.innerHTML = '<div class="text-secondary">Aucun événement.</div>'; return; }
        container.innerHTML = events.map(event => {
            const [label, icon] = auditLabels[event.action] || [event.action, 'bi-circle'];
            const details = Object.entries(event.details || {}).map(([k,v]) => `<strong>${escapeHtml(k)}:</strong> ${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : v)}`).join(' · ');
            return `<div class="audit-item"><h6><i class="bi ${icon} me-2 text-primary"></i>${escapeHtml(label)}</h6><time>${new Date(event.created_at).toLocaleString('fr-FR')}</time>${details ? `<div class="audit-details">${details}</div>` : ''}</div>`;
        }).join('');
    } catch (error) { container.innerHTML = `<div class="alert alert-danger">${escapeHtml(error.message)}</div>`; }
}

async function deleteProject() {
    if (!state.activeProjectId || !confirm('Supprimer définitivement ce projet et ses fichiers ?')) return;
    try {
        await api(`/api/projects/${state.activeProjectId}`, { method: 'DELETE' });
        state.activeProjectId = null;
        state.projectData = null;
        $('#workspaceView').classList.add('d-none');
        $('#welcomeView').classList.remove('d-none');
        playWelcomeAnimations();
        await loadProjects();
        toast('Projet supprimé.');
    } catch (error) { toast(error.message, 'danger'); }
}

function updateProjectFieldCounter(input, counterSelector) {
    const counter = $(counterSelector);
    if (!input || !counter) return;
    counter.textContent = `${input.value.length} / ${input.maxLength}`;
}

function resetProjectModalForm() {
    projectForm.reset();
    projectNameInput.classList.remove('is-invalid');
    projectNameGroup.classList.remove('has-error');
    updateProjectFieldCounter(projectNameInput, '#projectNameCount');
    updateProjectFieldCounter(projectDescInput, '#projectDescCount');
}

function openProjectModal() {
    resetProjectModalForm();
    projectModal.show();
}

$('#newProjectBtn').addEventListener('click', openProjectModal);
$('#welcomeCreateBtn').addEventListener('click', openProjectModal);
$('#emptyCreateBtn')?.addEventListener('click', openProjectModal);

projectNameInput.addEventListener('input', () => {
    updateProjectFieldCounter(projectNameInput, '#projectNameCount');
    if (projectNameInput.value.trim().length >= 3) {
        projectNameInput.classList.remove('is-invalid');
        projectNameGroup.classList.remove('has-error');
    }
});

projectDescInput.addEventListener('input', () => {
    updateProjectFieldCounter(projectDescInput, '#projectDescCount');
});

projectModalElement.addEventListener('shown.bs.modal', () => {
    projectNameInput.focus();
});

projectModalElement.addEventListener('hidden.bs.modal', resetProjectModalForm);

projectForm.addEventListener('submit', async event => {
    event.preventDefault();

    const projectName = projectNameInput.value.trim();
    if (projectName.length < 3) {
        projectNameInput.classList.add('is-invalid');
        projectNameGroup.classList.add('has-error');
        projectNameInput.focus();
        return;
    }

    const submit = event.submitter;
    setBusy(submit, true, 'Création...');
    try {
        const project = await api('/api/projects', {
            method: 'POST',
            body: {
                name: projectName,
                description: projectDescInput.value.trim() || null,
            },
        });
        projectModal.hide();
        await loadProjects(project.id);
        toast('Projet créé. Ajoutez maintenant la source et le schéma cible.');
    } catch (error) {
        toast(error.message, 'danger');
    } finally {
        setBusy(submit, false);
    }
});

$('#sourceFile').addEventListener('change', event => uploadFile('source', event.target));
$('#schemaFile').addEventListener('change', event => uploadFile('schema', event.target));
$('#goMappingBtn').addEventListener('click', generateMapping);
$('#saveMappingBtn').addEventListener('click', saveMappingAndDryRun);
$('#goExecuteBtn').addEventListener('click', () => goToStep(4));
$('#confirmExecution').addEventListener('change', event => $('#executeBtn').disabled = !event.target.checked);
$('#executeBtn').addEventListener('click', executeMigration);
$('#goAuditBtn').addEventListener('click', () => goToStep(5));
$('#refreshAuditBtn').addEventListener('click', loadAudit);
$('#refreshProjectBtn').addEventListener('click', () => selectProject(state.activeProjectId, false));
$('#deleteProjectBtn').addEventListener('click', deleteProject);
$$('[data-go-step]').forEach(button => button.addEventListener('click', () => goToStep(button.dataset.goStep)));
$$('.step').forEach(button => button.addEventListener('click', () => goToStep(button.dataset.step)));

(async function init() {
    await checkHealth();
    try {
        await loadProjects();
        playWelcomeAnimations();
    } catch (error) {
        toast(error.message, 'danger');
    }
})();

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import AuditEvent, Project
from .schemas import DryRunRequest, ExecuteRequest, MappingUpdate, ProjectCreate, ProjectOut, TargetSchema
from .services.anomaly_engine import detect_anomalies
from .services.audit import record_audit
from .services.mapping_engine import suggest_mapping
from .services.profiler import profile_csv
from .services.transformation_engine import transform_dataframe


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Plateforme intelligente de préparation, simulation et audit des migrations de données.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


def load_json(value: str | None, fallback):
    return json.loads(value) if value else fallback


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return list(db.scalars(select(Project).order_by(Project.updated_at.desc())).all())


@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    record_audit(db, project.id, "PROJECT_CREATED", {"name": project.name})
    return project


@app.get("/api/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    return {
        "project": ProjectOut.model_validate(project),
        "source_profile": load_json(project.source_profile_json, None),
        "target_schema": load_json(project.target_schema_json, None),
        "mapping": load_json(project.mapping_json, []),
        "dry_run": load_json(project.dry_run_json, None),
    }


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    for path_value in (project.source_file, project.output_file):
        if path_value:
            Path(path_value).unlink(missing_ok=True)
    db.delete(project)
    db.commit()


@app.post("/api/projects/{project_id}/source")
def upload_source(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".csv":
        raise HTTPException(status_code=400, detail="Le MVP accepte les sources CSV uniquement.")

    destination = settings.storage_dir / "uploads" / f"project-{project_id}-{uuid.uuid4().hex}.csv"
    with destination.open("wb") as target:
        shutil.copyfileobj(file.file, target)

    if destination.stat().st_size > settings.max_upload_mb * 1024 * 1024:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="Fichier trop volumineux")

    try:
        profile = profile_csv(destination)
        profile["filename"] = file.filename or destination.name
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"CSV invalide: {exc}") from exc

    if project.source_file:
        Path(project.source_file).unlink(missing_ok=True)
    project.source_file = str(destination)
    project.source_profile_json = json.dumps(profile, ensure_ascii=False)
    project.mapping_json = None
    project.dry_run_json = None
    project.status = "source_ready"
    db.commit()
    record_audit(db, project.id, "SOURCE_UPLOADED", {"filename": file.filename, "profile": profile})
    return profile


@app.post("/api/projects/{project_id}/target-schema")
def upload_target_schema(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    if Path(file.filename or "").suffix.lower() != ".json":
        raise HTTPException(status_code=400, detail="Le schéma cible doit être un fichier JSON.")

    try:
        payload = json.loads(file.file.read().decode("utf-8"))
        schema = TargetSchema.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Schéma JSON invalide: {exc}") from exc

    project.target_schema_json = schema.model_dump_json()
    project.mapping_json = None
    project.dry_run_json = None
    project.status = "schema_ready" if project.source_file else "draft"
    db.commit()
    record_audit(db, project.id, "TARGET_SCHEMA_UPLOADED", {"entity": schema.entity, "fields": len(schema.fields)})
    return schema.model_dump()


@app.post("/api/projects/{project_id}/suggest-mapping")
def generate_mapping(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    profile = load_json(project.source_profile_json, None)
    schema = load_json(project.target_schema_json, None)
    if not profile or not schema:
        raise HTTPException(status_code=409, detail="Chargez une source CSV et un schéma cible avant le mapping.")

    mappings = suggest_mapping(profile, schema)
    project.mapping_json = json.dumps(mappings, ensure_ascii=False)
    project.status = "mapping_ready"
    db.commit()
    record_audit(
        db,
        project.id,
        "MAPPING_SUGGESTED",
        {"fields": len(mappings), "auto_approved": sum(1 for item in mappings if item["approved"])},
    )
    return {"mappings": mappings}


@app.put("/api/projects/{project_id}/mapping")
def update_mapping(project_id: int, payload: MappingUpdate, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    schema = load_json(project.target_schema_json, None)
    if not schema:
        raise HTTPException(status_code=409, detail="Schéma cible manquant")

    expected = {field["name"] for field in schema["fields"]}
    received = {item.target_field for item in payload.mappings}
    if expected != received:
        raise HTTPException(status_code=400, detail="Le mapping doit contenir exactement tous les champs cibles.")

    serialized = [item.model_dump() for item in payload.mappings]
    project.mapping_json = json.dumps(serialized, ensure_ascii=False)
    project.dry_run_json = None
    project.status = "mapping_ready"
    db.commit()
    record_audit(db, project.id, "MAPPING_UPDATED", {"approved": sum(1 for item in serialized if item["approved"])})
    return {"mappings": serialized}


@app.post("/api/projects/{project_id}/dry-run")
def dry_run(project_id: int, payload: DryRunRequest, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    schema = load_json(project.target_schema_json, None)
    mappings = load_json(project.mapping_json, [])
    if not project.source_file or not schema or not mappings:
        raise HTTPException(status_code=409, detail="Source, schéma ou mapping manquant.")

    if any(not item.get("approved") for item in mappings):
        raise HTTPException(status_code=409, detail="Tous les champs du mapping doivent être validés avant la simulation.")

    dataframe = pd.read_csv(project.source_file, dtype=object, keep_default_na=True, nrows=payload.row_limit)
    transformed, transform_errors = transform_dataframe(dataframe, schema, mappings)
    issues = transform_errors + detect_anomalies(transformed, schema)
    error_count = sum(1 for issue in issues if issue.get("severity", "error") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")

    preview = transformed.head(20).where(pd.notnull(transformed.head(20)), None).to_dict(orient="records")
    result = {
        "rows_analyzed": int(len(dataframe)),
        "rows_ready": max(0, int(len(dataframe)) - len({i.get("row") for i in issues if i.get("row") and i.get("severity", "error") == "error"})),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues[:500],
        "preview": preview,
        "can_execute": error_count == 0,
    }

    project.dry_run_json = json.dumps(result, ensure_ascii=False, default=str)
    project.status = "dry_run_ready"
    db.commit()
    record_audit(db, project.id, "DRY_RUN_COMPLETED", {k: result[k] for k in ("rows_analyzed", "error_count", "warning_count", "can_execute")})
    return result


@app.post("/api/projects/{project_id}/execute")
def execute_migration(project_id: int, payload: ExecuteRequest, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    schema = load_json(project.target_schema_json, None)
    mappings = load_json(project.mapping_json, [])
    dry_run_result = load_json(project.dry_run_json, None)
    if not project.source_file or not schema or not mappings or not dry_run_result:
        raise HTTPException(status_code=409, detail="Une simulation valide est obligatoire avant l'exécution.")
    if not dry_run_result.get("can_execute"):
        raise HTTPException(status_code=409, detail="La simulation contient des erreurs bloquantes.")

    dataframe = pd.read_csv(project.source_file, dtype=object, keep_default_na=True)
    transformed, transform_errors = transform_dataframe(dataframe, schema, mappings)
    issues = transform_errors + detect_anomalies(transformed, schema)
    blocking = [issue for issue in issues if issue.get("severity", "error") == "error"]
    if blocking:
        raise HTTPException(status_code=409, detail={"message": "Des erreurs sont apparues pendant l'exécution.", "issues": blocking[:20]})

    output_path = settings.storage_dir / "outputs" / f"{schema['entity']}-project-{project_id}-{uuid.uuid4().hex[:8]}.csv"
    transformed.to_csv(output_path, index=False)
    if project.output_file:
        Path(project.output_file).unlink(missing_ok=True)
    project.output_file = str(output_path)
    project.status = "completed"
    db.commit()
    record_audit(
        db,
        project.id,
        "MIGRATION_EXECUTED",
        {"approved_by": payload.approved_by, "rows": len(transformed), "output": output_path.name},
    )
    return {"status": "completed", "rows_migrated": int(len(transformed)), "download_url": f"/api/projects/{project.id}/download"}


@app.get("/api/projects/{project_id}/download")
def download_output(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    if not project.output_file or not Path(project.output_file).exists():
        raise HTTPException(status_code=404, detail="Aucun fichier migré disponible")
    return FileResponse(project.output_file, media_type="text/csv", filename=Path(project.output_file).name)


@app.get("/api/projects/{project_id}/audit")
def get_audit(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    events = list(
        db.scalars(
            select(AuditEvent).where(AuditEvent.project_id == project_id).order_by(AuditEvent.created_at.desc())
        ).all()
    )
    return [
        {
            "id": event.id,
            "action": event.action,
            "details": load_json(event.details_json, {}),
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]

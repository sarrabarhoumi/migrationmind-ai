from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


GLOBAL_ALIASES: dict[str, list[str]] = {
    "first_name": ["prenom", "prénom", "firstname", "given_name", "givenname"],
    "last_name": ["nom", "surname", "lastname", "family_name", "familyname"],
    "full_name": ["nom_complet", "fullname", "client_nom", "employee_name", "customer_name"],
    "email": ["mail", "courriel", "email_address", "adresse_mail"],
    "phone": ["telephone", "téléphone", "tel", "mobile", "gsm", "phone_number", "tel_client"],
    "street": ["adresse", "address", "rue", "adresse_complete"],
    "city": ["ville", "localite", "localité", "town"],
    "postal_code": ["code_postal", "zipcode", "zip", "cp"],
    "country": ["pays", "nation"],
    "balance": ["solde", "account_balance", "remaining_balance"],
    "amount": ["montant", "total", "prix", "price"],
    "date": ["created_at", "creation_date", "date_creation", "date"],
    "hiring_date": ["date_embauche", "hire_date", "start_date"],
    "employee_number": ["matricule", "employee_id", "staff_number"],
    "customer_id": ["client_id", "id_client", "customer_number"],
    "company": ["societe", "société", "company_name", "organisation", "organization"],
    "active": ["actif", "enabled", "status", "etat", "état"],
}

TYPE_COMPATIBILITY: dict[str, set[str]] = {
    "string": {"string", "email", "phone", "date", "integer", "float", "boolean"},
    "email": {"email", "string"},
    "phone": {"phone", "string", "integer"},
    "integer": {"integer", "float", "string"},
    "float": {"float", "integer", "string"},
    "date": {"date", "string"},
    "datetime": {"date", "string"},
    "boolean": {"boolean", "integer", "string"},
}


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _tokens(value: str) -> set[str]:
    return {token for token in normalize_name(value).split("_") if token}


def _name_score(target: str, source: str, aliases: list[str]) -> float:
    t = normalize_name(target)
    s = normalize_name(source)
    if t == s:
        return 1.0

    candidates = [t] + [normalize_name(alias) for alias in aliases]
    best = 0.0
    for candidate in candidates:
        if candidate == s:
            return 0.98
        seq = SequenceMatcher(None, candidate, s).ratio()
        token_union = _tokens(candidate) | _tokens(s)
        token_intersection = _tokens(candidate) & _tokens(s)
        jaccard = len(token_intersection) / len(token_union) if token_union else 0.0
        contains = 0.92 if candidate in s or s in candidate else 0.0
        best = max(best, seq, jaccard, contains)
    return best




def _vector_scores(target_document: str, source_columns: list[dict[str, Any]]) -> dict[str, float]:
    """Compute ML-based text similarity with character n-gram TF-IDF vectors."""
    source_documents = []
    for source in source_columns:
        samples = " ".join(str(value) for value in source.get("samples", [])[:5])
        source_documents.append(
            f"{source.get('name', '')} {source.get('inferred_type', '')} {samples}"
        )

    if not source_documents:
        return {}

    documents = [target_document] + source_documents
    try:
        matrix = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1).fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return {source_columns[index]["name"]: float(score) for index, score in enumerate(similarities)}
    except ValueError:
        return {source["name"]: 0.0 for source in source_columns}


def _type_score(target_type: str, source_type: str) -> float:
    if target_type == source_type:
        return 1.0
    if source_type in TYPE_COMPATIBILITY.get(target_type, {"string"}):
        return 0.72
    return 0.15


def _transformation(target: str, target_type: str, source: str, source_type: str) -> str:
    t = normalize_name(target)
    s = normalize_name(source)

    if t == "first_name" and s in {"full_name", "nom_complet", "client_nom", "customer_name", "employee_name"}:
        return "split_first"
    if t == "last_name" and s in {"full_name", "nom_complet", "client_nom", "customer_name", "employee_name"}:
        return "split_last"
    if target_type == "phone":
        return "normalize_phone"
    if target_type == "email":
        return "lowercase"
    if target_type in {"date", "datetime"}:
        return "parse_date"
    if target_type == "integer":
        return "to_int"
    if target_type == "float":
        return "to_float"
    if target_type == "boolean":
        return "to_boolean"
    if target_type == "string" and source_type == "string":
        return "trim"
    return "direct"


def suggest_mapping(source_profile: dict[str, Any], target_schema: dict[str, Any]) -> list[dict[str, Any]]:
    source_columns = source_profile.get("columns", [])
    results: list[dict[str, Any]] = []

    for target in target_schema.get("fields", []):
        target_name = target["name"]
        target_type = target.get("type", "string")
        aliases = list(target.get("aliases", []))
        aliases.extend(GLOBAL_ALIASES.get(normalize_name(target_name), []))

        # Full-name sources are valid candidates for first/last name targets.
        if normalize_name(target_name) in {"first_name", "last_name"}:
            aliases.extend(GLOBAL_ALIASES["full_name"])

        target_document = " ".join(
            [target_name, target.get("label") or "", target_type, *aliases]
        )
        vector_scores = _vector_scores(target_document, source_columns)

        ranked: list[tuple[float, dict[str, Any]]] = []
        for source in source_columns:
            lexical = _name_score(target_name, source["name"], aliases)
            vector = vector_scores.get(source["name"], 0.0)
            type_score = _type_score(target_type, source.get("inferred_type", "string"))
            score = (0.48 * lexical) + (0.32 * vector) + (0.20 * type_score)

            if normalize_name(target_name) in {"first_name", "last_name"} and normalize_name(source["name"]) in {
                "full_name",
                "nom_complet",
                "client_nom",
                "customer_name",
                "employee_name",
            }:
                score = max(score, 0.9)

            ranked.append((score, source))

        ranked.sort(key=lambda item: item[0], reverse=True)
        best_score, best_source = ranked[0] if ranked else (0.0, None)
        accepted = best_source is not None and best_score >= 0.44

        if accepted:
            transformation = _transformation(
                target_name,
                target_type,
                best_source["name"],
                best_source.get("inferred_type", "string"),
            )
            explanation = (
                f"Correspondance basée sur des vecteurs TF-IDF, les alias métier et la compatibilité de type "
                f"({best_source.get('inferred_type', 'string')} vers {target_type})."
            )
            source_field = best_source["name"]
        else:
            transformation = "default" if target.get("default") is not None else "direct"
            explanation = "Aucune correspondance suffisamment fiable. Validation humaine requise."
            source_field = None

        results.append(
            {
                "target_field": target_name,
                "source_field": source_field,
                "transformation": transformation,
                "confidence": round(float(best_score if accepted else 0.0), 3),
                "explanation": explanation,
                "approved": bool(best_score >= 0.85),
            }
        )

    return results

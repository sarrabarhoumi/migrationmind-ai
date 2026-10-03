import pandas as pd

from app.services.anomaly_engine import detect_anomalies
from app.services.mapping_engine import suggest_mapping
from app.services.transformation_engine import transform_dataframe


def test_mapping_engine_matches_business_aliases():
    profile = {
        "columns": [
            {"name": "client_nom", "inferred_type": "string"},
            {"name": "tel_client", "inferred_type": "phone"},
            {"name": "solde", "inferred_type": "float"},
        ]
    }
    schema = {
        "fields": [
            {"name": "first_name", "type": "string"},
            {"name": "phone", "type": "phone"},
            {"name": "balance", "type": "float"},
        ]
    }

    mappings = {item["target_field"]: item for item in suggest_mapping(profile, schema)}
    assert mappings["first_name"]["source_field"] == "client_nom"
    assert mappings["first_name"]["transformation"] == "split_first"
    assert mappings["phone"]["source_field"] == "tel_client"
    assert mappings["balance"]["source_field"] == "solde"


def test_transformation_and_anomaly_detection():
    source = pd.DataFrame(
        [
            {"client_nom": "Sarra Barhoumi", "mail": "SARRA@EXAMPLE.COM", "solde": "125,5"},
            {"client_nom": "Amine Test", "mail": "bad-email", "solde": "10"},
        ]
    )
    schema = {
        "fields": [
            {"name": "first_name", "type": "string", "required": True},
            {"name": "last_name", "type": "string", "required": True},
            {"name": "email", "type": "email", "required": True, "unique": True},
            {"name": "balance", "type": "float", "required": False},
        ]
    }
    mappings = [
        {"target_field": "first_name", "source_field": "client_nom", "transformation": "split_first"},
        {"target_field": "last_name", "source_field": "client_nom", "transformation": "split_last"},
        {"target_field": "email", "source_field": "mail", "transformation": "lowercase"},
        {"target_field": "balance", "source_field": "solde", "transformation": "to_float"},
    ]

    transformed, errors = transform_dataframe(source, schema, mappings)
    assert not errors
    assert transformed.iloc[0]["first_name"] == "Sarra"
    assert transformed.iloc[0]["last_name"] == "Barhoumi"
    assert transformed.iloc[0]["balance"] == 125.5

    issues = detect_anomalies(transformed, schema)
    assert any(issue["field"] == "email" and issue["code"] == "INVALID_TYPE" for issue in issues)


def test_iso_and_european_dates_are_parsed_correctly():
    from app.services.transformation_engine import transform_value

    assert transform_value("2026/03/01", "parse_date") == "2026-03-01"
    assert transform_value("15/02/2026", "parse_date") == "2026-02-15"
    assert transform_value("2026-04-10", "parse_date") == "2026-04-10"

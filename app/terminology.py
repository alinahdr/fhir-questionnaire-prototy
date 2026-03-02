import requests

FHIR_BASE = "http://localhost:8080/fhir"

# ==========================
# TERMINOLOGIE KONSTANTEN
# ==========================
TERMINOLOGY_SYSTEM = "http://example.org/fhir/CodeSystem/nummer-buchstabe"
CONCEPTMAP_URL     = "http://example.org/fhir/ConceptMap/nummer-buchstabe"

# Felder die als Codes behandelt werden sollen (linkId)
CODED_FIELDS = {"kategorie_code"}


def validate_code(code):
    """Prüft ob der Code im CodeSystem gültig ist. Gibt (True/False, message) zurück."""
    body = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "url",  "valueUri":  TERMINOLOGY_SYSTEM},
            {"name": "code", "valueCode": code}
        ]
    }
    r = requests.post(
        f"{FHIR_BASE}/CodeSystem/$validate-code",
        headers={"Content-Type": "application/fhir+json"},
        json=body
    )
    if not r.ok:
        return False, f"Validierung fehlgeschlagen (HTTP {r.status_code})"

    params  = r.json().get("parameter", [])
    result  = next((p["valueBoolean"] for p in params if p["name"] == "result"), False)
    message = next((p["valueString"]  for p in params if p["name"] == "message"), "")
    return result, message


def translate_code(code):
    """Übersetzt einen Code via ConceptMap (z.B. '1' → 'A'). Gibt den Ziel-Code zurück."""
    body = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "url",    "valueUri":  CONCEPTMAP_URL},
            {"name": "system", "valueUri":  TERMINOLOGY_SYSTEM},
            {"name": "code",   "valueCode": code}
        ]
    }
    r = requests.post(
        f"{FHIR_BASE}/ConceptMap/$translate",
        headers={"Content-Type": "application/fhir+json"},
        json=body
    )
    if not r.ok:
        return None

    params = r.json().get("parameter", [])
    result = next((p["valueBoolean"] for p in params if p["name"] == "result"), False)
    if not result:
        return None

    match = next((p for p in params if p["name"] == "match"), None)
    if match:
        for part in match.get("part", []):
            if part["name"] == "concept":
                return part["valueCoding"]["code"]
    return None
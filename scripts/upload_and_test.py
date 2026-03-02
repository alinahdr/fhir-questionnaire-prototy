import requests
import json
import os

FHIR_BASE = "http://localhost:8080/fhir"
FHIR_DIR = os.path.join(os.path.dirname(__file__), "..", "terminology")

HEADERS = {"Content-Type": "application/fhir+json"}


# ==========================
# UPLOAD RESSOURCE
# ==========================
def upload(filename, resource_type):
    filepath = os.path.join(FHIR_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    r = requests.post(f"{FHIR_BASE}/{resource_type}", headers=HEADERS, json=data)

    if r.ok:
        rid = r.json().get("id", "?")
        print(f"[OK] {resource_type} hochgeladen → ID: {rid}")
        return rid
    else:
        print(f"[FEHLER] {resource_type}: {r.status_code} – {r.text[:200]}")
        return None


# ==========================
# $LOOKUP – Code nachschlagen
# ==========================
def lookup(code):
    """Schlägt einen Code im eigenen CodeSystem nach."""
    r = requests.get(
        f"{FHIR_BASE}/CodeSystem/$lookup",
        params={
            "system": "http://example.org/fhir/CodeSystem/nummer-buchstabe",
            "code": code
        }
    )
    if r.ok:
        params = r.json().get("parameter", [])
        display = next((p["valueString"] for p in params if p["name"] == "display"), "?")
        print(f"[$lookup] Code '{code}' → Display: '{display}'")
    else:
        print(f"[$lookup FEHLER] {r.status_code}: {r.text[:200]}")


# ==========================
# $VALIDATE-CODE
# ==========================
def validate_code(code):
    """Prüft ob ein Code im ValueSet gültig ist."""
    r = requests.get(
        f"{FHIR_BASE}/ValueSet/$validate-code",
        params={
            "url": "http://example.org/fhir/ValueSet/nummer-buchstabe",
            "code": code,
            "system": "http://example.org/fhir/CodeSystem/nummer-buchstabe"
        }
    )
    if r.ok:
        params = r.json().get("parameter", [])
        result = next((p["valueBoolean"] for p in params if p["name"] == "result"), False)
        print(f"[$validate-code] Code '{code}' gültig: {result}")
    else:
        print(f"[$validate-code FEHLER] {r.status_code}: {r.text[:200]}")


# ==========================
# $TRANSLATE – Mapping testen
# ==========================
def translate(code):
    """Übersetzt einen Code via ConceptMap (1 → A, 2 → B, ...)"""
    body = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name": "url",
                "valueUri": "http://example.org/fhir/ConceptMap/nummer-buchstabe"
            },
            {
                "name": "system",
                "valueUri": "http://example.org/fhir/CodeSystem/nummer-buchstabe"
            },
            {
                "name": "code",
                "valueCode": code
            }
        ]
    }

    r = requests.post(
        f"{FHIR_BASE}/ConceptMap/$translate",
        headers=HEADERS,
        json=body
    )

    if r.ok:
        params = r.json().get("parameter", [])
        result = next((p["valueBoolean"] for p in params if p["name"] == "result"), False)
        match = next((p for p in params if p["name"] == "match"), None)

        if result and match:
            concept = match.get("part", [])
            mapped_code = next((p["valueCoding"]["code"] for p in concept if p["name"] == "concept"), "?")
            print(f"[$translate] '{code}' → '{mapped_code}'  ✓")
        else:
            print(f"[$translate] Kein Mapping gefunden für '{code}'")
    else:
        print(f"[$translate FEHLER] {r.status_code}: {r.text[:200]}")


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print("=" * 50)
    print("  Terminologie Upload & Test")
    print("=" * 50)

    print("\n--- 1. Ressourcen hochladen ---")
    upload("code_system.json",          "CodeSystem")
    upload("buchstaben_code_system.json","CodeSystem")
    upload("value_set.json",            "ValueSet")
    upload("concept_map.json",          "ConceptMap")

    print("\n--- 2. $lookup testen ---")
    for code in ["1", "2", "3", "4", "5", "6"]:
        lookup(code)

    print("\n--- 3. $validate-code testen ---")
    for code in ["1", "6", "7"]:   # 7 sollte ungültig sein
        validate_code(code)

    print("\n--- 4. $translate testen (Mapping) ---")
    for code in ["1", "2", "3", "4", "5", "6"]:
        translate(code)

    print("\nFertig!")
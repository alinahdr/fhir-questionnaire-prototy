import requests
import json

FHIR_BASE = "http://localhost:8080/fhir"
HEADERS   = {"Content-Type": "application/fhir+json"}


def get_patient(patient_id):
    """Lädt einen Patienten und gibt (given, family) zurück."""
    r = requests.get(f"{FHIR_BASE}/Patient/{patient_id}")
    if not r.ok:
        return None, None
    p      = r.json()
    name   = p.get("name", [{}])[0]
    given  = " ".join(name.get("given", []))
    family = name.get("family", "")
    return given, family


def create_patient(given, family):
    """Legt einen neuen Patienten an. Gibt die neue ID zurück."""
    patient = {
        "resourceType": "Patient",
        "name": [{"given": [given], "family": family}]
    }
    r = requests.post(f"{FHIR_BASE}/Patient", headers=HEADERS, json=patient)
    r.raise_for_status()
    return r.json()["id"]


def get_all_patients(count=50):
    """Gibt eine Liste von Patienten zurück: [{"id": ..., "name": ...}, ...]"""
    r = requests.get(f"{FHIR_BASE}/Patient?_count={count}")
    if not r.ok:
        return []
    patients = []
    for entry in r.json().get("entry", []):
        p      = entry["resource"]
        pid    = p["id"]
        name   = p.get("name", [{}])[0]
        given  = " ".join(name.get("given", []))
        family = name.get("family", "")
        patients.append({"id": pid, "name": f"{given} {family}"})
    return patients


def upload_questionnaire(questionnaire_json):
    """Lädt einen Fragebogen auf HAPI hoch. Gibt die neue ID zurück."""
    r = requests.post(f"{FHIR_BASE}/Questionnaire", headers=HEADERS, json=questionnaire_json)
    r.raise_for_status()
    return r.json()["id"]


def populate_questionnaire(questionnaire_id, patient_id):
    """Ruft $populate auf. Gibt die vorausgefüllte QuestionnaireResponse zurück."""
    parameters = {
        "resourceType": "Parameters",
        "parameter": [{
            "name": "subject",
            "valueReference": {"reference": f"Patient/{patient_id}"}
        }]
    }
    r = requests.post(
        f"{FHIR_BASE}/Questionnaire/{questionnaire_id}/$populate",
        headers=HEADERS,
        json=parameters
    )
    if not r.ok:
        return None, r.text
    return r.json(), None


def save_questionnaire_response(questionnaire_id, patient_id, items):
    """Speichert eine QuestionnaireResponse. Gibt (qr_id, error) zurück."""
    qr = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "questionnaire": f"{FHIR_BASE}/Questionnaire/{questionnaire_id}",
        "subject": {"reference": f"Patient/{patient_id}"},
        "item": items
    }
    r = requests.post(f"{FHIR_BASE}/QuestionnaireResponse", headers=HEADERS, json=qr)
    if r.ok:
        return r.json().get("id"), None
    return None, r.text


def get_questionnaire_response(qr_id):
    """Lädt eine einzelne QuestionnaireResponse."""
    r = requests.get(f"{FHIR_BASE}/QuestionnaireResponse/{qr_id}")
    if not r.ok:
        return None
    return r.json()


def get_responses_for_patient(patient_id, count=20):
    """Gibt alle QuestionnaireResponses eines Patienten zurück."""
    r = requests.get(
        f"{FHIR_BASE}/QuestionnaireResponse",
        params={"subject": f"Patient/{patient_id}", "_sort": "-_lastUpdated", "_count": count}
    )
    if not r.ok:
        return []
    return [entry["resource"] for entry in r.json().get("entry", [])]
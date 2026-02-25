import requests
import json

FHIR_BASE = "http://localhost:8080/fhir"

def post_q(filename):
    with open(filename, "r", encoding="utf-8") as f:
        questionnaire_json = json.load(f)

    response = requests.post(
        f"{FHIR_BASE}/Questionnaire",
        headers={"Content-Type": "application/fhir+json"},
        json=questionnaire_json
    )

    print("Status:", response.status_code)
    print("Questionnaire ID:", response.json()["id"])
    return response.json()["id"]

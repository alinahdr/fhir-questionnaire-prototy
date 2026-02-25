import requests

FHIR_BASE = "http://localhost:8080/fhir"

def populate_q(questionnaire_id, patient_id):

    parameters = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name": "subject",
                "valueReference": {
                    "reference": f"Patient/{patient_id}"
                }
            }
        ]
    }

    r = requests.post(
        f"{FHIR_BASE}/Questionnaire/{questionnaire_id}/$populate",
        headers={"Content-Type": "application/fhir+json"},
        json=parameters
    )

    print("Status:", r.status_code)
    return r.json()

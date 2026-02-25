import requests

FHIR_BASE = "http://localhost:8080/fhir"

def post_response(qr):
    r = requests.post(
        f"{FHIR_BASE}/QuestionnaireResponse",
        headers={"Content-Type": "application/fhir+json"},
        json=qr
    )

    print("Response Status:", r.status_code)

    if r.ok:
        resp_json = r.json()
        qr_id = resp_json.get("id")
        questionnaire_canonical = qr.get("questionnaire")

        print("QuestionnaireResponse link:")
        print(f"{FHIR_BASE}/QuestionnaireResponse/{qr_id}")

        print("All responses for this Questionnaire:")
        print(f"{FHIR_BASE}/QuestionnaireResponse?questionnaire={questionnaire_canonical}")

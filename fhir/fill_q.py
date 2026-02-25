import requests

FHIR_BASE = "http://localhost:8080/fhir"

def fill_q(questionnaire_id):
    q = requests.get(f"{FHIR_BASE}/Questionnaire/{questionnaire_id}").json()

    items = []
    for item in q["item"]:
        answer = input(f'{item["text"]}: ')
        items.append({
            "linkId": item["linkId"],
            "answer": [{"valueString": answer}]
        })

    qr = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "questionnaire": q["url"],   # canonical URL
        "item": items
    }

    return qr

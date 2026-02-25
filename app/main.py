from fhir.post_q import post_q
from fhir.populate_q import populate_q
from fhir.post_response import post_response
import requests
import json

FHIR_BASE = "http://localhost:8080/fhir"


def create_patient():
    given = input("Firstname: ")
    family = input("Lastname: ")

    patient = {
        "resourceType": "Patient",
        "name": [
            {
                "given": [given],
                "family": family
            }
        ]
    }

    r = requests.post(
        f"{FHIR_BASE}/Patient",
        headers={"Content-Type": "application/fhir+json"},
        json=patient
    )

    print("Status:", r.status_code)
    print("Patient created with ID:", r.json()["id"])

def upload_questionnaire():
    file_name = input("Enter Questionnaire file (e.g. test01.json): ")
    qid = post_q(file_name)
    print("Uploaded Questionnaire ID:", qid)
def fill_questionnaire():

    questionnaire_id = input("Enter Questionnaire ID: ")
    patient_id = input("Enter Patient ID: ")

    qr = populate_q(questionnaire_id, patient_id)

    print("\n--- Filling unanswered questions ---")

    for item in qr.get("item", []):

        # Falls keine Antwort vorhanden → User fragen
        if "answer" not in item:

            question_text = item.get("text", item["linkId"])

            user_input = input(f"{question_text}: ")

            # Typ automatisch erkennen
            if item.get("type") == "date":
                item["answer"] = [{
                    "valueDate": user_input
                }]
            elif item.get("type") == "integer":
                item["answer"] = [{
                    "valueInteger": int(user_input)
                }]
            else:
                item["answer"] = [{
                    "valueString": user_input
                }]

    print("\n--- Final QuestionnaireResponse ---")
    print(json.dumps(qr, indent=2))

    save = input("\nUpload to FHIR Server? (y/n): ")
    if save.lower() == "y":
        post_response(qr)
        print("QuestionnaireResponse successfully uploaded.")

def main():
    while True:
        print("\n====== Mini System ======")
        print("1. Create Patient")
        print("2. Questionnaire hochladen")
        print("3. Questionnaire ausfüllen")
        print("4. Exit")

        choice = input("Choose option: ")

        if choice == "1":
            create_patient()
        elif choice == "2":
            upload_questionnaire()
        elif choice == "3":
            fill_questionnaire()
        elif choice == "4":
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
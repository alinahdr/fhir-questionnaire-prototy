# FHIR Questionnaire Prototyp

Ein lokaler Prototyp zur Demonstration von FHIR-basierten Fragebögen mit automatischer Patientendaten-Vorbefüllung über den `$populate` Mechanismus.

---

## 1. FHIR Grundlagen

### 1.1 FHIR REST API

FHIR-Server stellen eine standardisierte **REST API** bereit. Jede Ressource kann über HTTP-Methoden verwaltet werden:

```
GET    /fhir/Patient/123           → Patient abrufen
POST   /fhir/Patient               → Neuen Patienten anlegen
PUT    /fhir/Patient/123           → Patienten aktualisieren
DELETE /fhir/Patient/123           → Patienten löschen
```

Alle Daten werden im Format **JSON** oder **XML** übertragen.

### 1.3 FHIR Operations

Neben den Standard-REST-Methoden gibt es sogenannte **Operations** – spezielle Aktionen die mit `$` gekennzeichnet werden:

```
POST /fhir/Questionnaire/456/$populate   → Fragebogen mit Patientendaten befüllen
GET  /fhir/Patient/$everything           → Alle Daten eines Patienten abrufen
```

### 1.4 FHIR SDC – Structured Data Capture

**SDC** (Structured Data Capture) ist ein FHIR-Implementierungsleitfaden der intelligente Fragebögen ermöglicht. SDC erweitert den Standard-`Questionnaire` um Funktionen wie:

- **Automatische Vorbefüllung** aus Patientendaten (`$populate`)
- **FHIRPath Expressions** um Daten aus der Patientenakte zu extrahieren
- **Bedingte Felder** die nur angezeigt werden wenn bestimmte Bedingungen erfüllt sind
- **Validierungsregeln** direkt im Fragebogen

Dieses Projekt setzt auf FHIR SDC für die `$populate` Funktionalität.

### 1.5 FHIRPath

**FHIRPath** ist eine Abfragesprache speziell für FHIR-Ressourcen – ähnlich wie XPath für XML. Sie wird in SDC-Fragebögen verwendet um festzulegen welche Patientendaten in welches Feld eingetragen werden sollen:

| FHIRPath Expression | Bedeutung |
|---|---|
| `%patient.name.first().given.first()` | Erster Vorname des Patienten |
| `%patient.name.first().family` | Nachname des Patienten |
| `%patient.birthDate` | Geburtsdatum |
| `%patient.address.first().city` | Stadt aus der Adresse |

---

## 2. Projektübersicht

Dieser Prototyp implementiert einen vollständigen FHIR-Workflow:

1. Patienten werden im FHIR-Server angelegt und verwaltet
2. Fragebögen (`Questionnaire`) werden als FHIR-Ressourcen hochgeladen
3. Beim Öffnen eines Fragebogens werden Patientendaten automatisch über `$populate` vorbefüllt
4. Der ausgefüllte Fragebogen wird als `QuestionnaireResponse` gespeichert

Das System läuft vollständig lokal. Als FHIR-Server wird **HAPI FHIR** in einem **Docker-Container** betrieben.

---

## 3. Verwendete Technologien

| Komponente | Version | Beschreibung |
|---|---|---|
| **Docker** | aktuell | Containerisierung des HAPI FHIR Servers |
| **HAPI FHIR Server** | latest | Open-Source FHIR-Server (JPA Server Starter) |
| **Python** | 3.x | Programmiersprache für Backend und Skripte |
| **Flask** | 2.x | Web-Framework für die Browser-Oberfläche |
| **FHIRPath** | - | Abfragesprache zum Extrahieren von Patientendaten |
| **FHIR SDC** | - | Structured Data Capture – Standard für intelligente Fragebögen |

---

## 4. Projektstruktur

```
Questionnaire/
│
├── README.md                     # Diese Dokumentation
│
├── app/                          # Haupt-Anwendung
│   ├── _web.py                   # Flask Web-App (Browser-Oberfläche)
│   └── main.py                   # Terminal-Version desselben Workflows
│
├── fhir/                         # FHIR Logik
│   ├── populate_q.py             # $populate Aufruf
│   ├── post_q.py                 # Questionnaire auf HAPI hochladen
│   ├── post_response.py          # QuestionnaireResponse speichern
│   └── fill_q.py                 # Fragebogen manuell befüllen (Terminal)
│
├── questionnaires/               # FHIR Questionnaire Definitionen (JSON)
│   ├── test01.json               # Vorname + Nachname mit FHIRPath
│   ├── test03.json               # + Geburtsdatum, SVS-Nummer
│   └── test04.json               # + Adresse, Ort, PLZ
│
├── docs/                         # Dokumentation
│   └── sequenz_diagramm.puml     # Sequenzdiagramm des Workflows
│
├── config/                       # Konfiguration
│   └── application.yaml          # HAPI Server Konfiguration
│
└── kis.py                        # Simuliertes KIS
```

---

## 5. Systemarchitektur

### 5.1 Gesamtübersicht

```
┌──────────────────────────────────────────────────────┐
│                    Laptop (lokal)                    │
│                                                      │
│  ┌─────────────┐        ┌──────────────────────────┐ │
│  │   Browser   │        │      Docker Container    │ │
│  │             │        │                          │ │
│  │  HTML Form  │        │   HAPI FHIR Server       │ │
│  │  Port 5000  │        │   Port 8080              │ │
│  └──────┬──────┘        │                          │ │
│         │               │   - Patient Ressourcen   │ │
│         │ HTTP          │   - Questionnaire        │ │
│         ▼               │   - QuestionnaireResponse│ │
│  ┌─────────────┐        │   - $populate Operation  │ │
│  │  Flask App  │◀──────▶│                          │ │
│  │  (_web.py)  │  HTTP  └──────────────────────────┘ │
│  │  Port 5000  │                                     │
│  └─────────────┘                                     │
└──────────────────────────────────────────────────────┘
```

### 5.2 Datenfluss – Fragebogen ausfüllen

```
1. Browser ruft Fragebogen auf
   Browser ──GET /questionnaire/{id}──▶ Flask

2. Flask ruft $populate beim HAPI Server auf
   Flask ──POST /fhir/Questionnaire/{id}/$populate──▶ HAPI
   Flask ◀── vorausgefüllte QuestionnaireResponse ──── HAPI

3. Flask rendert HTML-Formular mit vorausgefüllten Werten
   Browser ◀── HTML Formular ── Flask

4. Patient überprüft/ergänzt Daten und klickt Submit
   Browser ──POST Formulardaten──▶ Flask

5. Flask baut QuestionnaireResponse zusammen und speichert sie
   Flask ──POST /fhir/QuestionnaireResponse──▶ HAPI
```

---

## 6. Einrichtung & Start

### 6.1 Voraussetzungen

- **Docker Desktop** (für Windows)
- **Python 3.x** mit den Paketen: `flask`, `requests`

### 6.2 HAPI FHIR Server starten

```bash
docker run -p 8080:8080 -e hapi.fhir.cr.enabled=true hapiproject/hapi:latest
```

**Parameter im Detail:**

| Parameter | Bedeutung |
|---|---|
| `-p 8080:8080` | Port 8080 des Containers auf Port 8080 des Laptops weiterleiten |
| `-e hapi.fhir.cr.enabled=true` | Clinical Reasoning Modul aktivieren (benötigt für `$populate`) |
| `hapiproject/hapi:latest` | Offizielles HAPI FHIR Docker-Image |

Nach dem Start erreichbar unter:
- FHIR API: `http://localhost:8080/fhir`
- HAPI Web-UI: `http://localhost:8080`

> Referenz: https://github.com/hapifhir/hapi-fhir-jpaserver-starter

### 6.3 Flask Web-App starten

```bash
python app/_web.py
```

Danach im Browser öffnen: `http://localhost:5000`

---

## 7. Kernfunktion: $populate

### 7.1 Was ist $populate?

`$populate` ist eine FHIR SDC Operation die einen Fragebogen automatisch mit Patientendaten vorbefüllt. Statt dass der Patient seinen Namen und sein Geburtsdatum manuell eintippen muss, holt der HAPI Server diese Daten direkt aus der Patientenakte.

### 7.2 FHIRPath Expressions im Fragebogen

Im Fragebogen werden FHIRPath Expressions hinterlegt die dem Server sagen wo er die Daten findet:

```json
{
  "linkId": "firstname",
  "type": "string",
  "text": "Firstname",
  "extension": [{
    "url": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
    "valueExpression": {
      "language": "text/fhirpath",
      "expression": "%patient.name.first().given.first()"
    }
  }]
}
```

### 7.3 Der $populate Aufruf im Code

```python
# fhir/populate_q.py
parameters = {
    "resourceType": "Parameters",
    "parameter": [{
        "name": "subject",
        "valueReference": {
            "reference": f"Patient/{patient_id}"
        }
    }]
}

r = requests.post(
    f"{FHIR_BASE}/Questionnaire/{questionnaire_id}/$populate",
    headers={"Content-Type": "application/fhir+json"},
    json=parameters
)
```

Der HAPI Server gibt eine vorausgefüllte `QuestionnaireResponse` zurück. Flask liest diese aus und rendert daraus ein HTML-Formular mit den bereits eingetragenen Werten.

### 7.4 QuestionnaireResponse – wer baut sie?

Das **Flask-Backend** baut die `QuestionnaireResponse` selbst zusammen nachdem der Patient das Formular abgeschickt hat:

```python
# app/_web.py – POST Handler
items = []
for key in request.form:
    value = request.form.get(key)
    items.append({
        "linkId": key,
        "answer": [{"valueString": value}]
    })

qr = {
    "resourceType": "QuestionnaireResponse",
    "status": "completed",
    "questionnaire": f"{FHIR_BASE}/Questionnaire/{qid}",
    "subject": {"reference": f"Patient/{active_patient}"},
    "item": items
}

requests.post(f"{FHIR_BASE}/QuestionnaireResponse",
              headers={"Content-Type": "application/fhir+json"},
              json=qr)
```

---

## 8. Hinweis: LForms (nicht verwendet)

In professionellen FHIR-Projekten wird für die Darstellung von Fragebögen im Browser häufig **LForms** verwendet – eine Web-Komponente der U.S. National Library of Medicine.

**Was LForms normalerweise macht:**
- Rendert FHIR `Questionnaire` Ressourcen automatisch als ausfüllbare Formulare im Browser
- Unterstützt alle FHIR-Feldtypen (Text, Datum, Zahl, Auswahl, etc.)
- Baut die `QuestionnaireResponse` automatisch im Frontend zusammen
- Schickt sie direkt an den FHIR-Server – ohne dass das Backend eingreifen muss

**Warum LForms hier nicht verwendet wurde:**

LForms konnte aus **Sicherheitsgründen** nicht in diesen Prototyp eingebunden werden. Daher wurde die gesamte Formular-Darstellung und die Erstellung der `QuestionnaireResponse` manuell im Flask-Backend (`_web.py`) implementiert – funktional gleichwertig, aber ohne die automatische Frontend-Logik von LForms.

---

## 9. FHIR-Ressourcen Beispiele

**Patient:**
```json
{
  "resourceType": "Patient",
  "name": [{"given": ["Anna"], "family": "Müller"}]
}
```

**QuestionnaireResponse (nach dem Ausfüllen):**
```json
{
  "resourceType": "QuestionnaireResponse",
  "status": "completed",
  "questionnaire": "http://localhost:8080/fhir/Questionnaire/1001",
  "subject": {"reference": "Patient/1000"},
  "item": [
    {"linkId": "firstname", "answer": [{"valueString": "Anna"}]},
    {"linkId": "lastname",  "answer": [{"valueString": "Müller"}]},
    {"linkId": "birthdate", "answer": [{"valueDate": "1990-05-14"}]}
  ]
}
```

---

## 10. Referenzen

- HAPI FHIR Server: https://github.com/hapifhir/hapi-fhir-jpaserver-starter
- HL7 FHIR Spezifikation: https://www.hl7.org/fhir/
- FHIR SDC (Structured Data Capture): https://hl7.org/fhir/uv/sdc/
- FHIRPath Spezifikation: https://hl7.org/fhirpath/
- LForms Web Component: https://lhncbc.github.io/lforms/
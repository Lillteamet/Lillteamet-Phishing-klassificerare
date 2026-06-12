# 🛡️ Lillteamet Phishing-klassificerare

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-NLP-green.svg)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-Phishing%20Detection-red.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

En komplett plattform för **phishing-detektering, adversarial testing och interaktiva demonstrationer**.

Projektet kombinerar NLP-baserad maskininlärning, säkerhetstestning och en webbaserad demoapplikation för att identifiera phishing-mejl och analysera hur robust modellen är mot olika angreppsstrategier.

---

## ✨ Funktioner

* 🧠 Träning av phishing-detektionsmodell
* 📧 Klassificering av inkommande e-post
* ⚔️ Adversarial testing och säkerhetsutvärdering
* 🌐 Interaktiv webbapplikation
* 📬 Simulerad mailbox
* 📊 Modellvalidering och rapportering
* 🔒 Säkerhetsdokumentation
* 🎓 Anpassad för demonstrationer och utbildning

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Lillteamet/Lillteamet-Phishing-klassificerare.git
cd Lillteamet-Phishing-klassificerare

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Träna modellen

```bash
python train.py --dataset-path Datasets
```

### Testa klassificering

```bash
python agent.py --email-file sample_email.txt
```

### Kör attacksimulering

```bash
python attack.py --mode adaptive --email-file sample_email.txt
```

### Starta webbappen

Linux/macOS:

```bash
./run_webapp.sh
```

Windows:

```bat
run_webapp.bat
```

Alternativt:

```bash
python webapp.py
```

Öppna sedan:

```text
http://localhost:5000
```

---

## 🏗️ Systemarkitektur

```text
Datasets
    │
    ▼
train.py
    │
    ▼
phishing_model.joblib
    │
    ├────────► agent.py
    │              │
    │              ▼
    │      Phishing / Ham
    │
    ├────────► attack.py
    │
    └────────► webapp.py
                    │
                    ▼
            Demo-Webbgränssnitt
```

---

## 🌐 Webbapplikation

Projektet innehåller en komplett webbapplikation för att demonstrera phishing-detektering i en realistisk miljö.

### Funktioner

* 📥 Inkorg för legitima meddelanden
* 🚨 Junk/Spam-vy för phishing-mejl
* 📜 Loggsystem för klassificeringar
* 🤖 Realtidsanalys via ML-modellen
* 🗄️ SQLite-baserad lagring
* 🎯 Perfekt för live-demos och presentationer

### Webbgränssnitt

| Sida     | Beskrivning                    |
| -------- | ------------------------------ |
| 📥 Inbox | Legitima e-postmeddelanden     |
| 🚨 Junk  | Identifierade phishing-mejl    |
| 📜 Logs  | Historik över klassificeringar |

Databas:

```text
instance/phishing_mailbox.db
```

---

## 🧠 Modellträning

`train.py` ansvarar för:

* Datainläsning
* Datarensning
* NLP-preprocessing
* Feature engineering
* Modellträning
* Modellutvärdering
* Export av tränad modell

Genererad modell:

```text
phishing_model.joblib
```

---

## ⚔️ Säkerhetstestning

Projektet innehåller flera verktyg för adversarial testing.

### attack.py

Grundläggande attacker mot modellen.

### attack_enhanced.py

Utökade attacker för att analysera modellens robusthet.

### attack_training_generator.py

Genererar ytterligare träningsdata för att förbättra modellens motståndskraft.

Målet är att förstå hur phishing-meddelanden kan modifieras för att kringgå ML-baserade detektionssystem.

---

## 📊 Validering och utvärdering

Valideringsverktyg finns under:

```text
scripts/
```

Exempel:

```bash
python scripts/validate_model.py
```

eller

```bash
python scripts/validate_pipeline.py
```

Rapporter genereras i:

```text
validation_report.txt
```

---

## 📚 Dataset

Projektet använder flera offentliga phishing-dataset:

* CEAS 2008
* Enron
* Ling
* Nazario
* Nigerian Fraud
* SpamAssassin
* Phishing & Legitimate Emails Dataset 2026

Samtliga källor dokumenteras i:

```text
Datasets/sources.txt
```

---

## 📁 Projektstruktur

```text
.
├── train.py
├── agent.py
├── attack.py
├── attack_enhanced.py
├── attack_training_generator.py
├── generate_data.py
├── webapp.py
├── phishing_model.joblib
├── requirements.txt
├── SECURITY.md
├── WEBAPP_README.md
├── WEBAPP_SETUP.md
│
├── Datasets/
├── templates/
├── scripts/
├── instance/
└── README.md
```

---

## 👥 Team

| Roll            | Person                             | Ansvar                                        |
| --------------- | ---------------------------------- | --------------------------------------------- |
| 📊 Data         | Sebastian (Fchas)                  | Dataset, feature engineering och datakvalitet |
| 🧠 Modell       | Liam (liam-baltze), Mert (MA-chas) | Modellträning, optimering och utvärdering     |
| ⚔️ Säkerhet     | André (andreedvardsson)            | Adversarial testing och säkerhetsanalys       |
| 🎤 Presentation | Abdulghani (abbe-max)              | Demo, dokumentation och presentation          |

---

## 📖 Dokumentation

| Dokument           | Beskrivning                    |
| ------------------ | ------------------------------ |
| `README.md`        | Projektöversikt                |
| `WEBAPP_README.md` | Webbappens funktioner          |
| `WEBAPP_SETUP.md`  | Installation och konfiguration |
| `SECURITY.md`      | Säkerhetsanalys                |
| `CHANGELOG.txt`    | Versionshistorik               |

---

## 🔒 Säkerhet

Säkerhetsrelaterad information och attackanalys finns dokumenterad i:

```text
SECURITY.md
```

---

## 📜 Licens

Projektet utvecklades inom ramen för utbildning och forskning inom cybersäkerhet, maskininlärning och phishing-detektering.

---

⭐ Om projektet hjälper dig, överväg gärna att ge repot en stjärna på GitHub.

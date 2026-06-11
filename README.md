# 🛡️ Lillteamet Phishing-klassificerare

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![ML](https://img.shields.io/badge/ML-NLP%20Classifier-green.svg)
![Security](https://img.shields.io/badge/security-phishing%20detection-red.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

---

## 📌 Projektöversikt

Detta projekt är en **NLP-baserad phishing-klassificerare** som identifierar skadliga e-postmeddelanden och URL:er.

Modellen analyserar:
- ✉️ E-postinnehåll (brödtext & rubriker)
- 🔗 URL-strukturer och domäner
- 🧾 Header-information
- 👤 Avsändarbeteende

Målet är att bygga en robust och utbyggbar säkerhetsmodell för att upptäcka phishing i textbaserad kommunikation.

---

## 📊 Dataset

Dataset används från flera källor listade i `sources.txt`:

🔗 https://github.com/Lillteamet/Lillteamet-Phishing-klassificerare/blob/test/Datasets/sources.txt  

---

## 🧠 Ursprungligt projekt

Bygger vidare på originalprojektet:

🔗 https://github.com/r87-e/ais-grupp-phishing  

---

## 🌐 Presentation

📽️ https://abbe-max.github.io/presentation-n-tfiske-/  

---

## 🏗️ Arkitektur

Projektet består av tre huvudkomponenter:

| Modul | Fil | Beskrivning |
|------|-----|-------------|
| 🧠 Träning | `train.py` | Tränar NLP-modellen |
| ⚔️ Attack | `attack.py` | Simulerar adversariala attacker |
| 🤖 Agent | `agent.py` | Klassificerar nya mail |

---

## 📁 Projektstruktur

```
.
├── train.py          # Modellträning
├── attack.py         # Adversarial testing
├── agent.py          # Inference/klassificering
├── requirements.txt
├── Datasets/
│   └── sources.txt
└── README.md
```

---

## 🧠 train.py – Modellträning

Ansvar:
- 📥 Laddar och preprocessar dataset
- 🔍 Extraherar NLP-features (text, URL, metadata)
- ⚙️ Tränar klassificeringsmodell
- 📈 Utvärderar performance (accuracy, precision, recall, F1)

---

## ⚔️ attack.py – Säkerhetstestning

Simulerar hur modellen kan angripas:

- 🧪 Genererar adversarial emails
- 🎭 Modifierar phishing-strukturer
- 🧠 Testar robusthet mot manipulation
- 📊 Mäter attack-success rate

Exempel:
```bash
python attack.py --mode adaptive --email-file sample_email.txt
```

---

## 🤖 agent.py – Produktion / inference

Används för att klassificera nya mail:

- 📩 Tar emot email-input
- 🧠 Kör modellen
- 🚨 Returnerar: `Phishing` eller `Ham`

Exempel:
```bash
python agent.py --email-file sample_email.txt
```

---

## 🚀 Snabbstart

```bash
# Skapa miljö
python3 -m venv venv
source venv/bin/activate

# Installera dependencies
pip install -r requirements.txt

# Träna modellen
python train.py --dataset-path Datasets

# Testa attacker
python attack.py --mode adaptive --email-file sample_email.txt

# Kör klassificering
python agent.py --email-file sample_email.txt
```

---

## 🎯 Projektmål

- 🧠 Bygga en robust phishing-detektor
- 🛡️ Förstå adversarial ML-attacker
- 🔬 Förbättra NLP-baserad feature engineering
- 📉 Minska false positives/negatives
- ⚙️ Skapa en enkel inference-agent

---

## 👥 Team

| Roll | Person | Ansvar |
|------|--------|--------|
| 📊 Data | Sebastian (Fchas) | Dataset, features & projekt ledning |
| 🧠 Modell | Liam (liam-baltze), Mert (MA-chas) | Modelloptimering |
| ⚔️ Attack & säkerhet | André (andreedvardsson) | Adversarial testing |
| 🎤 Presentation | Abdulghani (abbe-max) | Demo & slides |

---

## 🔮 Möjliga förbättringar

- 🤖 Transformer-modeller (BERT, RoBERTa)
- 🛡️ Adversarial training
- 🔗 Bättre URL-detektion
- 🌐 API för realtidsklassificering
- 📡 Logging & monitoring

---

## 📜 Licens

Projektet är en del av utbildningsarbete och bygger på open-source inspiration.

---

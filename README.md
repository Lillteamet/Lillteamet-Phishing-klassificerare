# Phishing-detektor

En enkel maskininlärningsbaserad klassificerare som avgör om ett e-postmeddelande är phishing eller legitimt (ham). Modellen tränas på syntetiska e-postexempel och demonstrerar sedan hur en angripare kan manipulera texten så att klassificeraren missar hotet.

Projektet är avsiktligt enkelt skrivet: syftet är att ni ska förstå varje rad kod och sedan förbättra och attackera er egen modell.

---

## Snabbstart

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
python train.py
python attack.py
```

Det är allt. Ingen nerladdning, ingen GPU, inget internet krävs.

---

## Vad ni ska leverera

### G (Godkänt)

- [ ] Modellen tränas och ger rimliga mätvärden (accuracy, precision, recall, F1)
- [ ] Kort skriftlig dokumentation: vad modellen gör, vilka features den använder
- [ ] Ni har kört `attack.py` och kan förklara varför modellen flippade
- [ ] Live-demo för klassen (5 min): visa träning, mätvärden och attacken

### VG (Väl godkänt)

- [ ] Jämför minst två olika ML-metoder (t.ex. Logistic Regression vs. Random Forest vs. Naive Bayes) och motivera vilket som är bäst för detta problem
- [ ] Robusthetstest: systematisk genomgång av hur många/vilka ordbyten som krävs för att lura modellen, redovisa resultaten i en tabell eller graf
- [ ] Integration mot SIEM/SOAR: exportera modellens utdata (label + confidence) till en loggfil i JSON-format som Wazuh eller liknande system kan läsa in
- [ ] Ren och reproducerbar kod: annan person ska kunna klona repot och få exakt samma mätvärden med tre kommandon

---

## Roller i teamet

| Roll | Person | Ansvar |
|------|--------|--------|
| **Data** | Sebastian (F-chas) | Förstår och utvidgar datasetet, dokumenterar features, ansvarar för train/test-uppdelning |
| **Modell** | Liam (liam-baltze), Mert (MA-chas) | Trimmar hyperparametrar, jämför algoritmer, skriver ut och tolkar mätvärden |
| **Attack och säkerhet** | André (andreedvardsson) | Kör `attack.py`, utforskar nya angreppsstrategier, skriver SECURITY.md |
| **Presentation** | Abdulghani (abbe-max) | Samordnar demon, gör slides eller live-demo, dokumenterar slutresultat |

Rollerna är ett startläge, inte en låst struktur. Hjälp varandra.

---

## Attackera er egen modell

Scriptet `attack.py` visar en enkel adversarial attack:

1. Det letar upp ett phishing-mail som modellen klassificerar korrekt med hög säkerhet.
2. Det byter ut "trigger-ord" (t.ex. "click here" -> "visit the page", "urgent" -> "upcoming").
3. Det lägger till ofarliga meningar tills modellen flippar till HAM.

Resultatet skrivs ut tydligt:

```
Prediction: PHISHING  (confidence: 93.45%)
...
Prediction: HAM  (confidence: 61.23%)
EVASION SUCCESSFUL
```

Er uppgift: förstå varför det funkade, och fundera på hur ni skulle göra modellen mer robust.

---

## Skala upp med riktig data

När ni är nöjda med er grundmodell kan ni prova med riktig phishing-data:

- **Nazario Phishing Corpus**: klassisk samling phishing-mail från forskning, finns på GitHub
- **PhishTank**: öppen databas med verifierade phishing-URL:er (phishtank.org)
- **Kaggle "phishing email"**: sök på Kaggle efter "phishing email dataset" för CSV-filer redo att använda

Det finns nu stöd för att läsa in lokala datasetfiler direkt i `train.py`.
Spara datasetet i CSV/TSV/JSON-format och träna med:

```bash
python train.py --dataset-paths Datasets
```

eller med individuella filer:

```bash
python train.py --dataset-paths Datasets/Phishing_validation_emails.csv Datasets/Phishing\ and\ Legitimate\ Emails\ Dataset\ for\ ML\ 2026/phishing_legit_dataset_KD_10000.csv
```

Funktionen stöder både kolumner som `text`, `message`, `email`, `content`, `body`, `email text` och `email type`, eller kombinationen `subject` + `body`.
Etiketten kan vara `label`, `class`, `target`, `phishing`, `is_phishing`, `spam` eller `category` med vanliga värden som `0/1`, `ham/phishing` eller `legitimate/spam`.

Ersätt `generate_dataset()` i `train.py` med en funktion som läser in en riktig CSV så är ni klara.

## AI-agent för e-postskanning

Det finns även en ny agent i `agent.py` som laddar den tränade modellen och skannar en e-posttext för kända phishing-signaturer.
Den skriver ut:

- Modellens prediktion och sannolikhet
- Upptäckta misstänkta mönster och fraser
- En kort slutsats om varför e-posten kan vara phishing

Exempel:

```bash
python agent.py --text "Subject: Verify your account now\n\nClick here to update your billing information."
```

eller

```bash
python agent.py --email-file sample_email.txt
```

Agenten hjälper er att visa hur både ML-signaler och enkla regelbaserade signaturer kan användas för phishingdetektion.

---

## Mer information

Hitta inlämningsformulär, deadlines och teamuppgifter på **Grupprojekt-sidan i portalen**:
https://web-gilt-three-68.vercel.app/

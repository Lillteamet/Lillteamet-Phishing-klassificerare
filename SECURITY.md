# Säkerhetsanalys av vår egen modell

Det här dokumentet beskriver hur vi testade vår phishingmodell som en egen
attackyta. Fokus ligger på evasion: om en angripare kan ändra ett phishingmejl
så att modellen inte längre klassificerar det som phishing.

---

## Vilken attack testade ni?

Vi testade en evasion-attack med `attack.py`.

Attacken försökte lura modellen genom att ändra typiska phishing-ord till mer
neutrala uttryck. Exempel på ordbyten:

- `click here` -> `visit the page`
- `verify your` -> `review your`
- `urgent` -> `upcoming`
- `password` -> `credentials`
- `confirm your` -> `update your`
- `your account` -> `your profile`

Scriptet lade också till normal fyllnadstext, till exempel artiga avslut och
vardagliga meningar, för att få mejlet att likna legitim kommunikation.

---

## Vad hände?

Vi körde först `agent.py` mot `sample_email.txt`. Agenten klassificerade
testmejlet som phishing:

```text
Prediction: PHISHING  (confidence: 100.00%)
```

Den hittade bland annat dessa phishing-signaler:

- `click here`
- `verify your`
- `billing information`
- generisk hälsning: `Dear customer`
- finansiellt/billing-relaterat språk

Sedan körde vi `attack.py`. Originalmejlet som valdes av attackscriptet
klassificerades som:

```text
Prediction: PHISHING  (confidence: 99.99%)
```

Attacken lyckades inte få modellen att flippa till `HAM`.

```text
Attack failed: model did not flip with available perturbations.
```

Resultatet blev alltså att modellen stod emot den här enkla attacken.

---

## Varför fungerade/fungerade inte attacken?

Attacken fungerade inte med de enkla ändringarna som testades. Det tyder på att
modellen inte bara bygger sitt beslut på ett enda ord, utan på flera textmönster
samtidigt.

Modellen använder TF-IDF-features, vilket innebär att den väger in många ord och
ordkombinationer i mejlet. Även om vissa phishing-ord byts ut kan andra signaler
finnas kvar, till exempel kontoaktivitet, verifiering, avstängning, faktura- eller
betalningsspråk.

Det betyder inte att modellen är helt säker. En mer avancerad angripare skulle
kunna testa större omskrivningar, felstavningar, URL-obfuskering eller exempel
som är särskilt konstruerade för att likna legitim kommunikation.

---

## Hur skulle ni försvara modellen?

För att göra modellen mer robust skulle vi använda flera försvar:

- **Adversarial training:** Lägg till manipulerade phishingmejl i träningsdatan,
  till exempel mejl med ordbyten, felstavningar och omskriven text.
- **URL-features:** Analysera länkar mer detaljerat, till exempel domänlängd,
  subdomäner, misstänkta TLD:er, IP-adresser i URL:er och URL-shorteners.
- **Ensemble eller extra regler:** Kombinera ML-modellen med regelbaserade
  kontroller, blocklistor och IOC-data.
- **Manuell granskning vid låg confidence:** Om modellen är osäker bör mejlet
  flaggas för mänsklig granskning istället för att automatiskt godkännas.
- **SIEM-loggning:** Skicka resultat som label, confidence och hittade signaler
  till ett SIEM-system så att säkerhetsteamet kan följa upp mönster över tid.

---

## Slutsats

Vi lärde oss att en ML-modell för phishingdetektion också måste testas som en
attackyta. Vår första evasion-attack lyckades inte lura modellen, men mer
avancerade attacker är fortfarande möjliga och bör ingå i framtida robusthetstestning.

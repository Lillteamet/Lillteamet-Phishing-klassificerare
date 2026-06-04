# Säkerhetsanalys av vår egen modell

Det här dokumentet beskriver hur vi testade vår phishingmodell som en egen
attackyta. Fokus ligger på evasion: om en angripare kan ändra ett phishingmejl
så att modellen inte längre klassificerar det som phishing.

---

## Vilken attack testade ni?

Vi testade först en evasion-attack med originalscriptet `attack.py`.

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

Efter det skapade vi en separat förbättrad attackdemo i `attack_enhanced.py`.
Originalfilen `attack.py` ändrades inte. Den förbättrade versionen kan köras mot
ett eget mejl med:

```bash
python attack_enhanced.py --email-file sample_email.txt
```

Den visar varje attacksteg, confidence efter varje steg och slutresultatet även
om attacken misslyckas. Den innehåller också fler realistiska konto- och
säkerhetsfraser, till exempel:

- `verify your account` -> `review your profile`
- `unusual activity` -> `recent activity`
- `customer support` -> `help desk`
- `your account` -> `your profile`

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

När vi sedan körde den förbättrade attacken mot `sample_email.txt` lyckades den
flippa modellen:

```text
Original prediction: PHISHING  (confidence: 100.00%)
Final prediction: HAM  (confidence: 71.12%)
Result: EVASION SUCCESSFUL
```

Attacken gjorde flera stegvisa ändringar, till exempel:

```text
click here -> visit the page
verify your -> review your
unusual activity -> recent activity
customer support -> help desk
immediately -> soon
your account -> your profile
```

Efter ordbytena lade scriptet till normal fyllnadstext. Då klassificerade
modellen det manipulerade mejlet som `HAM`, trots att mejlet fortfarande hade ett
misstänkt syfte.

---

## Varför fungerade/fungerade inte attacken?

Originalattacken fungerade inte med de enkla ändringarna som testades. Det tyder
på att modellen inte bara bygger sitt beslut på ett enda ord, utan på flera
textmönster samtidigt.

Modellen använder TF-IDF-features, vilket innebär att den väger in många ord och
ordkombinationer i mejlet. Även om vissa phishing-ord byts ut kan andra signaler
finnas kvar, till exempel kontoaktivitet, verifiering, avstängning, faktura- eller
betalningsspråk.

Den förbättrade attacken fungerade eftersom den kombinerade flera små ändringar:
frasbyten, mer neutral formulering och extra legitimt klingande text. Det gjorde
att den totala textprofilen flyttades närmare ham/legitim kommunikation enligt
modellen.

Det visar att modellen fortfarande är sårbar för mer systematisk evasion. En mer
avancerad angripare skulle också kunna testa större omskrivningar, felstavningar,
URL-obfuskering eller exempel som är särskilt konstruerade för att likna legitim
kommunikation.

---

## Hur skulle ni försvara modellen?

För att göra modellen mer robust skulle vi använda flera försvar:

- **Adversarial training:** Lägg till manipulerade phishingmejl i träningsdatan,
  till exempel de exempel som skapas av `attack_enhanced.py`.
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
attackyta. Originalattacken lyckades inte lura modellen, men den förbättrade
attacken i `attack_enhanced.py` lyckades flippa modellen från `PHISHING` till
`HAM`. Det ger modellteamet ett konkret robusthetstest att använda när modellen
förbättras.

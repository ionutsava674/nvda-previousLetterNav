# Navigare înapoi după literă (NVDA add-on)

În Explorer, apăsarea unei litere duce la **următorul** fișier care începe cu ea.
Acest add-on adaugă **Shift+literă**, care duce la fișierul **anterior**.

## Funcționare

- **Shift+R**: fișierul anterior care începe cu R. Repetat, continuă înapoi; la începutul listei sare la final.
- **Shift+R, apoi Shift+E** în mai puțin de o secundă: caută înapoi după prefixul „re”.
- Fără potrivire: un bip scurt.
- Funcționează în Explorer, pe desktop și în dialogurile Deschide/Salvează.
- La redenumire (F2) sau în câmpuri de editare nu se activează.
- Tastele se pot schimba din NVDA → Preferințe → Gesturi de intrare, categoria „Navigare înapoi după literă”.

## Structura proiectului

```
addon/                          conținutul pachetului
  manifest.ini                  nume, versiune, compatibilitate NVDA
  globalPlugins/previousLetterNav/__init__.py   codul add-on-ului
build.py                        construiește dist/*.nvda-addon
dist/                           rezultatul build-ului (ignorat de git)
CLAUDE.md                       context pentru Claude Code
```

## Build

Necesită doar Python 3:

```
python build.py
```

Rezultatul apare în `dist/previousLetterNav-<versiune>.nvda-addon`. Dai Enter pe el ca să-l instalezi.

## Dezvoltare rapidă (fără reinstalare)

Poți copia folderul `addon/globalPlugins/previousLetterNav` în
`%APPDATA%\nvda\scratchpad\globalPlugins\`, activa „Enable loading custom code from Developer Scratchpad
Directory” în NVDA → Preferințe → Setări → Avansat, apoi NVDA+Ctrl+F3 reîncarcă pluginurile.
Erorile se văd în jurnalul NVDA (NVDA+F1 sau Meniu NVDA → Unelte → Vizualizare jurnal).

## Limite cunoscute

- Doar literele a–z (fără ă, â, î, ș, ț).
- În foldere cu mii de fișiere poate răspunde mai încet (citește toată lista prin UI Automation la fiecare apăsare).

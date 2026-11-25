# CLAUDE.md

Proiect: add-on NVDA (cititor de ecran pentru Windows) care adaugă Shift+literă în listele de fișiere
pentru a merge la elementul ANTERIOR care începe cu litera respectivă (Explorer face doar „următorul”).

Utilizatorul folosește NVDA, deci comunică în română și ține cont că lucrează cu cititor de ecran:
răspunsuri clare, fără dependență de elemente vizuale.

## Cod

- `addon/globalPlugins/previousLetterNav/__init__.py` — tot codul.
  - `GlobalPlugin.chooseNVDAObjectOverlayClasses` adaugă clasa `PreviousLetterNavItem` peste
    obiectele cu rol LISTITEM din ferestrele `DirectUIHWND` (Explorer) și `SysListView32` (desktop).
  - `script_previousByLetter` e legat la `kb:shift+a` … `kb:shift+z`.
  - `_TypeAhead` imită tastarea incrementală din Explorer (timeout 1 s; aceeași literă = ciclare, litere diferite = prefix).
  - `_moveUIA`: metoda principală, prin UI Automation (`FindAllBuildCache` pe lista părinte, TreeScope_Descendants
    ca să prindă grupurile), apoi Realize / ScrollIntoView / Select / SetFocus.
  - `_moveGeneric`: rezervă prin obiecte NVDA / IAccessible (`accSelect` cu TAKEFOCUS|TAKESELECTION).
- `addon/manifest.ini` — versiunea se schimbă aici (`version`), plus `minimumNVDAVersion` / `lastTestedNVDAVersion`.
- `build.py` — creează `dist/<name>-<version>.nvda-addon` (zip cu conținutul folderului `addon/`).

## Comenzi

- Build: `python build.py`
- Verificare sintaxă: `python -m py_compile addon/globalPlugins/previousLetterNav/__init__.py`

## Note

- Codul folosește taburi pentru indentare (convenția NVDA).
- Testarea reală se face doar în NVDA pe Windows; jurnalul NVDA (nivel debug) arată avertismentele `previousLetterNav:`.
- Idei de îmbunătățire: suport pentru diacritice românești, cache al listei pentru foldere mari,
  setări în panoul NVDA (timeout, bip on/off), traduceri (addonHandler.initTranslation + locale/).

# Hot-Reload System - Quick Start

## Installation (3 Schritte)

### 1. Installiere Dependencies

```bash
pip install -r requirements.txt
```

Oder manuell:

```bash
pip install watchdog>=3.0.0
```

### 2. Aktiviere Hot-Reload (Optional)

Hot-Reload ist standardmäßig aktiviert. Um es zu deaktivieren, füge in `.env` hinzu:

```bash
HOT_RELOAD_ENABLED=false
```

### 3. Starte Agent Zero

```bash
python run_ui.py
```

Du solltest sehen:

```
Hot-reload manager initialized
Watching: D:\projects\agent-zero\python\tools
Watching: D:\projects\agent-zero\python\extensions
Watching: D:\projects\agent-zero\prompts
Hot-reload file watcher started
Hot-reload system initialized
```

## Verifikation

### Automatische Verifikation

```bash
python verify_hot_reload.py
```

### Manuelle Verifikation

1. **Starte Agent Zero**:
   ```bash
   python run_ui.py
   ```

2. **Öffne ein Tool in einem Editor**:
   ```bash
   vim D:\projects\agent-zero\python\tools\hot_reload_test.py
   ```

3. **Ändere die Nachricht**:
   ```python
   # Vorher:
   test_message = "Hot-Reload Test v1.0 - The system is working!"

   # Nachher:
   test_message = "Hot-Reload Test v2.0 - IT WORKS!"
   ```

4. **Speichere die Datei**

5. **Beobachte die Console**:
   ```
   Hot-Reload: MODIFIED - hot_reload_test.py
   Reloading module: tools.hot_reload_test
   Successfully reloaded: tools.hot_reload_test
   Tools cache invalidated
   ```

6. **Teste das Tool** (in der Agent Zero UI):
   ```
   Use the hot_reload_test tool
   ```

   Die neue Nachricht erscheint sofort - **kein Docker-Restart nötig!**

## DevTools Panel

Öffne die Agent Zero WebUI und schau in die **untere rechte Ecke**.

Du siehst:

- 🔥 **Hot-Reload** Panel
- **Status**: Grüner Punkt = Active
- **Statistiken**:
  - Reloads: Anzahl der Reload-Versuche
  - Success: Erfolgreiche Reloads
  - Failures: Fehlgeschlagene Reloads
  - Cached Modules: Anzahl gecachter Module

Das Panel aktualisiert sich automatisch alle 5 Sekunden.

## Workflow

### Entwicklung eines Tools

1. **Öffne/Erstelle Tool**:
   ```bash
   vim D:\projects\agent-zero\python\tools\my_new_tool.py
   ```

2. **Implementiere Tool-Klasse**:
   ```python
   from python.helpers.tool import Tool, Response

   class MyNewTool(Tool):
       async def execute(self, **kwargs) -> Response:
           result = "Tool output"
           return Response(message=result, break_loop=False)
   ```

3. **Speichere** → Hot-Reload erkennt automatisch

4. **Teste sofort** in Agent Zero UI

5. **Iteriere** ohne Restarts

### Entwicklung einer Extension

Gleicher Workflow:

1. Öffne Extension:
   ```bash
   vim D:\projects\agent-zero\python\extensions\message_loop_end\_10_my_extension.py
   ```

2. Implementiere `Extension` Klasse

3. Speichere → Automatisches Reload

4. Teste

## Troubleshooting

### Hot-Reload startet nicht

**Problem**: Keine "Hot-reload" Meldungen in Console

**Lösung**:

1. Prüfe `.env`:
   ```bash
   HOT_RELOAD_ENABLED=true
   ```

2. Prüfe watchdog Installation:
   ```bash
   pip install watchdog
   ```

3. Starte Agent Zero neu

### Änderungen werden nicht erkannt

**Problem**: File-Änderungen lösen kein Reload aus

**Lösung**:

1. Prüfe, ob Datei in überwachtem Verzeichnis liegt:
   - `python/tools/`
   - `python/extensions/`
   - `prompts/`

2. Prüfe Dateiendung:
   - `.py` für Python-Dateien
   - `.md` für Prompts

### Reload schlägt fehl

**Problem**: DevTools Panel zeigt Failures

**Lösung**:

1. Prüfe Console auf Fehlermeldungen

2. Syntax-Fehler in deinem Code?
   - Hot-Reload rollback zur letzten funktionierenden Version

3. Import-Fehler?
   - Prüfe, ob alle Imports verfügbar sind

## Performance

### Vorher (ohne Hot-Reload)

1. Editiere Tool
2. Speichere
3. Stoppe Docker Container
4. Rebuild Image
5. Starte Container
6. Warte auf Initialization
7. Teste

**Zeit**: 30-60 Sekunden

### Nachher (mit Hot-Reload)

1. Editiere Tool
2. Speichere
3. Teste

**Zeit**: < 1 Sekunde

## Best Practices

### Do

- ✅ Kleine, fokussierte Änderungen
- ✅ Teste nach jedem Reload
- ✅ Beobachte DevTools Panel für Failures
- ✅ Nutze Rollback bei Fehlern

### Don't

- ❌ Große Refactorings ohne Tests
- ❌ Änderungen an kritischen System-Modulen
- ❌ Komplexe Dependency-Chains

## Weitere Dokumentation

Siehe `docs/HOT_RELOAD.md` für:

- Detaillierte Architektur
- Erweiterte Funktionen
- API-Referenz
- Troubleshooting-Guide

## Support

Bei Problemen:

1. Prüfe Console-Output
2. Prüfe DevTools Panel
3. Führe `python verify_hot_reload.py` aus
4. Konsultiere `docs/HOT_RELOAD.md`

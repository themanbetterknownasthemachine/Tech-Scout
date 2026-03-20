# 🔭 Tech Scout Agent

Automatischer Tech Scout für ML, Deep Learning, Data Science und Data Analytics.
Läuft jeden Montag 08:00 via GitHub Actions und speichert Findings als JSON.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `tech_scout_agent.py` | Agent-Script mit Web Search und Agentic Loop |
| `tech_scout_findings.json` | Findings (automatisch generiert) |
| `.github/workflows/tech_scout.yml` | GitHub Actions Workflow |

## Workflow

```
Montag 08:00 → GitHub Actions startet
             → Agent sucht im Web (arXiv, HuggingFace, GitHub, Blogs)
             → Findings gespeichert in tech_scout_findings.json
             → Im Repo committet
             → Tech Scout Website → 📥 JSON importieren
```

## Manuell starten

Actions → Tech Scout Weekly → Run workflow

Optional: Fokus-Thema und Anzahl Findings eingeben.

## Setup

1. `ANTHROPIC_API_KEY` als Repository Secret hinterlegen
2. Actions aktivieren
3. Einmalig manuell testen via "Run workflow"

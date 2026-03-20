# 🔭 Tech Scout Agent

Automatischer Tech Scout für ML, Deep Learning, Data Science und Data Analytics.
Läuft jeden Montag 08:00 via GitHub Actions und speichert Findings als JSON.

**Website**: [themanbetterknownasthemachine.github.io/Tech-Scout](https://themanbetterknownasthemachine.github.io/Tech-Scout)

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `tech_scout_agent.py` | Agent-Script mit Web Search und Agentic Loop |
| `SKILL.md` | Scouting-Framework, PoC-Scorecard, Report-Templates |
| `index.html` | Tech Scout Website (Feed, PoC Tracker, Filter, Export) |
| `tech-scout-doku.html` | Workflow-Dokumentation (Architektur, Setup, Kosten) |
| `tech_scout_findings.json` | Findings (automatisch generiert) |
| `.github/workflows/tech_scout.yml` | GitHub Actions Workflow |

## Features

- **Automatisches Scouting** — Wöchentliche Recherche via Anthropic API + Web Search
- **PoC-Scorecard** — Systematische Bewertung von PoC-Kandidaten (6 Kriterien, Score /30)
- **PoC Tracker** — Kanban-Board mit Stages: Idee → In Prüfung → Aktiv → Done
- **Report-Templates** — Wöchentlich, Monatlich, Quartals-Review
- **Export** — JSON und Markdown Export der Findings

## Workflow

```
Montag 08:00 → GitHub Actions startet
             → Agent liest SKILL.md (Framework + Quellen)
             → Web Search (arXiv, HuggingFace, GitHub, Blogs)
             → Findings gespeichert in tech_scout_findings.json
             → Im Repo committet
             → Website lädt JSON automatisch von GitHub
```

## Manuell starten

Actions → Tech Scout Weekly → Run workflow

Optional: Fokus-Thema und Anzahl Findings eingeben.

## Setup

1. `ANTHROPIC_API_KEY` als Repository Secret hinterlegen
2. GitHub Pages aktivieren (Source: main, Root)
3. Actions aktivieren
4. Einmalig manuell testen via "Run workflow"
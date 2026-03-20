#!/usr/bin/env python3
"""
Tech Scout Agent — vollständig nach Tech Scout SKILL.md
=========================================================
Nutzt ALLE Quellen, Kategorien, Qualitätskriterien und den
kompletten Workflow aus dem Tech Scout Skill.

Setup:
    pip install anthropic

Usage:
    python tech_scout_agent.py
    python tech_scout_agent.py --focus "Time Series Forecasting"
    python tech_scout_agent.py --limit 5
    python tech_scout_agent.py --kategorie "Operative Effizienz"
    python tech_scout_agent.py --dry-run
    python tech_scout_agent.py --output findings.json

Workflow (wie im Skill definiert):
    1. Suchfokus definieren (via --focus / --kategorie)
    2. HuggingFace + arXiv für aktuelle Paper
    3. Firmen-Blogs der relevanten Labs
    4. Twitter/X für Breaking News
    5. YouTube-Kanäle für Video-Zusammenfassungen
    6. Filtern nach Qualitätskriterien
    7. Formatieren nach Output-Format
    8. Priorisieren nach Relevanz-Matrix
    9. PoC-Kandidaten mit verlinktem Code identifizieren
"""

import os, json, argparse, hashlib, datetime, time, re
from pathlib import Path
import anthropic

# ── Konfiguration ──────────────────────────────────────────────────────────────
MODEL          = "claude-opus-4-6"
DEFAULT_OUTPUT = Path("tech_scout_findings.json")
MAX_TURNS      = 12

# ── Vollständiger Skill-Prompt ─────────────────────────────────────────────────
def build_skill_prompt(focus: str, kategorie: str, limit: int, today: str) -> str:
    return f"""Du bist ein Innovation ICT Tech Scout für Machine Learning, Data Science und Data Analysis.
Unternehmen: Schweizer Lebensmittellogistik. Stack: Snowflake (Data Vault 2.0), Apache Airflow,
Power BI, Python (LightGBM, NeuralForecast, scikit-learn), Claude Code. Heute: {today}.

## Auftrag
Finde {limit} hochwertige, aktuelle Tech-Findings. Führe den vollständigen Scout-Workflow durch.

## Relevanz-Matrix (Priorisierung)
1. Direkte Anwendbarkeit — für ML, Data Science, Data Analysis
2. Technische Reife — PoC-ready vs. Forschungsphase
3. Impact/Aufwand-Verhältnis — Business Value vs. Implementierungskosten

## Themenbereich
Suche offen nach den aktuellsten Trends aus ML, Deep Learning, Data Science, Data Analytics, MLOps und GenAI.
{f"Fokus eingegrenzt auf: {kategorie}" if kategorie else "Keine thematische Einschränkung — Qualitaet und Aktualitaet entscheiden."}
Die Kategorien (Operative Effizienz / Data Engineering / Business Intelligence / Emerging Tech) sind nur Labels
fuer die spaetere Einordnung im JSON-Output — lass dich davon nicht beim Suchen einschraenken.

## Fokus-Thema
{focus or "Allgemeiner Scout über alle Kategorien"}

## Workflow (PFLICHT — in dieser Reihenfolge ausführen)

### Schritt 1: Papers & Forschung
Suche auf:
- arXiv cs.CL (recent): https://arxiv.org/list/cs.CL/recent
- arXiv cs.LG (recent): https://arxiv.org/list/cs.LG/recent
- arXiv cs.AI (recent): https://arxiv.org/list/cs.AI/recent
- Papers with Code: https://paperswithcode.com
- ACL Anthology: https://aclanthology.org
- HuggingFace Trending: https://huggingface.co/papers
- Top-Konferenzen: NeurIPS, ICML, ICLR, KDD, ACL, EMNLP, NAACL

### Schritt 2: Code & Implementierungen
Suche auf:
- GitHub Trending Python: https://github.com/trending?l=python
- HuggingFace Models/Datasets (trending)
- Papers with Code Benchmarks: https://paperswithcode.com/sota

### Schritt 3: Firmen-Blogs & Primärquellen
Suche bei:
- Anthropic Research: https://www.anthropic.com/research
- OpenAI Research: https://openai.com/research
- Google DeepMind: https://deepmind.google/research/publications/
- Meta AI Research: https://ai.meta.com/research/
- Apple ML: https://machinelearning.apple.com
- Microsoft Research: https://www.microsoft.com/en-us/research/blog/
- Amazon Science: https://www.amazon.science/blog
- Snowflake Engineering: https://www.snowflake.com/en/engineering-blog/
- dbt Labs Blog: https://www.getdbt.com/blog
- Databricks Blog: https://www.databricks.com/blog
- Stanford NLP: https://nlp.stanford.edu/blog/
- MIT CSAIL: https://www.csail.mit.edu/news

### Schritt 4: Fachpublikationen & Newsletter
- Towards Data Science / Medium
- KDnuggets, Analytics Vidhya
- The Batch (Andrew Ng)
- VentureBeat AI, MIT Technology Review

### Schritt 5: Community & Breaking News
- Reddit: r/MachineLearning, r/datascience, r/LocalLLaMA
- Twitter/X: @karpathy, @ylecun, @sama, @DrJimFan, @ilyasut
- YouTube: Two Minute Papers, Yannic Kilcher, Andrej Karpathy, HuggingFace

## Qualitätskriterien (PFLICHT)
✓ Primärquelle bevorzugen (Original-Paper, offizielle Firmen-Ankündigungen)
✓ Aktualität: idealerweise < 4 Wochen alt
✓ Hype vs. Substanz unterscheiden
✓ Reproduzierbare Ergebnisse und Code verfügbar?
✓ Peer-reviewed oder nur Preprint?
✓ GitHub Stars / Zitierungen als Qualitätsindikator

## Red Flags (AUSSCHLIESSEN)
⚠ Reine Marketing-Ankündigungen ohne technische Details
⚠ Übertriebene Versprechungen ohne Benchmarks
⚠ Closed-Source ohne Evaluationsmöglichkeit
⚠ Kein reproduzierbarer Code bei Methoden-Claims

## Thought Leaders (bei Suche berücksichtigen)
Andrej Karpathy, Yann LeCun, Andrew Ng, Cassie Kozyrkov, Chip Huyen,
Eugene Yan, Yannic Kilcher, Jim Fan, Sebastian Raschka

## Output pro Finding
Beschreibe jeden Fund mit: Titel, URL, Organisation, Typ (Paper/Blog/Tool/Video/Code),
Zusammenfassung 2-3 Sätze Deutsch, Relevanz (Hoch/Mittel/Niedrig),
PoC-Potenzial für Logistik/Forecasting/BI mit Begründung,
Kategorie, Tags, Code-URL falls vorhanden.

Priorisiere nach Relevanz-Matrix. Identifiziere PoC-Kandidaten explizit."""


FORMAT_PROMPT = """Konvertiere die Tech-Scout-Findings exakt in ein JSON-Array.
Antworte NUR mit dem Array — kein Text, kein Markdown, keine Codeblöcke.

Schema:
[{{
  "title": "exakter Titel",
  "source": "https://url.com",
  "type": "Paper",
  "summary": "2-3 Sätze Deutsch",
  "relevance": "Hoch",
  "poc": true,
  "poc_note": "Warum PoC-relevant oder leer",
  "category": "Emerging Tech",
  "tags": ["tag1", "tag2"],
  "code_url": null,
  "source_org": "Organisation"
}}]

Enums:
- type: Paper | Blog | Tool | Video | Code
- relevance: Hoch | Mittel | Niedrig
- category: Operative Effizienz | Data Engineering | Business Intelligence | Emerging Tech

Findings:
{findings_text}"""


# ── Agentic Loop ───────────────────────────────────────────────────────────────
def run_agentic_search(client: anthropic.Anthropic, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    tools    = [{"type": "web_search_20250305", "name": "web_search"}]

    for turn in range(MAX_TURNS):
        print(f"  [Turn {turn+1}] API Call...", end="", flush=True)

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=8000,
            tools=tools,
            messages=messages,
            betas=["web-search-2025-03-05"]
        )

        stop_reason = response.stop_reason
        print(f" → {stop_reason}")

        # Content serialisierbar machen
        content_raw = response.content
        content_serializable = []
        for block in content_raw:
            if hasattr(block, "model_dump"):
                content_serializable.append(block.model_dump())
            elif hasattr(block, "dict"):
                content_serializable.append(block.dict())
            else:
                content_serializable.append(block)

        messages.append({"role": "assistant", "content": content_serializable})

        if stop_reason in ("end_turn", "max_tokens"):
            texts = [b.text for b in content_raw if hasattr(b, "text") and b.text]
            return "\n".join(texts).strip()

        if stop_reason == "tool_use":
            tool_results = []
            for block in content_raw:
                if hasattr(block, "type") and block.type == "tool_use":
                    inp = block.input if isinstance(block.input, dict) else {}
                    query = inp.get("query", "")
                    print(f"       🔍 Web Search: '{query}'")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Suchanfrage ausgeführt: {query}"
                    })
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                break
        else:
            break

    raise RuntimeError(f"Kein Ergebnis nach {MAX_TURNS} Turns")


# ── JSON parsen ────────────────────────────────────────────────────────────────
def parse_json_array(text: str) -> list:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I|re.M)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned, flags=re.M).strip()
    try:
        p = json.loads(cleaned)
        if isinstance(p, list): return p
    except: pass
    m = re.search(r"\[[\s\S]*\]", cleaned)
    if m:
        return json.loads(m.group())
    raise ValueError(f"Kein JSON-Array:\n{text[:400]}")


def normalize(f: dict, today: str) -> dict:
    title = (f.get("title") or "Kein Titel").strip()
    return {
        "id":         hashlib.md5(title.lower().encode()).hexdigest()[:12],
        "title":      title,
        "source":     (f.get("source") or "#").strip(),
        "type":       f.get("type","Blog") if f.get("type") in ["Paper","Blog","Tool","Video","Code"] else "Blog",
        "summary":    (f.get("summary") or "").strip(),
        "relevance":  f.get("relevance","Mittel") if f.get("relevance") in ["Hoch","Mittel","Niedrig"] else "Mittel",
        "poc":        bool(f.get("poc", False)),
        "pocNote":    (f.get("poc_note") or f.get("pocNote") or "").strip(),
        "category":   f.get("category","Emerging Tech") if f.get("category") in
                      ["Operative Effizienz","Data Engineering","Business Intelligence","Emerging Tech"]
                      else "Emerging Tech",
        "tags":       f.get("tags",[]) if isinstance(f.get("tags"),list) else [],
        "codeUrl":    f.get("code_url") or f.get("codeUrl") or None,
        "source_org": (f.get("source_org") or "").strip(),
        "date":       today,
        "scouted_at": datetime.datetime.now().isoformat(),
    }


def load_findings(path: Path) -> list:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    return []


def save_findings(findings: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)


def dedupe(existing: list, new: list) -> tuple:
    ids = {f["id"] for f in existing}
    added = [f for f in new if f["id"] not in ids]
    return added, len(added)


def print_report(findings: list, added: int, output: Path, elapsed: float) -> None:
    icons = {"Hoch":"🟢","Mittel":"🟡","Niedrig":"⚫"}
    print(f"\n{'═'*62}")
    print(f"  🔭 Tech Scout Report — {datetime.date.today()}")
    print(f"{'═'*62}")
    print(f"  Neu gespeichert : {added} Findings")
    print(f"  Laufzeit        : {elapsed:.1f}s")
    print(f"  Output-Datei    : {output.absolute()}")
    print(f"{'─'*62}")
    for f in findings:
        icon  = icons.get(f.get("relevance",""),"•")
        poc   = " 📌 PoC" if f.get("poc") else ""
        code  = " 💻" if f.get("codeUrl") else ""
        print(f"\n{icon} [{f.get('type','')}] {f.get('title','')}{poc}{code}")
        print(f"   📍 {f.get('source_org','')} | 🏷  {', '.join(f.get('tags',[])[:3])}")
        summary = f.get("summary","")
        print(f"   {summary[:110]}{'...' if len(summary)>110 else ''}")
        if f.get("poc") and f.get("pocNote"):
            print(f"   → PoC: {f['pocNote'][:80]}")
    print(f"\n{'═'*62}")
    print(f"\n  → Findings importieren: 'JSON importieren' Button in der Tech Scout Website")
    print(f"  → Datei: {output.absolute()}\n")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Tech Scout Agent — vollständig nach SKILL.md")
    parser.add_argument("--focus",      type=str,  default="", help="Fokus-Thema, z.B. 'LLM Agents'")
    parser.add_argument("--kategorie",  type=str,  default="", help="Kategorie: 'Operative Effizienz' | 'Data Engineering' | 'Business Intelligence' | 'Emerging Tech'")
    parser.add_argument("--limit",      type=int,  default=5,  help="Anzahl Findings (default: 5)")
    parser.add_argument("--output",     type=Path, default=DEFAULT_OUTPUT, help="Output JSON-Datei")
    parser.add_argument("--dry-run",    action="store_true", help="Nicht speichern")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY fehlt → export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    client = anthropic.Anthropic(api_key=api_key)
    today  = datetime.date.today().isoformat()
    start  = time.time()

    print(f"\n🔭 Tech Scout Agent — vollständig nach SKILL.md")
    print(f"   Fokus:     {args.focus or '(allgemein — alle Kategorien)'}")
    print(f"   Kategorie: {args.kategorie or '(alle, nach Priorität)'}")
    print(f"   Limit:     {args.limit} Findings")
    print(f"   Output:    {args.output}\n")

    # ── SCHRITT 1-5: Vollständiger Skill-Workflow via Web Search ──────────────
    print("── Schritt 1-5: Scout-Workflow (Web Search) ──")
    prompt = build_skill_prompt(args.focus, args.kategorie, args.limit, today)

    try:
        search_result = run_agentic_search(client, prompt)
    except Exception as e:
        print(f"❌ Web Search Fehler: {e}")
        return

    if not search_result:
        print("❌ Keine Ergebnisse")
        return

    print(f"\n✓ Scout-Workflow abgeschlossen ({len(search_result)} Zeichen)\n")

    # ── SCHRITT 6-9: JSON strukturieren ───────────────────────────────────────
    print("── Schritt 6-9: Filtern, Formatieren, Priorisieren ──")
    fmt_prompt = FORMAT_PROMPT.format(findings_text=search_result)

    try:
        fmt_res = client.messages.create(
            model=MODEL, max_tokens=2000,
            messages=[{"role": "user", "content": fmt_prompt}]
        )
        json_text = "".join(
            b.text for b in fmt_res.content if hasattr(b, "text")
        ).strip()
        raw = parse_json_array(json_text)
    except Exception as e:
        print(f"❌ JSON-Parsing Fehler: {e}")
        return

    new_findings = [normalize(f, today) for f in raw]
    print(f"✓ {len(new_findings)} Findings strukturiert und normalisiert")

    # Nach Relevanz sortieren
    order = {"Hoch": 0, "Mittel": 1, "Niedrig": 2}
    new_findings.sort(key=lambda f: order.get(f["relevance"], 1))

    # ── Speichern ──────────────────────────────────────────────────────────────
    existing    = load_findings(args.output)
    to_add, cnt = dedupe(existing, new_findings)

    if not args.dry_run:
        merged = to_add + existing  # Neueste zuerst
        save_findings(merged, args.output)
    else:
        print(f"ℹ️  Dry-Run: {cnt} neue Findings (nicht gespeichert)")

    print_report(new_findings, cnt, args.output, time.time() - start)


if __name__ == "__main__":
    main()

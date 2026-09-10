# 🚨 Sentinel Watchdog — Breaking Changes Detection & Structured Telemetry Guide
> *"The gunslinger does not aim with his hand; he aims with his eye."*  
> *We parse the trail signs to mark danger points in the ledger.*

[![Dashboard Deployment](https://github.com/FreeFades2Black/repo-watchdog-agent/actions/workflows/watchdog-dashboard.yml/badge.svg)](https://github.com/FreeFades2Black/repo-watchdog-agent/actions)
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-2ea44f?style=flat-square&logo=githubpages&logoColor=white)](https://freefades2black.github.io/repo-watchdog-agent/)
[![Breaking Change Parser](https://img.shields.io/badge/Telemetry-Schema%20Enforced-critical?style=flat-square&logo=json)](docs/data/latest.json)

This guide documents the **Structured Telemetry Schema**, the **Deterministic Breaking Change Parser**, and the **High-Contrast Warning UI** implemented for the Sentinel Agent dashboard.

---

## 📋 1. Structured Data Schema

To display warning badges reliably without fragile DOM text-scraping, the agent emits an explicit, machine-readable JSON payload into `docs/data/latest.json`. This enables the dashboard to evaluate Boolean flags (`has_breaking_changes`) and exact numeric counts (`breaking_count`).

### Schema Definition (`docs/data/latest.json`)
```json
{
  "timestamp": "2026-09-10T10:45:00Z",
  "date": "2026-09-10",
  "status": "Success",
  "has_breaking_changes": true,
  "breaking_count": 2,
  "breaking_changes": [
    {
      "repo": "microsoft/agent-framework",
      "title": "Renamed Agent.run() signature to async Agent.execute_async()",
      "detail": "PR #412 removes sync run invocation, breaking backward compatibility."
    },
    {
      "repo": "microsoft/semantic-kernel",
      "title": "Deprecated OpenAIChatCompletionService constructor options",
      "detail": "Removed legacy credentials payload in favor of azure-ai-inference clients."
    }
  ],
  "agent_summary": "### Daily Upstream Intelligence\n\n- Detected 2 critical breaking updates...",
  "tracked_repos": ["microsoft/agent-framework", "microsoft/semantic-kernel"]
}
```

### Manifest Schema (`docs/data/manifest.json`)
Maintains a rolling 30-day index of all executions, enabling historical badge coloring in the sidebar:
```json
[
  {
    "timestamp": "2026-09-10T15:46:23.942701+00:00",
    "date": "2026-09-10",
    "status": "Success",
    "has_breaking_changes": false,
    "breaking_count": 0,
    "summary_snippet": "**Generated:** `2026-09-10 15:46:23 UTC` ... Upstream APIs remain stable."
  },
  {
    "timestamp": "2026-09-09T15:00:00.000000+00:00",
    "date": "2026-09-09",
    "status": "Success",
    "has_breaking_changes": true,
    "breaking_count": 1,
    "summary_snippet": "**Generated:** `2026-09-09 15:00:00 UTC` ... Detected breaking change."
  }
]
```

---

## 🐍 2. Agent Telemetry Exporter Update

The parser in `agent_watchdog.py` inspects the synthesized briefing, extracts bulleted items located under the `High Impact / Breaking Changes` section, attributes each to a monitored repository, and constructs the structured telemetry:

### Implementation (`agent_watchdog.py`)
```python
# ==============================================================================
# "The gunslinger does not aim with his hand; he aims with his eye."
# We parse the trail signs to mark danger points in the ledger.
# ==============================================================================

import os
import json
import datetime
from typing import Dict, Any, List

def parse_and_export_telemetry(
    agent_raw_output: str,
    repo_list: List[str],
    docs_dir: str = None
) -> dict:
    """
    Parses agent findings for breaking changes and saves structured telemetry
    to docs/data/latest.json and updates docs/data/manifest.json.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    base_docs = docs_dir or os.path.join(os.getcwd(), "docs")
    data_dir = os.path.join(base_docs, "data")
    os.makedirs(data_dir, exist_ok=True)

    # --------------------------------------------------------------------------
    # Extraction: Parse breaking changes from output markers
    # --------------------------------------------------------------------------
    breaking_records = []
    lines = agent_raw_output.splitlines()
    in_breaking_section = False

    for line in lines:
        cleaned = line.strip()
        if ("high impact" in cleaned.lower() or "breaking changes" in cleaned.lower()) and cleaned.startswith("##"):
            in_breaking_section = True
            continue
        elif (cleaned.startswith("##") or cleaned.startswith("---")) and in_breaking_section:
            # End of breaking changes block
            in_breaking_section = False

        if in_breaking_section and (cleaned.startswith("- ") or cleaned.startswith("* ")):
            item_text = cleaned[2:].strip()
            lower_text = item_text.lower()
            # Filter out non-actionable placeholder statements
            if (
                item_text
                and not lower_text.startswith("none")
                and not lower_text.startswith("no explicit")
                and not lower_text.startswith("no breaking")
                and not lower_text.startswith("zero")
            ):
                # Attribute item to known repo if referenced
                matched_repo = next((r for r in repo_list if r.lower() in item_text.lower()), "Upstream")
                title_part = item_text.split(":")[0] if ":" in item_text else item_text[:80]
                breaking_records.append({
                    "repo": matched_repo,
                    "title": title_part.strip(),
                    "detail": item_text
                })

    has_breaking = len(breaking_records) > 0
    breaking_count = len(breaking_records)

    # 1. Write Latest Run Snapshot
    payload = {
        "timestamp": timestamp,
        "date": date_str,
        "status": "Success",
        "has_breaking_changes": has_breaking,
        "breaking_count": breaking_count,
        "breaking_changes": breaking_records,
        "agent_summary": agent_raw_output,
        "tracked_repos": repo_list
    }

    with open(os.path.join(data_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # 2. Update Run Manifest (Historical Runs)
    manifest_file = os.path.join(data_dir, "manifest.json")
    manifest = []
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            manifest = []

    manifest.insert(0, {
        "timestamp": timestamp,
        "date": date_str,
        "status": "Success",
        "has_breaking_changes": has_breaking,
        "breaking_count": breaking_count,
        "summary_snippet": agent_raw_output[:160] + "..." if len(agent_raw_output) > 160 else agent_raw_output
    })

    # Retain the last 30 runs
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest[:30], f, indent=2)

    print(f"[+] Exported telemetry: {breaking_count} breaking changes identified.")
    return payload
```

---

## 🖥️ 3. Updated Dashboard Frontend (`docs/index.html`)

The updated dashboard features:
1. **High-Visibility Red Warning Badges (`.badge-danger`):** Dynamically rendered in the header when `has_breaking_changes === true`.
2. **Urgent Alert Box (`#breaking-banner`):** Renders itemized breaking commits/PRs with their parent repository tags.
3. **Historical Danger Badges:** Displays individual red tags (`X Breaking`) vs green tags (`Stable`) per run in the 30-day sidebar.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sentinel Watchdog | Live Dashboard</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --accent: #58a6ff;
      --green: #2ea043;
      --red: #f85149;
      --red-bg: rgba(248, 81, 73, 0.15);
      --red-border: rgba(248, 81, 73, 0.4);
      --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      padding: 2rem 1rem;
      line-height: 1.5;
    }
    .container { max-width: 1100px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1.5rem;
    }
    h1 { font-size: 1.5rem; font-weight: 600; color: #fff; }

    /* Badge Indicators */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.75rem;
      border-radius: 20px;
      font-size: 0.8rem;
      font-family: var(--font-mono);
      font-weight: 600;
    }
    .badge-ok {
      background: rgba(46, 160, 67, 0.15);
      color: var(--green);
      border: 1px solid rgba(46, 160, 67, 0.3);
    }
    .badge-ok::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
    }
    .badge-danger {
      background: var(--red-bg);
      color: var(--red);
      border: 1px solid var(--red-border);
    }
    .badge-danger::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--red);
    }

    /* Danger Alert Box */
    .alert-box {
      display: none;
      background: var(--red-bg);
      border: 1px solid var(--red-border);
      border-radius: 6px;
      padding: 1rem 1.25rem;
      margin-bottom: 1.5rem;
    }
    .alert-box h2 {
      font-size: 1rem;
      color: var(--red);
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .alert-list {
      list-style-type: disc;
      margin-left: 1.5rem;
      font-size: 0.85rem;
      color: #f0f6fc;
    }

    /* Layout Grid */
    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 800px) {
      .grid { grid-template-columns: 1fr; }
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1.25rem;
    }
    .card-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: #8b949e;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 1rem;
    }
    pre {
      background: #090d12;
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: #e6edf3;
      white-space: pre-wrap;
      max-height: 480px;
      overflow-y: auto;
    }
    .history-list { list-style: none; }
    .history-item {
      padding: 0.75rem 0;
      border-bottom: 1px solid var(--border);
    }
    .history-item:last-child { border-bottom: none; }
    .history-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.35rem;
    }
    .history-time {
      font-size: 0.75rem;
      font-family: var(--font-mono);
      color: #8b949e;
    }
    .history-snippet {
      font-size: 0.8rem;
      color: var(--text);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Sentinel Watchdog Dashboard</h1>
        <p style="color: #8b949e; font-size: 0.85rem; margin-top: 0.25rem;">
          Microsoft Agent Framework Upstream Monitoring Engine
        </p>
      </div>
      <div id="status-badge" class="badge">Checking status...</div>
    </header>

    <!-- Breaking Changes Alert Banner -->
    <div id="breaking-banner" class="alert-box">
      <h2>⚠️ Critical Breaking Changes Detected</h2>
      <ul id="breaking-details" class="alert-list"></ul>
    </div>

    <div class="grid">
      <!-- Main Content Column -->
      <section class="card">
        <div class="card-title">Latest Intelligence Summary</div>
        <div id="run-metadata" style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent); margin-bottom: 0.75rem;">
          Loading execution data...
        </div>
        <pre id="summary-content">Loading agent assessment...</pre>
      </section>

      <!-- Sidebar History -->
      <section class="card">
        <div class="card-title">Run History (30 Days)</div>
        <ul id="history-container" class="history-list">
          <li class="history-item" style="color: #8b949e;">Fetching logs...</li>
        </ul>
      </section>
    </div>
  </div>

  <script>
    async function loadDashboard() {
      try {
        // 1. Fetch and parse latest run data
        const latestRes = await fetch('./data/latest.json?t=' + Date.now());
        if (latestRes.ok) {
          const latest = await latestRes.json();
          const badge = document.getElementById('status-badge');
          
          if (latest.has_breaking_changes) {
            badge.className = 'badge badge-danger';
            badge.textContent = `${latest.breaking_count} Breaking Changes`;

            // Render breaking changes banner
            const banner = document.getElementById('breaking-banner');
            const detailsList = document.getElementById('breaking-details');
            detailsList.innerHTML = '';
            
            latest.breaking_changes.forEach(change => {
              const li = document.createElement('li');
              li.innerHTML = `<strong>[${change.repo}]</strong> ${change.detail}`;
              detailsList.appendChild(li);
            });
            banner.style.display = 'block';
          } else {
            badge.className = 'badge badge-ok';
            badge.textContent = 'Stable - No Breaking Changes';
          }

          document.getElementById('run-metadata').textContent = `Execution Timestamp: ${latest.timestamp}`;
          document.getElementById('summary-content').textContent = latest.agent_summary || 'No log details generated.';
        }

        // 2. Fetch and render execution history
        const manifestRes = await fetch('./data/manifest.json?t=' + Date.now());
        if (manifestRes.ok) {
          const history = await manifestRes.json();
          const container = document.getElementById('history-container');
          container.innerHTML = '';

          history.forEach(run => {
            const li = document.createElement('li');
            li.className = 'history-item';

            const badgeHtml = run.has_breaking_changes
              ? `<span class="badge badge-danger" style="font-size:0.7rem; padding: 0.15rem 0.4rem;">${run.breaking_count} Breaking</span>`
              : `<span class="badge badge-ok" style="font-size:0.7rem; padding: 0.15rem 0.4rem;">Stable</span>`;

            li.innerHTML = `
              <div class="history-meta">
                <span class="history-time">${run.timestamp.replace('T', ' ').slice(0, 16)} UTC</span>
                ${badgeHtml}
              </div>
              <div class="history-snippet">${run.summary_snippet}</div>
            `;
            container.appendChild(li);
          });
        }
      } catch (err) {
        console.error('Failed to parse watchdog dashboard data:', err);
      }
    }

    loadDashboard();
  </script>
</body>
</html>
```

---

## 🧪 4. Key Verification Checks

### 1. Verify JSON Generation Locally
```bash
python agent_watchdog.py --dry-run
```
Inspect `docs/data/latest.json` to verify that `has_breaking_changes` and `breaking_count` are present and properly typed as JSON Booleans and integers.

### 2. Local UI Preview
```bash
cd docs
python -m http.server 8000
```
Open `http://localhost:8000` to confirm that:
* When `has_breaking_changes: false`, the badge displays green `Stable - No Breaking Changes`.
* When `has_breaking_changes: true`, the red alert banner appears and the badge renders `${count} Breaking Changes`.

### 3. Automated Push in Actions
The GitHub Actions workflow `.github/workflows/watchdog-dashboard.yml` automatically stages and pushes `docs/data/` changes:
```yaml
git add docs/data/ briefings/
if ! git diff --cached --quiet; then
  git commit -m "chore(telemetry): update dashboard manifests [$(date +'%Y-%m-%d')]"
  git push
fi
```
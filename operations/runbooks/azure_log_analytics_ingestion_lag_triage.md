# Operational Runbook: Azure Log Analytics Ingestion Lag & Spool Queue Drain

**Severity:** P2 / SIEM Audit Lag  
**Target Systems:** Watchdog Agent, Azure Data Collector API, Spool Queue

## Diagnostic Workflow

### 1. Check Local Spool Buffer Depth
```bash
python -m agent_watchdog --check-spool-depth
```
If local buffered records > 100:

### 2. Verify Azure Monitor Workspace Ingestion Status
```bash
az monitor log-analytics workspace show \
  --resource-group watchdog-rg \
  --workspace-name watchdog-analytics \
  --query 'properties.retentionInDays'
```

### 3. Step-by-Step Remediation
1. Verify outbound HTTPS connectivity to Azure Data Collector:
   ```bash
   curl -I https://watchdog-analytics.ods.opinsights.azure.com
   ```
2. Trigger manual spool buffer drain:
   ```bash
   python -m agent_watchdog --drain-spool
   ```

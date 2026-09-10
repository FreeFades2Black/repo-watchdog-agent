# 🖥️ Azure Portal Executive Operations & Cost Dashboard

This guide details how to import and deploy the **Sentinel AI Foundry & Watchdog Executive Dashboard** into your Azure Portal (`portal.azure.com`). 

Once loaded, this shared dashboard automatically appears on your **Azure Portal Home / Dashboard** view, showcasing:
1. **What has been built:** Full resource inventory across AI Foundry, AI Search, Key Vault, Storage, and Sentinel Watchdog.
2. **What has been ran:** Model invocation rates, Prompt Shield / RAI policy blocks, search query latency, and audit logs.
3. **Cost in compute and storage:** Accumulated month-to-date actual spend, cost breakdown by service (Compute vs Storage vs AI Search), blob storage capacity, and transaction volumes.

---

## 📸 Dashboard Visual Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🛰️ SENTINEL AI FOUNDRY & WATCHDOG OPERATIONS CENTER                [Time Range: Past 24h] │
├──────────────────────────────────────────┬─────────────────────────┬───────────────────┤
│ [1] Executive Architecture & Portals     │ [2] MTD Accumulated Cost│ [3] Cost by Svc   │
│ • Azure AI Foundry & Model Deployments   │     (Actual Daily Trend)│     (AI vs Storage│
│ • AI Search Vector Knowledge Base        │      Area Chart (USD)   │      Bar Chart    │
│ • Live Tactical Watchdog UI Links        │                         │                   │
├─────────────────────────┬────────────────┴────────┬────────────────┴───────────────────┤
│ [4] AI Compute Metrics  │ [5] AI Search Metrics   │ [6] Key Vault API Activity         │
│ • Total Model Calls     │ • Queries Per Second    │ • Key & Secret Retrievals          │
│ • Successful vs Blocked │ • Search Latency (ms)   │ • Zero-Trust Auth Latency          │
├─────────────────────────┼─────────────────────────┼────────────────────────────────────┤
│ [7] Storage Capacity    │ [8] Storage Transactions│ [9] Log Analytics Health           │
│ • Blob Used Capacity    │ • Ingress / Egress (MB) │ • Telemetry Ingestion Rate         │
│ • Hot/Cool Tier Bytes   │ • Transaction Operations│ • Red-Team Gate Audit Heartbeat    │
├─────────────────────────┴─────────────────────────┴────────────────────────────────────┤
│ [10] Architecture & Operational Run Matrix (Summary Table of Deployed Cloud Resources) │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Option 1: 1-Click Instant Upload in Azure Portal (Easiest)

You can import the dashboard directly through your web browser without running any CLI commands:

1. Open your browser and navigate to **[https://portal.azure.com](https://portal.azure.com)**.
2. In the left navigation or top search bar, click on **Dashboard** (or go to `portal.azure.com/#home` and select **Dashboard**).
3. In the top toolbar of the Dashboard view, click the **Upload** button.
   *(Located next to "+ New dashboard" and "Download")*.
4. In the file dialog, select:
   ```plaintext
   repo-watchdog-agent/azure/portal-dashboard.json
   ```
5. The portal will immediately parse the tiles and render the complete executive operations and cost dashboard!
6. Click **Save** in the top toolbar.

---

## ⚡ Option 2: Deploy via Azure CLI / PowerShell

To deploy the dashboard as a permanent, shared Azure Resource (`Microsoft.Portal/dashboards`) in your subscription:

```powershell
# Run the automated PowerShell deployment script:
cd C:\Users\FreeF\repo-watchdog-agent\azure
.\deploy-dashboard.ps1 -ResourceGroupName "rg-sentinel-operations" -Location "eastus2"
```

Or deploy directly with Azure CLI:
```bash
az deployment group create \
  --resource-group rg-sentinel-operations \
  --template-file azure/azuredeploy.json \
  --parameters dashboardName="Sentinel-AI-Foundry-Operations-Dashboard"
```

---

## 🏗️ Option 3: Deploy via Terraform

The dashboard is integrated as a native Terraform module in the companion repository **`foundry-responsible-agent-sentinel`**:

```bash
cd C:\Users\FreeF\foundry-responsible-agent-sentinel\terraform
terraform init
terraform apply -target=module.dashboard
```

Terraform provisions `azurerm_portal_dashboard.sentinel_dashboard` and outputs the resource ID:
```
Outputs:
azure_portal_dashboard_id = "/subscriptions/65684f2a.../resourceGroups/rg-sentinel.../providers/Microsoft.Portal/dashboards/Sentinel-AI-Operations-Dashboard"
```

---

## ⚙️ How to Make the Dashboard Show Up on Portal Home

To have this dashboard appear automatically every time you visit **portal.azure.com**:

1. In the Azure Portal, click the **Gear (Settings)** icon in the upper right header.
2. Select **Appearance + startup views**.
3. Under **Startup view**, change the selection from **Home** to **Dashboard**.
4. Click **Apply**.
5. When you visit `https://portal.azure.com`, the Sentinel Operations & Cost Dashboard will be your primary home view!

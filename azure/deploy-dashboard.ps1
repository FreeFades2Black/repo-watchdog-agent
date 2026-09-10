<#
.SYNOPSIS
    Deploys the Sentinel AI Foundry & Watchdog Executive Dashboard to Azure.

.DESCRIPTION
    Provisions a shared Azure Portal Dashboard (Microsoft.Portal/dashboards) into your
    target Azure Resource Group, showcasing deployed resources, cost tracking (compute vs storage),
    AI search queries, and execution health.

.PARAMETER ResourceGroupName
    The name of the Azure Resource Group to deploy the dashboard to. Defaults to "rg-sentinel-foundry".

.PARAMETER Location
    The Azure region. Defaults to "eastus2".

.EXAMPLE
    .\deploy-dashboard.ps1 -ResourceGroupName "rg-sentinel-operations"
#>

[CmdletBinding()]
param(
    [string]$ResourceGroupName = "rg-sentinel-operations",
    [string]$Location = "eastus2",
    [string]$DashboardName = "Sentinel-AI-Foundry-Operations-Dashboard"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " 🛰️ Deploying Sentinel Azure Portal Executive Dashboard" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Verify Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI (az) is not installed. Install it from https://aka.ms/installazurecliwindows"
}

# 2. Check Azure authentication status
Write-Host "[+] Verifying Azure authentication status..." -ForegroundColor Yellow
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "[!] Azure token expired or not logged in. Initiating interactive login..." -ForegroundColor Yellow
    az login --use-device-code
    $account = az account show --output json | ConvertFrom-Json
}

Write-Host "[✓] Authenticated to Azure:" -ForegroundColor Green
Write-Host "    - Subscription: $($account.name) ($($account.id))" -ForegroundColor Gray
Write-Host "    - Tenant:       $($account.tenantId)" -ForegroundColor Gray
Write-Host "    - User:         $($account.user.name)" -ForegroundColor Gray

# 3. Ensure Resource Group exists
Write-Host "[+] Ensuring Resource Group '$ResourceGroupName' exists in '$Location'..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output table

# 4. Deploy ARM Template
$templatePath = Join-Path $PSScriptRoot "azuredeploy.json"
Write-Host "[+] Deploying Dashboard ARM template from '$templatePath'..." -ForegroundColor Yellow

$deployment = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file $templatePath `
    --parameters dashboardName=$DashboardName location=$Location `
    --output json | ConvertFrom-Json

if ($deployment.properties.provisioningState -eq "Succeeded") {
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host " [✓] Azure Dashboard Deployed Successfully!" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host "Dashboard Resource Name: $DashboardName" -ForegroundColor White
    Write-Host "Resource Group:          $ResourceGroupName" -ForegroundColor White
    Write-Host "Direct Portal URL:       https://portal.azure.com/#@$($account.tenantId)/resource/subscriptions/$($account.id)/resourceGroups/$ResourceGroupName/providers/Microsoft.Portal/dashboards/$DashboardName" -ForegroundColor Cyan
    Write-Host "`nTo view it when visiting portal.azure.com:" -ForegroundColor Yellow
    Write-Host "1. Navigate to https://portal.azure.com" -ForegroundColor White
    Write-Host "2. Click 'Dashboard' in the top/left navigation." -ForegroundColor White
    Write-Host "3. In the dashboard dropdown, select '$DashboardName'." -ForegroundColor White
    Write-Host "4. Click the gear (Settings) icon -> Appearance + startup views -> Set startup view to 'Dashboard' if you want it to appear immediately upon login." -ForegroundColor White
} else {
    Write-Error "Deployment finished with state: $($deployment.properties.provisioningState)"
}

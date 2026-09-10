# 🛠️ Ansible Automation — Autonomous Sentinel Node Deployment

This Ansible role provisions and orchestrates **Repo Watchdog Agent** on Linux nodes (Arch Linux, Ubuntu/Debian, Fedora/RHEL). It automates the creation of isolated virtual environments, deployment of environment secrets, and registration of systemd timers for unattended, scheduled daily monitoring.

---

## 🏗️ Architecture

```
[Ansible Control Node (Local or Bastion)]
              │
              ├─► Connects via SSH to Sentinel Node (e.g., omarchy)
              ├─► Installs OS packages & Python 3 runtime
              ├─► Configures /etc/repo-watchdog/watchdog.env
              ├─► Deploys /etc/systemd/system/repo-watchdog.service
              ├─► Deploys /etc/systemd/system/repo-watchdog.timer (Daily 06:00 UTC)
              └─► Enables & starts systemd timer
```

---

## 📂 Layout

```
ansible/
├── ansible.cfg                    # Ansible default settings
├── inventory.ini                  # Target host definitions
├── deploy-sentinel-node.yml       # Master playbook
├── README.md                      # Usage documentation
└── roles/
    └── watchdog_sentinel/
        ├── defaults/main.yml      # Configurable variables & paths
        ├── tasks/main.yml         # Provisioning tasks
        ├── templates/
        │   ├── repo-watchdog.service.j2 # Systemd service unit
        │   ├── repo-watchdog.timer.j2   # Systemd timer unit
        │   └── watchdog.env.j2          # Environment variables
        └── handlers/main.yml      # Systemd reload & restart triggers
```

---

## 🚀 Quickstart Usage

### 1. Execute Playbook Locally (e.g., on target host)
```bash
ansible-playbook -i inventory.ini deploy-sentinel-node.yml --connection=local --limit localhost
```

### 2. Execute Playbook Remotely (e.g., targeting `omarchy`)
```bash
ansible-playbook -i inventory.ini deploy-sentinel-node.yml --limit omarchy
```

### 3. Passing Secrets at Runtime
You can pass live LLM credentials or tokens via `--extra-vars` or an Ansible Vault:
```bash
ansible-playbook -i inventory.ini deploy-sentinel-node.yml \
  --limit omarchy \
  -e "github_token=ghp_xxxxxx" \
  -e "azure_openai_api_key=3f8a9...b4c2" \
  -e "azure_openai_endpoint=https://aoai-sentinel.openai.azure.com/"
```

---

## 🔍 Verification & Inspection on the Target Node

Once deployed, you can verify the status of the timer and service on the target machine:

### 1. Check Systemd Timer Status
```bash
systemctl status repo-watchdog.timer
systemctl list-timers --all | grep repo-watchdog
```

### 2. Trigger an Immediate Test Run
```bash
sudo systemctl start repo-watchdog.service
```

### 3. Inspect Live Systemd Execution Logs
```bash
journalctl -u repo-watchdog.service -n 50 -f
```

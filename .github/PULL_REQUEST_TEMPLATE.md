## Repo Watchdog Operational Overview
*Describe modifications to webhook auditors, compliance checks, or Azure SIEM ingestion.*

- [ ] Webhook Event Handler (Push, PR, Release)
- [ ] Branch Protection Compliance Auditor
- [ ] Azure Log Analytics Ingestion & Buffer
- [ ] Security Telemetry Dashboard Export

## Safety & HMAC Verification
- **HMAC Verification Tested:** Confirmed invalid signatures return HTTP 401 Unauthorized.
- **Rate-Limit Handling:** Verified token-bucket pacing prevents secondary rate-limit tripwires.

## Verification Checklist
- [ ] Test suite passed (7/7 tests): `python -m pytest tests/ -v`
- [ ] Zero hardcoded secrets or webhook tokens committed

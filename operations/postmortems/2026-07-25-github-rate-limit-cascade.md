# Incident Post-Mortem: GitHub Secondary Rate-Limit Triggering Audit Delay

**Incident Date:** 2026-07-25  
**Impact Duration:** 25 minutes  
**Severity:** SEV-3  
**Root Cause:** A simultaneous branch push event across 40 repositories caused the watchdog agent to dispatch 160 concurrent GitHub API calls checking branch rulesets without client-side pacing, triggering GitHub secondary rate limits (HTTP 403).

## Timeline
* **15:00 UTC:** Mass repository sync triggered webhook burst.
* **15:02 UTC:** GitHub returned `403 Forbidden: You have exceeded a secondary rate limit`.
* **15:10 UTC:** Watchdog agent paused invocations for 180 seconds.
* **15:18 UTC:** Patched dispatcher with a token-bucket rate limiter (max 10 requests/sec).
* **15:25 UTC:** All backlog audit checks completed successfully.

## Corrective Actions
1. Implemented token-bucket rate limiting in `agent_watchdog.py`.
2. Added exponential jitter to API retries based on `retry-after` header.

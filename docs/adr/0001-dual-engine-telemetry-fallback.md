# ADR-0001: Dual-Engine Telemetry Fallback (Azure Log Analytics + Local Encrypted Ring Buffer)

**Status:** Accepted  
**Date:** 2026-05-20  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Our security watchdog agent audits branch protection, secret leaks, and PR approvals across GitHub repositories. Telemetry must be sent to Azure Log Analytics Workspace for enterprise SIEM visibility, but watchdog operations must never drop audit records during Azure WAN network outages.

## 2. Options Considered
* **Option A: Synchronous Direct Ingestion to Azure Log Analytics**
  - *Evaluation:* Simple, but any network glitch or Azure 503 response drops audit records or blocks incoming webhook processing.
* **Option B: Dual-Engine Architecture with Local Encrypted Ring Buffer Fallback**
  - *Evaluation:* Primary path streams directly to Azure Data Collector API; on failure, records spool to a local encrypted SQLite/JSONL ring buffer with an automated background replay worker.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (Dual-Engine Fallback)**.  
**Trade-Off Accepted:** Requires local disk storage for the spool queue; requires background thread management to drain the buffer upon reconnection.

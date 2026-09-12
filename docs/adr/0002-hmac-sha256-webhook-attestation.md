# ADR-0002: Mandatory HMAC-SHA256 Webhook Payload Attestation

**Status:** Accepted  
**Date:** 2026-06-07  
**Lead Architect:** William Free Hall (Free) <whall4.wh@gmail.com>

## 1. Context & Operational Challenge
Public webhook endpoints are exposed to denial-of-service attacks, spoofed webhook payloads, and replay attempts from malicious actors.

## 2. Options Considered
* **Option A: IP Whitelisting against GitHub Meta API**
  - *Evaluation:* GitHub publishes hook IP ranges, but ranges change dynamically and IP whitelisting does not prevent spoofing within shared cloud hosting providers.
* **Option B: Cryptographic HMAC-SHA256 Signature Verification (`X-Hub-Signature-256`)**
  - *Evaluation:* Every payload is signed with a shared high-entropy secret; constant-time string comparison (`hmac.compare_digest`) prevents timing attacks and guarantees payload authenticity.

## 3. Decision & Trade-Off Accepted
We adopted **Option B (HMAC-SHA256 Attestation)**.  
**Trade-Off Accepted:** Incurs ~0.5ms cryptographic hash calculation per webhook invocation; eliminates all unauthenticated payload processing.

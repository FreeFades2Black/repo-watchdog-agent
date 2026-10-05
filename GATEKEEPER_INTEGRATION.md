# OCaml Gatekeeper Ingress Integration Spec

## 1. Role & Objective
Integrate `ocaml-event-engine` as an upstream, zero-exception validation and deduplication filter.
No raw input data may reach downstream pipelines without first passing this verification gate.

## 2. Interface Contract
- **Ingress:** Newline-delimited JSON streamed into `stdin`.
- **Egress:** Deterministic JSON status from `stdout`:
  - `{"status":"processed","id":"<id>"}`: Proceed with downstream execution.
  - `{"status":"duplicate","id":"<id>"}`: Discard immediately; log debug trace.
  - `{"status":"invalid","id":"<id>","error":"<reason>"}`: Route payload to dead-letter log (`dead_letter_events.jsonl`).

## 3. Execution Adapter Requirements
- Author a dedicated wrapper module (`gatekeeper_client.py` or shell wrapper).
- Support fallback: prefer local `./bin/ocaml-event-engine`, fall back to `docker run -i --rm ghcr.io/freefades2black/ocaml-event-engine:latest`.
- Must handle interactive I/O with continuous flushing (`bufsize=1`).

# network diagnostics agent
Home and small office users frequently experience slow or unstable networks 
but lack the tools or expertise to determine whether the cause is local 
WiFi, DNS, the routers, or the upstream ISP. Existing tools expose raw 
metrics without interpretation.

This project aims to provide automated, explainable netwrok diagnostics 
that run entirely locally and require no networking expertise to intrepret 
and understand. 

## Design Principles
- Local-first: no cloud dependency by default
- Observability-first: measure → infer → explain
- Explainability over raw metrics
- Failure-aware: probes may partially fail
- Low dependency footprint
- Designed for extension, not one-off scripts

## Architecture Overview

The system is composed of four conceptual layers:

1. Probes  
   Periodic measurements (ICMP, DNS, HTTP, TCP)

2. Storage  
   Local time-series persistence with safe writes

3. Analysis  
   Deterministic heuristics that infer probable root causes

4. Reporting  
   Human-readable CLI summaries and static HTML reports

## Features

- Periodic ICMP latency and packet-loss measurement
- DNS resolution latency and failure tracking
- HTTP(S) endpoint latency probing
- Automated diagnosis with supporting evidence
- Daily and weekly summary reports
- Static HTML report generation

## Installation 
Requirements: 
- Python 3.11+

## License
MIT License. See LICENSE file for details.
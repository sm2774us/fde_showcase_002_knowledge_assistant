---
title: Incident Response Runbook
access: internal
owner: Security Operations
---
# Incident Response

## Severity levels
| Severity | Definition | Response time | Update cadence |
|---|---|---|---|
| Sev-1 | customer-facing outage or confirmed data exposure | 15 minutes | every 30 minutes |
| Sev-2 | degraded critical service | 1 hour | every 2 hours |
| Sev-3 | non-critical defect, failed integration delivery | next business day | daily |

## Escalation
The on-call engineer pages the incident commander for any Sev-1. For suspected data exposure involving an AI agent, disable the affected agent topic first, then preserve logs, then notify the privacy office within 24 hours.

---
title: AI Agent Governance Standard
access: internal
owner: Model Risk Management
---
# AI Agent Governance

## Action approval thresholds
Agents may issue refunds up to $250 automatically. Refunds above $250 and up to $5,000 require supervisor approval. Refunds above $5,000 require two-person approval from supervisor and finance. Customer-visible messages sent during the first 90 days of a new agent must be reviewed by a human.

## Model allowlist
Only models on the approved list may be used, and each must run with zero data retention. Model or prompt changes need a passing evaluation run on the 100-case regression set before release.

## Logging and audit
Every tool call is logged with the user, agent version, inputs, outputs and approval decision. Logs are immutable and retained for 7 years for SOX purposes.

## Kill switch
Operations can disable any agent topic in under 5 minutes through the feature-flag console.

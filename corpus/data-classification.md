---
title: Data Classification Policy
access: internal
owner: Data Governance
---
# Data Classification

## Classes
| Class | Examples | AI usage |
|---|---|---|
| Public | marketing pages, published rates | any approved model |
| Internal | runbooks, org charts | approved models with zero data retention |
| Confidential | customer names, emails, account balances | masked before prompting; approved models only |
| Restricted | card numbers (PAN), national IDs, health data | never sent to a third-party model |

## PII handling in AI systems
Mask or tokenize Confidential data before it enters a prompt. Prompts and model outputs are logged with hashed customer identifiers only. Raw card numbers must never appear in prompts, traces or vector stores. Deletion requests must also purge derived embeddings within 30 days.

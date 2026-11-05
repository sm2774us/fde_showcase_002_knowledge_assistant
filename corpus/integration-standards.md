---
title: Integration Standards v4
access: internal
owner: Integration Architecture
---
# Integration Standards

## Webhooks and retries
All outbound webhooks must be idempotent and carry an `Idempotency-Key` header. Receivers must acknowledge within 5 seconds with HTTP 2xx.

| Attempt | Delay before retry | Notes |
|---|---|---|
| 1 | immediate | first delivery |
| 2 | 30 seconds | exponential backoff starts |
| 3 | 5 minutes | |
| 4 | 1 hour | |
| 5 | 6 hours | final attempt, then dead-letter queue |

Failed webhooks after attempt 5 land in the dead-letter queue and raise a Sev-3 ticket in ServiceNow.

## REST APIs
Client timeouts are 10 seconds for reads and 30 seconds for writes. Use cursor pagination with a maximum page size of 200. Rate limit is 100 requests per minute per client, returned as HTTP 429 with a Retry-After header.

## Event streaming
Kafka topics use the naming pattern `domain.entity.event.v1`. Consumers must tolerate duplicate delivery. Schema changes require a backward-compatible Avro evolution reviewed by the architecture board.

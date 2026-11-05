---
title: Data 360 Ingestion Runbook
access: internal
owner: Data Platform
---
# Data 360 Ingestion

## Core banking files
Core banking account and closure files arrive by SFTP every night at 02:00 UTC and are ingested into Data 360 by 03:30 UTC. Transaction history is shared zero-copy from Snowflake and is refreshed hourly.

## Mapping
Source records map to the unified individual using a hashed customer identifier. Match rules prefer exact email plus date of birth, then phone plus postal code.

## Failure handling
If the nightly file is missing by 04:00 UTC, the pipeline retries three times at 15-minute intervals and then opens a Sev-3 ticket. Agents must show a data freshness warning when the latest file is older than 26 hours.

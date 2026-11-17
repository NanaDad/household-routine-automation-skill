# Sanitized automation catalog

This catalog summarizes enabled workflow types observed in one OpenClaw installation. Exact cron expressions, one-time dates, agent IDs, job IDs, recipients, school/class names, addresses, and repository paths are intentionally excluded. Configure cadence and local context on the target installation.

| Workflow | Generic cadence | Core actions | Safety/completion gate |
|---|---|---|---|
| School notice scout | Daily, weekday/weekend branches | Authenticate through protected session/API; find relevant new posts; read bodies **and all attachments** (download images, extract text/facts) | Do not infer no updates from failed login; never text-body-only when attachments exist; report lookup failures; update seen from send-record checkpoints |
| School pre-brief check | Daily before next-day brief | Detect new notices, preparation items, and schedule changes including image-only facts | Separate new candidates from seen posts; report partial status honestly |
| School album processing | Daily or on request | Enumerate recent albums (not only newest), download attachments, validate counts/hashes, classify with locked score bands, archive approved media, send through configured channels | Human identity confirmation; no archive/send for unsure faces; silent `NO_REPLY` when already processed / no new album; never spam already_processed |
| Weekday morning checklist | Weekdays | Secretary-style today-only pack list, activities (where+what), meals full split, weather, parent deadlines | Do not leak tomorrow-only details; label fallback data |
| Evening family brief | Daily | Next-day secretary-style schedule, preparation, meals, weather, exceptions, near-term heads-up | Preserve full detail requirements; one send attempt per channel unless a safe retry is proven |
| Weekend weather note | Weekends | Short current-day forecast and practical tip | Use configured source and fallback; never forward raw command output |
| Activity reminder | Weekly/event-based | Remind about upcoming activity and required items | Verify date/time from private calendar/config; use approved contacts only |
| Local face-model refresh | Quarterly configured | Refresh local recognition reference from recent approved examples using growth-aware three-month buckets; keep negative/lookalike refs | Human approval; high-confidence/manual-baseline gate; bounded refs, backup/rollback; local caches only; dedupe exact duplicate embeddings. Details: `references/face-model-and-growth.md` |
| Market summary | Weekdays | Read-only market data and concise digest | No trade/order action; state freshness and source failures |
| Service discount report | Daily | Read-only local history and outcome summary | Do not expose account/customer identifiers; distinguish unknown/error from failure |
| Travel-seat monitor | Time-boxed recurring monitor | Search configured outbound/return conditions and report viable pairs | Never reserve/pay automatically; stop and alert on automation detection/access block |
| Memory maintenance | Scheduled | Consolidate approved local notes into durable memory | Do not export or commit private memory; preserve provenance and omit secrets |

## Per-run status vocabulary

- success: all required checks, destinations, and archive verification passed.
- partial: some work succeeded, but one or more required stages are unresolved.
- unknown: timeout or missing evidence means the external effect may have completed; do not retry blindly.
- blocked: permission, authentication, or service restriction needs operator action.
- no_change: checks completed and there was nothing new; this is not an error and should not notify unless configured.
- needs_owner_review: candidates exist but identity is unconfirmed; owner channel only.

## Channel policy (generic)

- Shared family notices/briefs: configured dual-delivery when enabled.
- Owner review/correction traffic: owner channel only; do not auto-relay to the other session.
- Owner alerts for internal failures: owner channel only.

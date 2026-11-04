# Sanitized automation catalog

This catalog summarizes enabled workflow types observed in one OpenClaw installation. Exact cron expressions, one-time dates, agent IDs, job IDs, recipients, school/class names, addresses, and repository paths are intentionally excluded. Configure cadence and local context on the target installation.

| Workflow | Generic cadence | Core actions | Safety/completion gate |
|---|---|---|---|
| School notice scout | Daily, weekday/weekend branches | Authenticate through protected session; find relevant new posts; read bodies and attachments | Do not infer no updates from failed login; report lookup failures; update seen only after required delivery verification |
| School pre-brief check | Daily before next-day brief | Detect new notices, preparation items, and schedule changes | Separate new candidates from seen posts; report partial status honestly |
| School album processing | Daily or on request | Enumerate all attachments, download locally, validate counts/hashes, classify candidates, archive approved media, send through configured channels | Human identity confirmation; no archive/send for ambiguous faces; verify all counts and channels before success |
| Weekday morning checklist | Weekdays | Today-only preparation, activities, meals, weather | Do not leak tomorrow-only details; label fallback data |
| Evening family brief | Daily | Next-day schedule, preparation, meals, weather, exceptions | Preserve full detail requirements; one send attempt per channel unless a safe retry is proven |
| Weekend weather note | Weekends | Short current-day forecast and practical tip | Use configured source and fallback; never forward raw command output |
| Activity reminder | Weekly/event-based | Remind about upcoming activity and required items | Verify date/time from private calendar/config; use approved contacts only |
| Local face-model refresh | Quarterly configured | Refresh local recognition reference from recent approved examples using a growth-aware three-month bucket scheme | Human approval; high-confidence/manual-baseline gate; bounded refs, backup/rollback; local caches only. Details and schedule verification: references/face-model-and-growth.md |
| Market summary | Weekdays | Read-only market data and concise digest | No trade/order action; state freshness and source failures |
| Service discount report | Daily | Read-only local history and outcome summary | Do not expose account/customer identifiers; distinguish unknown/error from failure |
| Travel-seat monitor | Time-boxed recurring monitor | Search configured outbound/return conditions and report viable pairs | Never reserve/pay automatically; stop and alert on automation detection/access block |
| Memory maintenance | Scheduled | Consolidate approved local notes into durable memory | Do not export or commit private memory; preserve provenance and omit secrets |

## Per-run status vocabulary

- success: all required checks, destinations, and archive verification passed.
- partial: some work succeeded, but one or more required stages are unresolved.
- unknown: timeout or missing evidence means the external effect may have completed; do not retry blindly.
- blocked: permission, authentication, or service restriction needs operator action.
- no_change: checks completed and there was nothing new; this is not an error.

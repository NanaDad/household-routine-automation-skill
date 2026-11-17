# Sanitized automation catalog

Workflow families for a **kindergarten/preschool parent assistant**. Exact cron expressions, dates, agent IDs, job IDs, recipients, school brand/class names, addresses, and host paths are excluded. Configure cadence and local context on the target machine.

## Primary (child-care)

| Workflow | Generic cadence | Core actions | Safety/completion gate |
|---|---|---|---|
| School notice scout | Daily; weekday/weekend depth branches | Auth via protected session/API; find relevant new parent posts; read bodies **and all attachments** (download images; extract place/date/prep) | Failed login ≠ “no updates”; never text-only when attachments exist; seen updates from send-record checkpoints |
| School pre-brief check | Daily before next-day brief | Detect notices, preparation items, schedule changes including image-only facts | Separate new vs seen; honest partial status |
| School album processing | Daily or on request | Scan several recent albums; download complete assets; validate counts/hashes; local face score bands; archive approved only; deliver on configured channels | Human identity confirmation; no archive/send for unsure faces; `NO_REPLY` when already processed / no new album |
| Weekday morning checklist | Weekdays | Today-only secretary brief: where+what, pack list, classes, parent deadlines, full meals, weather | No tomorrow-only leak; label fallback data |
| Evening family brief | Daily | Next-day secretary brief + near-term heads-up | Full meal/prep detail rules; safe per-channel retry policy |
| Activity reminder | Weekly/event-based | Upcoming class/event + required items | Time from private calendar/config; approved contacts only |
| Local face-model refresh | Quarterly (configured) | Growth-aware reference refresh; negative/lookalike refs; dedupe exact duplicate embeddings | Human approval; min-score/manual baseline; backup/rollback; local caches only |

## Supporting

| Workflow | Generic cadence | Core actions | Safety/completion gate |
|---|---|---|---|
| Weekend weather note | Weekends | Short forecast + practical tip | Configured source/fallback; no raw command dumps |
| Market summary | Weekdays | Read-only digest | No trades |
| Service status/discount report | Daily | Read-only outcome summary | No account identifiers in reports |
| Travel-seat monitor | Time-boxed | Report viable pairs only | Never auto reserve/pay; stop on bot detection |
| Memory maintenance | Scheduled | Consolidate approved local notes | Do not export private memory |

## Status vocabulary

- `success` — required checks + destinations + archive verification passed  
- `partial` — some stages unresolved  
- `unknown` — timeout / missing evidence; do not blind-retry  
- `blocked` — auth/permission/service restriction needs operator  
- `no_change` — healthy idle (prefer silence)  
- `needs_owner_review` — identity unconfirmed; owner channel only  

## Channel policy (generic)

- Shared family notices/briefs: optional dual-delivery when configured  
- Owner review/correction: owner channel only; do not auto-relay  
- Internal failures: owner alert channel only  

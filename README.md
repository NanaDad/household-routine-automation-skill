# Household Routine Automation Skill

A portable OpenClaw skill for recurring household and personal-assistant workflows. This repository intentionally contains procedures and generic templates only; it does not contain any user's live automation configuration, credentials, media, or identity data.

## Included workflow families

- School notice and album checks (API-first detail + attachment inspection)
- Secretary-style family checklists, next-day briefs, weather, and activity reminders
- Local face-classifier maintenance with locked score bands and human review gates
- Read-only market and service-status reporting
- Travel availability monitoring without automatic booking
- Private memory maintenance

## Face recognition (local only)

Documents the InsightFace `buffalo_l` local classifier path, growth-aware reference refresh, negative/lookalike veto, and operator-locked score bands (confirmed ≥ 0.55, needs-confirm 0.45–0.55, ignore below 0.45). No embeddings, photos, child names, or archive paths are stored in this repository.

## Privacy design

All people, contacts, locations, schedules, account identifiers, provider credentials, local paths, and media are represented by runtime placeholders or omitted. Do not add live configuration, status files, logs, screenshots, credentials, or personal media. Keep the repository private.

## Use

Copy this skill directory into an authorized OpenClaw skill location, then adapt the private placeholders on the target machine. Keep actual schedules, destinations, credentials, and storage paths in local protected configuration—not in the skill or Git history.

## Validation

Run `scripts/validate-redaction.sh` before committing. Also run OpenClaw `skill-creator` quick validation. Review every diff for private data; scanners are guardrails, not a substitute for review.

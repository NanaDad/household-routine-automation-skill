# Household Routine Automation Skill

A portable OpenClaw skill for recurring household and personal-assistant workflows. This repository intentionally contains procedures and generic templates only; it does not contain the user's live automation configuration.

## Included workflow families

- School notice and album checks
- Family checklists, next-day briefs, weather, and activity reminders
- Local face-classifier maintenance with human review gates
- Read-only market and service-status reporting
- Travel availability monitoring without automatic booking
- Private memory maintenance

## Privacy design

All people, contacts, locations, schedules, account identifiers, provider credentials, local paths, and media are represented by runtime placeholders or omitted. Do not add live configuration, status files, logs, screenshots, credentials, or personal media. Use a private repository when storing any future operator-specific extensions.

## Use

Copy this skill directory into an authorized OpenClaw skill location, then adapt the private placeholders on the target machine. Keep actual schedules, destinations, credentials, and storage paths in local protected configuration—not in the skill or Git history.

## Validation

Run scripts/validate-redaction.sh before committing. Review every diff for private data; the scanner is a guardrail, not a substitute for review.

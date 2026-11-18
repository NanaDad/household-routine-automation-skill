# Kindergarten Parent Assistant Skill

Portable OpenClaw skill for **kindergarten / preschool parent routines** and related household assistant workflows.

This repository is procedure-only. It does **not** contain any family's live config, credentials, child identity, school name, photos, or face embeddings.

## What this skill is mainly for

Parent-side automation around a child's school day:

1. **School notice pipeline**  
   Scout new parent notices → read full detail → **inspect every attached image/file** (places, prep lists, schedules often live only in photos) → draft a clear family message → send on configured channels → dedupe by send-record.

2. **School photo album pipeline**  
   Find new albums → download complete attachments → local face match with locked score bands → split **confirmed / needs-confirm / ignore** → owner review on the owner channel → archive only approved child photos → verified delivery.

3. **Secretary-style daily briefs**  
   Morning/evening checklists that review: special activities (**where + what**), pack list & clothing, regular classes, parent deadlines, weather, full meals, and 2–3 day heads-up.

4. **Local child face classifier maintenance**  
   Offline InsightFace-based enroll/sort/refresh, negative lookalike veto, growth buckets, and human confirmation gates. See `references/face-extract-store-use.md`.

Secondary optional families (same skill, less central): read-only market/service digests, travel-seat monitoring without auto-booking, private memory maintenance.

## Design principles

- **Child-care first**: notices, albums, prep, and reminders are the core product surface.
- **Privacy by construction**: no child names, bot names, school brand names, phones, or credentials in git.
- **Human confirmation for identity**: classifier scores are candidates only.
- **Attachments matter**: never finish a notice from plain text when images exist.
- **Quiet when idle**: no spam for already-processed albums / no-new days.

## Face recognition (local only)

- Detect faces → **512-D embeddings** → store vectors locally (not photos in the DB)
- Match with cosine similarity + optional time-bucket weighting
- Locked bands: confirmed ≥ 0.55 · needs-confirm 0.45–0.55 · ignore < 0.45
- Growth refresh + negative veto documented under `references/`

## Repo layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Entry procedure + operating rules |
| `references/automation-catalog.md` | Workflow families and completion gates |
| `references/face-model-and-growth.md` | Model provenance + growth refresh |
| `references/face-extract-store-use.md` | Extract → store → use pipeline |
| `references/privacy-and-security.md` | Privacy boundaries |
| `templates/private-config.example.yaml` | Unpopulated local config placeholders |
| `scripts/validate-redaction.sh` | Pre-commit PII/secret guardrail |

## Use

1. Install into an authorized OpenClaw skill directory.
2. Copy `templates/private-config.example.yaml` to an **untracked** local file and fill placeholders on-device.
3. Keep schedules, recipients, school login refs, and archive roots in protected runtime config only.

## Validation

```bash
bash scripts/validate-redaction.sh
python3 <openclaw>/skills/skill-creator/scripts/quick_validate.py .
```

Manual diff review is still required. The scanner blocks household identity labels and credential patterns, but it is not a substitute for reading the staged tree.

## License note

InsightFace library code is MIT; upstream pretrained packs such as `buffalo_l` are documented as non-commercial research weights. This skill assumes private family use unless you obtain an appropriate commercial license.

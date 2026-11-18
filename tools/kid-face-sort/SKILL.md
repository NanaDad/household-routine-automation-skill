---
name: kid-face-sort
description: Sort a folder of family photos by child using local face recognition (InsightFace ArcFace). Use when the user asks to find/sort/group photos of their child (or kids) by face, build a per-child album, or tune face-match thresholds. Fully offline after first model download.
---

# kid-face-sort

## When to use
- "우리 아이 사진만 모아줘", "아이별로 사진 분류", "단체사진에서 우리 애 찾아줘"
- Enrolling new reference photos as a child grows; tuning the threshold.

## Install (once, macOS)
```bash
cd <path>/kid-face-sort && bash install.sh   # needs python3 + Xcode CLT
```

## Commands (run via ./kidface.sh)
| Command | Purpose |
|---|---|
| `enroll <name> <photos-or-dir...> [--largest] [--replace]` | Store reference embeddings (1 face per photo; `--largest` for multi-face) |
| `sort <input_dir> -o <out_dir> [-t 0.55] [--margin 0.10] [--mode symlink\|copy\|dry] [--keep-others]` | Recursively scan, match every face, place into `out/<name>/`, `_unsure/`, write `report.csv` |
| `sort ... [--rescan] [--no-cache] [-v] [--write-meta [sidecar\|inplace]] [--finder-tag]` | Cache-aware: unchanged files skipped; DB/threshold change → re-score from cached embeddings (no detection) |
| `cache stats\|clear\|export [out.csv]` | Inspect / wipe / export scan cache (`~/.kidface/scan_cache.sqlite`, env `KIDFACE_CACHE`) |
| `tune <name> <positives_dir> [negatives_dir]` | Print scores and recommend threshold |
| `refresh <name> <dir\|report.csv\|cache> [--min-score 0.65] [--dup-cos 0.95] [--cap 20] [--apply]` | Growth-aware auto-enrollment from high-confidence matches. Dry-run by default; `--apply` backs up DB to `~/.kidface/backups/` first |
| `rollback <name\|all>` | Restore latest backup |
| `list`, `forget <name>`, `migrate` | Manage children (list shows per-quarter bucket / origin counts); migrate v1 DB |
Global: `--db PATH` (default `~/.kidface/embeddings.npz`, or env `KIDFACE_DB`), `--min-face 40`.
Env: `KIDFACE_CPU_ONLY=1` to disable CoreML.

## Workflow
1. Ask the user for 3-10 solo, frontal, recent photos per child → `enroll`.
2. `sort --mode dry` first and show the summary; then real run (`symlink` default, doesn't duplicate photos).
3. Have the user review `_unsure/`; if errors, run `tune` and adjust `-t`.

## Growth-aware matching
Refs carry metadata (sha1, capture date from EXIF or mtime, 3-month bucket, score, added_at, origin manual|auto).
Score = max over refs of cos × max(0.85, 1 − 0.02 × bucket distance); distance is to the photo's own bucket if dated, else to the newest ref bucket.

## Monthly refresh & drift-safety (MUST)
- Always show `refresh` dry-run to the user before the first `--apply`; never lower `--min-score` below 0.65 without user consent.
- Never add from `_unsure`; candidates must also score ≥ min-score against manual refs only; photos with 2+ matching faces are skipped; dedupe sha1 and cos>0.95; cap 20/bucket; manual refs are never pruned.
- If sort results look wrong after a refresh, run `rollback <name>` immediately.
- Scheduling: `schedule/monthly_refresh.sh` + `schedule/com.kidface.refresh.plist` (launchd, `~/Library/LaunchAgents`, `launchctl load`) or cron `0 10 1 * *`. Edit YOURNAME/name/photo paths first.

## Scan cache & metadata
- Re-runs are cheap: always prefer cached runs; use `--rescan` only if the user suspects bad detections or model changed.
- `refresh <name> cache` reads candidates from the cache (no folder rescan).
- Default never modifies originals. `--write-meta` writes `.xmp` sidecars. Use `--write-meta inplace` (exiftool) or `--finder-tag` ONLY when the user explicitly asks; warn that in-place writes change file bytes and may trigger iCloud re-sync. Never touch files inside the Photos library package.

## Privacy rules (MUST)
- NEVER upload, send, or paste child photos or embeddings to any web service, API, LLM vision endpoint, or chat. All processing stays on this Mac.
- The scan cache contains face embeddings (biometric): keep it local, never upload/sync it.
- Keep the embeddings DB local (chmod 600); never commit it to git or sync it to cloud folders.
- Do not move or delete the user's originals; prefer `symlink` or `copy`.
- Delete any temporary copies you make after testing.
- Pretrained InsightFace models are non-commercial: do not use this for a paid service without a commercial license.

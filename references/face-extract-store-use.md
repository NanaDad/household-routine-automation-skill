# Face feature extract, store, and use

This document describes the **local-only** pipeline used by the household face sorter. It is a procedure guide, not a dump of any household's embeddings, photos, or identity labels.

## Pipeline overview

1. **Detect** faces in an image (SCRFD detector from InsightFace `buffalo_l`).
2. **Align/crop** the face region for recognition input.
3. **Embed** each face into a **512-dimensional L2-normalized vector** (ResNet50@WebFace600K recognition ONNX).
4. **Compare** candidate embeddings to stored identity references with cosine similarity, optional age-bucket weighting, and optional same-face negative/lookalike veto.
5. **Decide** folder/label using locked thresholds; keep unsure items for human review.
6. **Store** only numeric embeddings + metadata locally — never store source photos inside the embedding database.

Photos are not uploaded. Network is used only for the first model download unless the operator chooses otherwise.

## Commands (generic local adapter)

Assume a local CLI wrapper around InsightFace (example name: `kidface`):

| Step | Command pattern | What it does |
|---|---|---|
| Enroll references | `kidface enroll <label> <photos-or-dir...> [--largest] [--replace]` | Detect one face per reference photo (or largest with `--largest`), embed, append to local DB under `<label>` |
| Sort / match | `kidface sort <input_dir> -o <out_dir> [-t 0.55] [--margin 0.10] [--mode symlink\|copy\|dry]` | Detect every face, score vs all labels, place into `out/<label>/`, `_unsure/`, write `report.csv` |
| Tune threshold | `kidface tune <label> <positives_dir> [negatives_dir]` | Print score ranges; recommend threshold if positives/negatives separate cleanly |
| List / forget | `kidface list` / `kidface forget <label>` | Inspect reference counts; remove a label |
| Refresh growth | `kidface refresh <label> <dir\|report.csv\|cache> [--min-score 0.65] [--apply]` | Propose high-confidence auto-refs; apply only after review/backup |
| Rollback | `kidface rollback <label\|all>` | Restore latest embedding DB backup |
| Cache ops | `kidface cache stats\|clear\|export` | Inspect/clear local scan cache |

Default decision bands (operator-locked):

- confirmed: score ≥ **0.55** (and negative veto passes)
- needs-confirm / `_unsure`: **0.45–0.55**
- ignore: **< 0.45**
- sort flags: always `-t 0.55 --margin 0.10` unless the owner explicitly retunes after a documented evaluation

## What “feature extraction” means here

- Not hand-crafted facial landmarks as the match key.
- Primary match key = **deep embedding vector** (512-D, unit-norm).
- Detection may use landmarks internally for alignment; the **stored reusable feature** is the embedding.
- Score between two faces ≈ **cosine similarity** of their embeddings (with optional time-bucket weight).

## How features are stored (local)

### Identity reference DB

- Typical path pattern (runtime only): `~/.kidface/embeddings.npz` (mode `600`)
- Contents per identity label:
  - `float32` matrix of shape `(N, 512)` — one row per reference face
  - parallel metadata list: content hash, capture date, quarter bucket, enroll score (if auto), added_at, origin (`manual`|`auto`), source filename (basename only in ops; do not commit paths)
- Photos themselves are **not** copied into the DB.
- Before apply of bulk changes: copy DB into a local backups folder; support rollback.

### Scan cache (speed)

- Typical path pattern: `~/.kidface/scan_cache.sqlite` (mode `600`)
- Per image: content hash, size/mtime, face bboxes, detection scores, **cached embeddings**, last scores/decision, model id, reference-DB hash, threshold used, scanned_at
- Re-runs skip unchanged files; if only the reference DB/threshold changed, **re-score from cached embeddings** without re-detecting
- Cache holds biometric embeddings → keep local, never cloud-sync or commit

### Optional sidecars

- Prefer not modifying originals.
- Optional XMP sidecar or Finder tags may record labels; inplace EXIF writes change file bytes and should be opt-in only.

## How stored features are used

### Matching a new photo

1. Load image → detect faces → embed each face.
2. For each identity label, score = max over references of `cos(candidate, ref) * time_weight`.
3. Time weight uses quarter buckets so recent appearance can rank higher without discarding older refs.
4. If a `__negative__` (lookalike) set exists, compare **the same face** to negative refs; reject when negative score ≥ positive score.
5. Apply thresholds → confirmed / unsure / ignore.
6. Multi-face group photos: accept if any face clears confirmed band for a label (after veto).

### Building / maintaining the reference set

1. Start with 3–10 clear solo frontal photos → `enroll` as `manual`.
2. After owner-confirmed archives accumulate, optionally `refresh --apply` with min-score 0.65, manual-baseline gate, single-face only, dedupe sha1 and cos>0.95, cap per quarter.
3. Owner-marked false positives → enroll into `__negative__` to reduce repeat mistakes.
4. If reference pairwise cos ≈ 1.0 for distinct rows, **dedupe exact duplicate embeddings** before trusting rankings.
5. Never auto-enroll from `_unsure` alone.

### Integration with school-album workflow

1. Download album attachments locally.
2. `sort --mode dry` with locked thresholds.
3. Split outputs: confirmed vs needs-confirm vs ignore.
4. Send confirmed only after policy allows; send needs-confirm to owner review channel; ignore the rest.
5. On owner pass/exclude, update archive state and optionally enroll negatives.
6. Keep embeddings/cache/photos out of git and out of shared skill repos.

## Privacy and licensing hard rules

- Do not commit embeddings, caches, photos, child names, or absolute archive paths.
- Do not upload family faces to cloud vision APIs for this workflow.
- Pretrained `buffalo_l` weights are non-commercial research licensed upstream; private family use is the intended scope of this skill documentation.
- Treat embeddings as biometric data: local disk, restricted permissions, no sync folders.

## Operator checklist before claiming “face system is ready”

- [ ] `buffalo_l` detection + recognition ONNX files present locally
- [ ] At least one identity label enrolled with multiple manual refs
- [ ] `list` shows expected counts; no mass exact-duplicate refs
- [ ] Dry-run sort on a known positive set and a known negative set
- [ ] Thresholds locked at 0.55 / 0.10 unless retuned with evidence
- [ ] Backup path verified before any `--apply` refresh

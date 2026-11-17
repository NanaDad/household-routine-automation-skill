# Face model provenance and growth refresh

## Model and upstream source

- Upstream library/repository: [InsightFace](https://github.com/deepinsight/insightface), Python package `insightface`, model pack `buffalo_l`.
- The official [model-zoo table](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md) identifies `buffalo_l` as SCRFD-10GF detection plus ResNet50@WebFace600K recognition, with optional alignment/gender modules. The locally installed bundle commonly contains `det_10g.onnx` and `w600k_r50.onnx`; the local sorter loads detection and recognition and produces 512-dimensional normalized embeddings.
- Do not describe this installation as RetinaFace + ArcFace R100 unless that exact bundle is verified on disk.
- The local kid-face-sort adapter is a local adapter around InsightFace, not a claim of a separate public product remote.
- InsightFace library code is MIT licensed, but pretrained model weights are licensed for non-commercial research use only per upstream model-zoo documentation. Keep use private/non-commercial unless a suitable commercial model license is obtained.

## Locked score bands (operator-confirmed)

- Sort defaults: `-t 0.55 --margin 0.10`
- Confirmed candidate: score ≥ 0.55 and same-face negative/lookalike veto passes when negatives exist
- Needs-confirm (`_unsure`): about 0.45–0.55 only
- Ignore: score < 0.45 — not a review candidate
- Never lower the review floor (for example to 0.32) to “find more” candidates

## Growth-aware reference updates

The identity reference set is updated from recent, approved photos so a growing child's appearance can be represented across time. Each reference records capture date and is grouped into three-month buckets. Matching uses the time-nearest reference bucket where capture date is known, with a gradual age-distance weight; older references remain usable rather than abruptly expiring.

Observed refresh safeguards:

- Only high-confidence candidates are considered (minimum score 0.65 for auto-refresh), and the candidate must also score against the manual reference set.
- Skip uncertain-folder images, multi-face/ambiguous photos, low scores, duplicate files, and near-duplicate embeddings (cosine similarity above 0.95).
- Keep a bounded number of references per quarter bucket (cap 20); never remove manual references. Back up before apply and support rollback.
- Before trusting scores, detect and drop exact-duplicate reference embeddings (pairwise cos ≈ 1.0), which can distort ranking.
- Refresh is not an unconditional full re-extraction of every archived photo. Unchanged images reuse local cached face embeddings; force full rescan only when deliberately requested.
- Candidate embeddings are not proof of identity. Use explicit human review/approval before an image is sent, archived as the child, or enrolled as a trusted reference.
- Owner-marked non-matches may be enrolled as `__negative__` lookalike veto references; compare **the same detected face** against positive and negative scores.

## Runtime verification notes

- Verify model filenames and architecture against the installed artifact directory before documenting claims.
- Distinguish: installed LaunchAgent/cron vs sample schedule file; cached embedding reuse vs full re-extract; configured quarterly job vs proven completed runs.
- Keep embeddings DB, scan cache, and source photos local with restricted permissions. Never commit them.

## Privacy

Never place reference photos, embeddings, scan caches, child names, archive paths, or per-run logs in this repository. Store protected paths and identity labels only in local runtime configuration.

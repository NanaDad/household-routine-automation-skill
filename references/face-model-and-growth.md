# Face model provenance and growth refresh

## Model and upstream source

- Upstream library/repository: [InsightFace](https://github.com/deepinsight/insightface), Python package insightface, model pack buffalo_l.
- The official [model-zoo table](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md) identifies buffalo_l as SCRFD-10GF detection plus ResNet50@WebFace600K recognition, with 2D106/3D68 alignment and gender/age modules. The locally installed bundle contains det_10g.onnx and w600k_r50.onnx; the local sorter loads detection and recognition only and produces 512-dimensional normalized embeddings.
- Do not describe this installation as RetinaFace + ArcFace R100: that statement in the local sorter README was inaccurate for the installed buffalo_l bundle and has been corrected to match the official model-zoo entry and installed model filenames.
- The local kid-face-sort adapter has no separate public Git remote configured, so its own code provenance cannot be attributed to another public repository. Record it as a local adapter around InsightFace, not as code copied from an unverified repository.
- InsightFace library code is MIT licensed, but the pretrained model weights are licensed for non-commercial research use only according to the upstream model-zoo documentation. Keep use private/non-commercial unless a suitable commercial model license is obtained.

## Growth-aware reference updates

The identity reference set is updated from recent, approved photos so a growing child's appearance can be represented across time. Each reference records capture date and is grouped into three-month buckets. Matching uses the time-nearest reference bucket where capture date is known, with a gradual age-distance weight; older references remain usable rather than abruptly expiring.

The observed refresh safeguards are:

- Only high-confidence candidates are considered (minimum score 0.65), and the candidate must also score against the manual reference set.
- Skip uncertain-folder images, multi-face/ambiguous photos, low scores, duplicate files, and near-duplicate embeddings (cosine similarity above 0.95).
- Keep a bounded number of references per quarter bucket (cap 20); never remove manual references. Back up before apply and support rollback.
- Refresh is not an unconditional full re-extraction of every archived photo. Unchanged images reuse local cached face embeddings; new or changed images are detected and embedded. Force a full feature re-extraction only when deliberately requested (for example, a model change or explicit rescan). Keep caches local and access-restricted.
- Candidate embeddings are still not proof of identity. Use explicit human review/approval before an image is sent, archived as the child, or enrolled as a trusted reference.

## Schedule status observed during audit

An enabled OpenClaw quarterly refresh job is configured to refresh from recent local archive photos with the safeguards above. Its run history had no completed run at audit time, so configuration is present but periodic execution is not yet proven. The example macOS monthly LaunchAgent described in the local tool README is not installed on this host; do not claim monthly refresh is active.

## Privacy

Never place reference photos, embeddings, scan caches, child names, archive paths, or per-run logs in this repository. Store actual protected paths and identity labels only in local runtime configuration.

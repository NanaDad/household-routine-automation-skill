# Tools

## kid-face-sort
Local-only child photo face classifier (InsightFace `buffalo_l`).

- Detect faces → 512-D embeddings → store in local `~/.kidface/` (not in git)
- CLI: enroll / sort / tune / refresh / rollback / cache
- No photos, embeddings, or household identity are committed here

### Quick start (makes face extract/use actually work)
```bash
cd tools/kid-face-sort
bash install.sh   # venv + deps + buffalo_l model download + empty DB
./kidface.sh enroll <label> /path/to/reference-photos/
./kidface.sh sort /path/to/album -o /tmp/out --mode dry -t 0.55 --margin 0.10
```

`install.sh` downloads public model weights to `~/.insightface/models/` and seeds an empty DB at `~/.kidface/embeddings.npz`. No household face data is in git.

See `tools/kid-face-sort/QUICKSTART.md`, `tools/kid-face-sort/README.md`, and `references/face-extract-store-use.md`.

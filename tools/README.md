# Tools

## kid-face-sort
Local-only child photo face classifier (InsightFace `buffalo_l`).

- Detect faces → 512-D embeddings → store in local `~/.kidface/` (not in git)
- CLI: enroll / sort / tune / refresh / rollback / cache
- No photos, embeddings, or household identity are committed here

### Quick start
```bash
cd tools/kid-face-sort
bash install.sh
./kidface.sh enroll <label> /path/to/reference-photos/
./kidface.sh sort /path/to/album -o /path/to/out --mode dry -t 0.55 --margin 0.10
```

See `tools/kid-face-sort/README.md` and `references/face-extract-store-use.md`.

# Empty face DB template

`embeddings.empty.npz` is an **empty** identity database for first-run setup.

- Contains no person labels, no face embeddings, no photos
- Schema matches `kidface` local DB (`__meta__` JSON + optional `<label>__emb` arrays)
- Copy to a **local untracked** path such as `~/.kidface/embeddings.npz` before enroll

```bash
mkdir -p ~/.kidface
cp templates/embeddings.empty.npz ~/.kidface/embeddings.npz
chmod 600 ~/.kidface/embeddings.npz
./kidface.sh enroll <label> /path/to/reference-photos/
```

Do not commit populated DBs (any `*__emb` arrays with real faces).

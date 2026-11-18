# kid-face-sort quick start (usable after install)

## One-time install
```bash
cd tools/kid-face-sort
bash install.sh
```
This will:
1. Create a local Python venv and install dependencies
2. Download public **buffalo_l** face models into `~/.insightface/models/` (~280MB, once)
3. Create an **empty** embeddings DB at `~/.kidface/embeddings.npz` if missing
4. Leave all personal photos/embeddings off git

## Use
```bash
# enroll reference faces (solo clear photos)
./kidface.sh enroll child_a ~/Pictures/refs_child_a/

# dry-run classify an album folder
./kidface.sh sort ~/Pictures/album -o /tmp/sorted --mode dry -t 0.55 --margin 0.10

# inspect identities
./kidface.sh list

# optional: lookalike negatives after human reject
./kidface.sh enroll __negative__ ~/Pictures/not_child_a/ --largest
```

## Score bands (recommended)
- confirmed ≥ **0.55**
- needs-confirm **0.45–0.55** (`_unsure`)
- ignore **< 0.45**

## Privacy
- Populated embeddings DB and scan cache stay under `~/.kidface/` (local only)
- Never commit real `embeddings.npz`, photos, or `.onnx` weights to git
- Model weights are public pretrained files (non-commercial research license upstream)

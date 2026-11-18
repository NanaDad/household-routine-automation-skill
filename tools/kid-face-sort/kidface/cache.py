"""로컬 스캔 캐시 (~/.kidface/scan_cache.sqlite). 사진 원본은 저장하지 않고 얼굴 임베딩/점수만 저장."""
import hashlib, json, os, sqlite3, time
from pathlib import Path
import numpy as np

DEFAULT_CACHE = Path(os.environ.get("KIDFACE_CACHE", Path.home() / ".kidface" / "scan_cache.sqlite"))
SCHEMA = """
CREATE TABLE IF NOT EXISTS paths(path TEXT PRIMARY KEY, sha1 TEXT, size INT, mtime REAL);
CREATE TABLE IF NOT EXISTS files(sha1 TEXT PRIMARY KEY, model TEXT, n_faces INT, photo_date TEXT, scanned_at TEXT);
CREATE TABLE IF NOT EXISTS faces(sha1 TEXT, idx INT, bbox TEXT, det REAL, emb BLOB, PRIMARY KEY(sha1, idx));
CREATE TABLE IF NOT EXISTS results(sha1 TEXT PRIMARY KEY, db_hash TEXT, threshold REAL, margin REAL,
  scores TEXT, best TEXT, decision TEXT, scored_at TEXT);
"""

def now(): return time.strftime("%Y-%m-%dT%H:%M:%S")

def model_id():
    try:
        import insightface; v = insightface.__version__
    except Exception: v = "?"
    return f"{os.environ.get('KIDFACE_MODEL', 'buffalo_l')}@insightface-{v}"

def db_hash(db):
    p = Path(db)
    return hashlib.sha1(p.read_bytes()).hexdigest()[:16] if p.exists() else "none"

class Cache:
    def __init__(self, path=DEFAULT_CACHE):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        self.c = sqlite3.connect(self.path); self.c.executescript(SCHEMA)
        if new: os.chmod(self.path, 0o600)
        self.model = model_id()

    def sha_for(self, p, sha_fn, rescan=False):
        st = p.stat(); key = str(p.resolve())
        if not rescan:
            r = self.c.execute("SELECT sha1,size,mtime FROM paths WHERE path=?", (key,)).fetchone()
            if r and r[1] == st.st_size and abs(r[2] - st.st_mtime) < 1e-3: return r[0]
        h = sha_fn(p)
        self.c.execute("REPLACE INTO paths VALUES(?,?,?,?)", (key, h, st.st_size, st.st_mtime)); return h

    def get_faces(self, sha):
        r = self.c.execute("SELECT model,photo_date FROM files WHERE sha1=?", (sha,)).fetchone()
        if not r or r[0] != self.model: return None
        fs = [(np.frombuffer(e, dtype=np.float32).copy(), d, json.loads(b)) for b, d, e in
              self.c.execute("SELECT bbox,det,emb FROM faces WHERE sha1=? ORDER BY idx", (sha,))]
        return fs, r[1]

    def put_faces(self, sha, faces, pdate):
        self.c.execute("DELETE FROM faces WHERE sha1=?", (sha,))
        self.c.executemany("INSERT INTO faces VALUES(?,?,?,?,?)",
            [(sha, i, json.dumps(bb), ds, e.astype(np.float32).tobytes()) for i, (e, ds, bb) in enumerate(faces)])
        self.c.execute("REPLACE INTO files VALUES(?,?,?,?,?)", (sha, self.model, len(faces), pdate, now()))
        self.c.execute("DELETE FROM results WHERE sha1=?", (sha,))

    def get_result(self, sha, dbh, t, m):
        r = self.c.execute("SELECT scores,best,decision FROM results WHERE sha1=? AND db_hash=? AND threshold=? AND margin=?",
                           (sha, dbh, t, m)).fetchone()
        return (json.loads(r[0]), json.loads(r[1]), json.loads(r[2])) if r else None

    def put_result(self, sha, dbh, t, m, scores, best, decision):
        self.c.execute("REPLACE INTO results VALUES(?,?,?,?,?,?,?,?)",
                       (sha, dbh, t, m, json.dumps(scores), json.dumps(best), json.dumps(decision, ensure_ascii=False), now()))

    def iter_cached(self):
        """(path, sha1, photo_date, faces, decision) — 현존하는 파일만."""
        for path, sha in self.c.execute("SELECT path,sha1 FROM paths").fetchall():
            if not Path(path).exists(): continue
            g = self.get_faces(sha)
            if not g: continue
            r = self.c.execute("SELECT decision FROM results WHERE sha1=?", (sha,)).fetchone()
            yield Path(path), sha, g[1], g[0], (json.loads(r[0]) if r else [])

    def stats(self):
        q = lambda s: self.c.execute(s).fetchone()[0]
        return {"paths": q("SELECT count(*) FROM paths"), "files": q("SELECT count(*) FROM files"),
                "faces": q("SELECT count(*) FROM faces"), "results": q("SELECT count(*) FROM results"),
                "size_kb": round(self.path.stat().st_size / 1024, 1), "path": str(self.path)}

    def clear(self):
        for t in ("paths", "files", "faces", "results"): self.c.execute(f"DELETE FROM {t}")
        self.commit(); self.c.execute("VACUUM")

    def export_rows(self):
        return self.c.execute("""SELECT p.path, p.sha1, f.photo_date, f.n_faces, r.best, r.decision, r.db_hash, r.threshold, r.scored_at, f.model
            FROM paths p LEFT JOIN files f ON f.sha1=p.sha1 LEFT JOIN results r ON r.sha1=p.sha1 ORDER BY p.path""").fetchall()

    def alias(self, old, p, sha_fn):
        """원본에 메타를 써서 해시가 바뀐 경우, 기존 검출/점수를 새 해시로 복사(재검출 방지)."""
        new = self.sha_for(Path(p), sha_fn, rescan=True)
        if new == old: return
        for t, cols in (("files", "*"), ("results", "*")):
            r = self.c.execute(f"SELECT * FROM {t} WHERE sha1=?", (old,)).fetchone()
            if r: self.c.execute(f"REPLACE INTO {t} VALUES({','.join('?'*len(r))})", (new, *r[1:]))
        self.c.execute("INSERT OR REPLACE INTO faces SELECT ?,idx,bbox,det,emb FROM faces WHERE sha1=?", (new, old))

    def commit(self): self.c.commit()
